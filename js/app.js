/**
 * Master Application Controller for SENTRY Cyber-Defense Platform
 */

document.addEventListener('DOMContentLoaded', () => {
  App.init();
});

const App = {
  streamer: null,
  isRecording: false,

  init() {
    this.setupTabs();
    this.setupLiveMic();
    this.setupFileUpload();
    this.setupROISimulator();
    this.loadStats();
    this.loadSpeakers();
    this.loadHeldTransactions();
    this.loadAuditLogs();

    // Initialize scenarios in tab 2
    if (window.Scenarios) {
      Scenarios.loadScenarios('scenarios-container');
    }

    // Refresh periodic stats every 10s
    setInterval(() => {
      this.loadStats();
    }, 10000);
  },

  setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetId = btn.getAttribute('data-tab');
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        const panel = document.getElementById(targetId);
        if (panel) panel.classList.add('active');

        // Trigger tab-specific refresh
        if (targetId === 'tab-vault') App.loadSpeakers();
        if (targetId === 'tab-benchmarks') App.loadBenchmarks();
        if (targetId === 'tab-incidents') {
          App.loadHeldTransactions();
          App.loadAuditLogs();
        }
      });
    });
  },

  async loadStats() {
    try {
      const resp = await fetch('/api/stats');
      if (!resp.ok) return;
      const stats = await resp.json();

      document.getElementById('kpi-threats').textContent = stats.total_threats_analyzed.toLocaleString();
      document.getElementById('kpi-high-risk').textContent = stats.high_risk_sessions.toLocaleString();
      document.getElementById('kpi-critical').textContent = stats.critical_incidents.toLocaleString();
      document.getElementById('kpi-exposure').textContent = stats.total_exposure_inr >= 100000 
        ? `₹${(stats.total_exposure_inr / 100000).toFixed(1)}L` 
        : `₹${stats.total_exposure_inr.toLocaleString()}`;
      document.getElementById('kpi-avoided').textContent = stats.total_avoided_inr >= 100000 
        ? `₹${(stats.total_avoided_inr / 100000).toFixed(1)}L` 
        : `₹${stats.total_avoided_inr.toLocaleString()}`;
    } catch (e) {
      console.warn('Failed to refresh stats:', e);
    }
  },

  setupLiveMic() {
    const startBtn = document.getElementById('btn-start-mic');
    const stopBtn = document.getElementById('btn-stop-mic');
    const canvas = document.getElementById('mic-visualizer');
    const claimedSelect = document.getElementById('live-claimed-speaker');
    const amountInput = document.getElementById('live-tx-amount');

    this.streamer = new SentryAudioStreamer({
      chunkIntervalMs: 800,
      onAnalysisResult: (data) => {
        this.renderLiveStreamResult(data);
      },
      onError: (err) => {
        alert('Microphone Access Error: ' + err.message);
        this.setStreamingUI(false);
      }
    });

    startBtn.addEventListener('click', async () => {
      const claimedSpk = claimedSelect ? claimedSelect.value : null;
      const txAmount = amountInput ? amountInput.value : 0;

      const started = await this.streamer.startStream(claimedSpk, txAmount);
      if (started) {
        this.isRecording = true;
        this.setStreamingUI(true);
        this.streamer.drawWaveform(canvas);
      }
    });

    stopBtn.addEventListener('click', () => {
      this.streamer.stopStream();
      this.isRecording = false;
      this.setStreamingUI(false);
    });
  },

  setStreamingUI(isStreaming) {
    const startBtn = document.getElementById('btn-start-mic');
    const stopBtn = document.getElementById('btn-stop-mic');
    const pulse = document.getElementById('mic-status-pulse');
    const label = document.getElementById('mic-status-label');

    if (isStreaming) {
      startBtn.style.display = 'none';
      stopBtn.style.display = 'inline-flex';
      pulse.style.backgroundColor = '#ef4444';
      pulse.style.boxShadow = '0 0 12px #ef4444';
      label.textContent = 'STREAMING LIVE (Sliding Window 2.0s)';
      label.style.color = '#ef4444';
    } else {
      startBtn.style.display = 'inline-flex';
      stopBtn.style.display = 'none';
      pulse.style.backgroundColor = '#10b981';
      pulse.style.boxShadow = '0 0 8px #10b981';
      label.textContent = 'STANDBY / READY';
      label.style.color = '#94a3b8';
    }
  },

  renderLiveStreamResult(data) {
    const auth = data.authenticity;
    const spk = data.speaker_verification;
    const risk = data.risk_evaluation;
    const fin = data.financial_exposure;
    const prev = data.prevention_action;

    // Update circular gauge
    const circle = document.getElementById('live-gauge-circle');
    const text = document.getElementById('live-gauge-score');
    const tier = document.getElementById('live-gauge-tier');
    if (circle && text && tier) {
      Charts.updateRiskGauge(circle, text, risk.overall_risk_score, risk.risk_tier);
      tier.textContent = `${risk.risk_tier} RISK`;
      tier.style.color = risk.tier_color;
    }

    // Update Layer bars
    document.getElementById('live-synth-prob').textContent = `${(auth.synthetic_probability * 100).toFixed(1)}%`;
    document.getElementById('live-synth-bar').style.width = `${auth.synthetic_probability * 100}%`;
    document.getElementById('live-synth-bar').style.backgroundColor = auth.synthetic_probability > 0.7 ? '#ef4444' : '#10b981';

    document.getElementById('live-spk-match').textContent = `${spk.match_confidence_pct}%`;
    document.getElementById('live-spk-bar').style.width = `${spk.match_confidence_pct}%`;
    document.getElementById('live-spk-bar').style.backgroundColor = spk.is_match ? '#10b981' : '#ef4444';

    document.getElementById('live-exposure-val').textContent = fin.formatted_amount;
    document.getElementById('live-avoided-val').textContent = fin.formatted_avoided_exposure;
    document.getElementById('live-action-text').textContent = prev.prevention_action;

    // Banner alert if critical
    const alertBox = document.getElementById('live-alert-banner');
    if (alertBox) {
      if (prev.notification_banner) {
        alertBox.style.display = 'flex';
        alertBox.className = `prevention-banner ${prev.notification_banner.severity}`;
        alertBox.innerHTML = `<strong>${prev.notification_banner.title}:</strong> ${prev.notification_banner.message}`;
      } else {
        alertBox.style.display = 'none';
      }
    }
  },

  setupFileUpload() {
    const uploadForm = document.getElementById('audio-upload-form');
    const fileInput = document.getElementById('upload-audio-file');
    const claimedSelect = document.getElementById('upload-claimed-speaker');
    const amountInput = document.getElementById('upload-tx-amount');
    const transcriptInput = document.getElementById('upload-transcript');
    const resultContainer = document.getElementById('upload-result-container');

    if (!uploadForm) return;

    uploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!fileInput.files || fileInput.files.length === 0) {
        alert('Please select an audio file (WAV/MP3) to analyze.');
        return;
      }

      resultContainer.innerHTML = `
        <div style="text-align:center; padding:2rem 1rem;">
          <div class="pulse-dot" style="margin:0 auto 1rem; width:16px; height:16px;"></div>
          <p style="color:var(--text-secondary);">Extracting acoustic features and running neural models...</p>
        </div>
      `;

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      if (claimedSelect && claimedSelect.value) formData.append('claimed_speaker_id', claimedSelect.value);
      if (amountInput && amountInput.value) formData.append('transaction_amount_inr', amountInput.value);
      if (transcriptInput && transcriptInput.value) formData.append('transcript', transcriptInput.value);

      try {
        const resp = await fetch('/api/analyze/file', {
          method: 'POST',
          body: formData
        });

        if (!resp.ok) throw new Error('File analysis failed');
        const data = await resp.json();

        // Render result inside Forensics view
        this.renderForensicsResult(resultContainer, data);
      } catch (err) {
        resultContainer.innerHTML = `<div class="prevention-banner CRITICAL"><p>Error: ${err.message}</p></div>`;
      }
    });
  },

  renderForensicsResult(container, data) {
    const auth = data.authenticity;
    const spk = data.speaker_verification;
    const risk = data.risk_evaluation;
    const fin = data.financial_exposure;
    const prev = data.prevention_action;

    container.innerHTML = `
      <div class="glass-card" style="border-color:${risk.tier_color}; margin-top:1.5rem;">
        <div class="card-header">
          <div class="card-title">
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
            Comprehensive Forensics Dossier (${data.session_id})
          </div>
          <span class="badge" style="background:${risk.tier_color}33; color:${risk.tier_color}; border:1px solid ${risk.tier_color};">
            ${risk.risk_tier} RISK (${risk.overall_risk_score}/100)
          </span>
        </div>

        <div class="grid-3" style="margin-bottom:1rem;">
          <div style="background:rgba(0,0,0,0.3); padding:0.75rem; border-radius:6px;">
            <span style="font-size:0.75rem; color:var(--text-muted);">Acoustic Synthetic Probability</span>
            <strong style="color:${auth.synthetic_probability > 0.7 ? '#ef4444' : '#10b981'}; font-size:1.2rem; display:block;">
              ${(auth.synthetic_probability * 100).toFixed(1)}%
            </strong>
            <span style="font-size:0.7rem; color:var(--text-muted);">${auth.classification}</span>
          </div>
          <div style="background:rgba(0,0,0,0.3); padding:0.75rem; border-radius:6px;">
            <span style="font-size:0.75rem; color:var(--text-muted);">Speaker Match Confidence</span>
            <strong style="color:${spk.is_match ? '#10b981' : '#ef4444'}; font-size:1.2rem; display:block;">
              ${spk.match_confidence_pct}%
            </strong>
            <span style="font-size:0.7rem; color:var(--text-muted);">${spk.verification_status}</span>
          </div>
          <div style="background:rgba(0,0,0,0.3); padding:0.75rem; border-radius:6px;">
            <span style="font-size:0.75rem; color:var(--text-muted);">Financial Exposure Avoided</span>
            <strong style="color:var(--accent-emerald); font-size:1.2rem; display:block;">
              ${fin.formatted_avoided_exposure}
            </strong>
            <span style="font-size:0.7rem; color:var(--text-muted);">Target: ${fin.formatted_amount}</span>
          </div>
        </div>

        <!-- Temporal Anomaly Timeline Canvas -->
        <div style="margin-bottom:1.25rem;">
          <div style="display:flex; justify-content:space-between; font-size:0.78rem; margin-bottom:0.4rem; color:var(--text-muted);">
            <span>Temporal Anomaly Timeline (Sliding 1.0s Windows)</span>
            <span style="color:#ef4444;">-- 70% Anomaly Threshold</span>
          </div>
          <div class="visualizer-box" style="height:90px;">
            <canvas id="timeline-canvas" class="visualizer-canvas"></canvas>
          </div>
        </div>

        <!-- Physical Vocoder Metrics Table -->
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap:0.6rem; background:rgba(0,0,0,0.25); padding:0.75rem; border-radius:6px; font-size:0.75rem;">
          <div>High-Freq Attenuation: <strong>${auth.vocoder_metrics.hf_attenuation_ratio || 'N/A'}</strong></div>
          <div>Pitch Jitter Perturbation: <strong>${auth.vocoder_metrics.pitch_jitter || 'N/A'}</strong></div>
          <div>Amplitude Shimmer: <strong>${auth.vocoder_metrics.amplitude_shimmer || 'N/A'}</strong></div>
          <div>Spectral Centroid: <strong>${auth.vocoder_metrics.spectral_centroid_hz || 'N/A'} Hz</strong></div>
          <div>Spectral Flux: <strong>${auth.vocoder_metrics.spectral_flux || 'N/A'}</strong></div>
          <div>Inference Latency: <strong>${data.latency_ms} ms</strong></div>
        </div>

        <!-- Cryptographic Hash Verification -->
        ${data.incident_dossier ? `
          <div style="margin-top:1rem; padding-top:0.75rem; border-top:1px solid rgba(255,255,255,0.06); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem; font-size:0.75rem;">
            <div>
              <span style="color:var(--text-muted);">Cryptographic Incident Hash:</span>
              <code style="color:var(--accent-cyan); margin-left:0.5rem;">${data.incident_dossier.cryptographic_hash.substring(0, 32)}...</code>
            </div>
            <button class="btn btn-sm" onclick="App.exportIncidentJson('${data.incident_dossier.incident_id}')">
              Export Forensics JSON
            </button>
          </div>
        ` : ''}
      </div>
    `;

    // Draw timeline canvas
    setTimeout(() => {
      const canvas = document.getElementById('timeline-canvas');
      if (canvas && auth.temporal_slices) {
        Charts.drawTemporalTimeline(canvas, auth.temporal_slices);
      }
    }, 50);
  },

  async loadSpeakers() {
    const tableBody = document.getElementById('speakers-table-body');
    const selectLive = document.getElementById('live-claimed-speaker');
    const selectUpload = document.getElementById('upload-claimed-speaker');

    try {
      const resp = await fetch('/api/speakers');
      if (!resp.ok) return;
      const speakers = await resp.json();

      if (tableBody) {
        tableBody.innerHTML = speakers.map(spk => `
          <tr>
            <td><strong>${spk.display_name}</strong></td>
            <td>${spk.role}</td>
            <td><code style="color:var(--accent-cyan); font-size:0.75rem;">${spk.biometric_hash.substring(0, 16)}...</code></td>
            <td><span class="badge badge-low">ENROLLED</span></td>
            <td>${spk.formatted_enrolled_at || 'Verified'}</td>
            <td>
              <button class="btn btn-sm btn-danger" onclick="App.deleteSpeaker('${spk.speaker_id}')">Delete</button>
            </td>
          </tr>
        `).join('');
      }

      // Populate dropdowns
      const optionsHtml = '<option value="">-- No Enrolled Claim (Anonymous) --</option>' +
        speakers.map(s => `<option value="${s.speaker_id}">${s.display_name} (${s.role})</option>`).join('');

      if (selectLive) selectLive.innerHTML = optionsHtml;
      if (selectUpload) selectUpload.innerHTML = optionsHtml;
    } catch (e) {
      console.warn('Failed to load speakers:', e);
    }
  },

  async deleteSpeaker(speakerId) {
    if (!confirm(`Are you sure you want to remove voice biometric profile "${speakerId}"?`)) return;
    try {
      const resp = await fetch(`/api/speakers/${speakerId}`, { method: 'DELETE' });
      if (resp.ok) {
        this.loadSpeakers();
      }
    } catch (e) {
      alert('Error deleting speaker: ' + e.message);
    }
  },

  setupROISimulator() {
    const sliderCalls = document.getElementById('roi-annual-calls');
    const sliderTicket = document.getElementById('roi-avg-ticket');
    const sliderFraudRate = document.getElementById('roi-fraud-rate');
    const sliderEfficacy = document.getElementById('roi-efficacy');
    const sliderCost = document.getElementById('roi-cost');

    const updateCalc = async () => {
      if (!sliderCalls) return;

      const calls = parseInt(sliderCalls.value);
      const ticket = parseFloat(sliderTicket.value);
      const fraudRate = parseFloat(sliderFraudRate.value);
      const efficacy = parseFloat(sliderEfficacy.value);
      const cost = parseFloat(sliderCost.value);

      // Update label displays
      document.getElementById('val-annual-calls').textContent = `${(calls / 1000000).toFixed(1)} Million`;
      document.getElementById('val-avg-ticket').textContent = `₹${ticket.toLocaleString()}`;
      document.getElementById('val-fraud-rate').textContent = `${fraudRate.toFixed(2)}%`;
      document.getElementById('val-efficacy').textContent = `${efficacy.toFixed(0)}%`;
      document.getElementById('val-cost').textContent = `₹${(cost / 100000).toFixed(0)} Lakhs`;

      try {
        const resp = await fetch('/api/simulation/roi', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            annual_interactions: calls,
            avg_transaction_value_inr: ticket,
            estimated_fraud_rate_pct: fraudRate,
            detection_improvement_pct: efficacy,
            annual_platform_cost_inr: cost
          })
        });

        if (resp.ok) {
          const res = await resp.json();
          const m = res.metrics;

          document.getElementById('res-exposure-before').textContent = m.formatted_exposure_before;
          document.getElementById('res-residual-exposure').textContent = m.formatted_residual_exposure;
          document.getElementById('res-avoided-loss').textContent = m.formatted_exposure_avoided;
          document.getElementById('res-net-savings').textContent = m.formatted_net_savings;
          document.getElementById('res-roi-mult').textContent = m.roi_label;
          document.getElementById('res-breakeven').textContent = `${m.break_even_months} Months`;
        }
      } catch (e) {
        console.warn('ROI calc error:', e);
      }
    };

    [sliderCalls, sliderTicket, sliderFraudRate, sliderEfficacy, sliderCost].forEach(el => {
      if (el) el.addEventListener('input', updateCalc);
    });

    // Initial run
    updateCalc();
  },

  async loadHeldTransactions() {
    const container = document.getElementById('held-transactions-body');
    if (!container) return;

    try {
      const resp = await fetch('/api/prevention/held-transactions');
      if (!resp.ok) return;
      const list = await resp.json();

      if (list.length === 0) {
        container.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:1.5rem;">No active transactions currently frozen. All queues normal.</td></tr>`;
        return;
      }

      container.innerHTML = list.map(item => `
        <tr>
          <td><strong style="color:#ef4444;">${item.hold_id}</strong></td>
          <td>${item.caller_id}</td>
          <td><strong style="color:var(--accent-cyan);">₹${item.amount_inr.toLocaleString()}</strong></td>
          <td><span class="badge badge-critical">${item.status}</span></td>
          <td style="font-size:0.75rem;">${item.reason}</td>
          <td>
            ${item.status === 'HELD_PENDING_FORENSIC_REVIEW' ? `
              <button class="btn btn-sm btn-success" onclick="App.releaseTransactionHold('${item.hold_id}')">
                Approve & Release
              </button>
            ` : `<span style="font-size:0.75rem; color:var(--accent-emerald);">Cleared</span>`}
          </td>
        </tr>
      `).join('');
    } catch (e) {
      console.warn('Failed to load held transactions:', e);
    }
  },

  async releaseTransactionHold(holdId) {
    const officerId = prompt('Enter SOC Officer Authorization ID:', 'SOC_LEAD_RITHWIK');
    if (!officerId) return;

    try {
      const resp = await fetch(`/api/prevention/held-transactions/${holdId}/release`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ officer_id: officerId })
      });

      if (resp.ok) {
        alert(`Transaction ${holdId} successfully released and cleared for processing.`);
        this.loadHeldTransactions();
        this.loadAuditLogs();
      }
    } catch (e) {
      alert('Failed to release hold: ' + e.message);
    }
  },

  async loadAuditLogs() {
    const container = document.getElementById('soc-audit-stream');
    if (!container) return;

    try {
      const resp = await fetch('/api/audit-logs');
      if (!resp.ok) return;
      const logs = await resp.json();

      container.innerHTML = logs.map(ev => `
        <div style="border-bottom:1px solid rgba(255,255,255,0.04); padding:0.5rem 0; font-size:0.78rem; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <span style="color:var(--text-muted); margin-right:0.6rem;">${ev.formatted_time.split(' ')[1]}</span>
            <strong style="color:#e2e8f0; margin-right:0.5rem;">[${ev.event_type}]</strong>
            <span style="color:var(--text-secondary);">${ev.caller_id} — Action: ${ev.action_taken}</span>
          </div>
          <span class="badge ${ev.risk_level === 'CRITICAL' ? 'badge-critical' : (ev.risk_level === 'HIGH' ? 'badge-high' : 'badge-low')}">
            ${ev.risk_level} (${ev.risk_score})
          </span>
        </div>
      `).join('');
    } catch (e) {
      console.warn('Failed to load audit logs:', e);
    }
  },

  async loadBenchmarks() {
    try {
      const resp = await fetch('/api/benchmarks');
      if (!resp.ok) return;
      const data = await resp.json();

      const dsBody = document.getElementById('benchmark-datasets-body');
      if (dsBody) {
        dsBody.innerHTML = data.datasets.map(d => `
          <tr>
            <td><strong>${d.name}</strong></td>
            <td>${d.samples_count}</td>
            <td><strong style="color:var(--accent-emerald);">${d.sentry_eer_pct}%</strong></td>
            <td><span style="color:#ef4444;">${d.baseline_eer_pct}%</span></td>
            <td><strong style="color:var(--accent-cyan);">${d.sentry_auc}</strong></td>
          </tr>
        `).join('');
      }

      const modelBody = document.getElementById('model-comparison-body');
      if (modelBody) {
        modelBody.innerHTML = data.model_comparison.map(m => `
          <tr>
            <td><strong>${m.model}</strong><br><small style="color:var(--text-muted);">${m.approach}</small></td>
            <td><strong style="color:var(--accent-emerald);">${m.eer_asv21}</strong></td>
            <td><strong style="color:var(--accent-cyan);">${m.latency_ms}</strong></td>
            <td>${m.params}</td>
          </tr>
        `).join('');
      }

      // Load Foundation models
      const fmResp = await fetch('/api/foundation-models');
      if (fmResp.ok) {
        const models = await fmResp.json();
        const fmList = document.getElementById('foundation-models-list');
        if (fmList) {
          fmList.innerHTML = models.map(fm => `
            <div style="background:rgba(0,0,0,0.3); padding:0.65rem 0.85rem; border-radius:6px; border:1px solid rgba(255,255,255,0.05); display:flex; justify-content:space-between; align-items:center;">
              <div>
                <strong style="color:#e2e8f0; font-size:0.85rem;">${fm.repo_id}</strong>
                <p style="font-size:0.72rem; color:var(--text-muted); margin-top:0.1rem;">${fm.description}</p>
              </div>
              <span class="badge ${fm.is_cached ? 'badge-low' : 'badge-moderate'}" style="font-size:0.7rem;">
                ${fm.type} (${fm.dimension}d)
              </span>
            </div>
          `).join('');
        }
      }
    } catch (e) {
      console.warn('Failed to load benchmarks:', e);
    }
  },

  async testMultilingualPhrase() {
    const input = document.getElementById('ml-test-input');
    const resultBox = document.getElementById('ml-test-result');
    if (!input || !resultBox) return;

    resultBox.innerHTML = `<p style="font-size:0.8rem; color:var(--text-muted);">Parsing phonetic and linguistic threat indicators...</p>`;

    try {
      const resp = await fetch('/api/test/multilingual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: input.value })
      });

      if (!resp.ok) throw new Error('Multilingual test failed');
      const data = await resp.json();

      resultBox.innerHTML = `
        <div style="background:rgba(0,0,0,0.35); border:1px solid rgba(6,182,212,0.3); border-radius:6px; padding:0.85rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
            <span style="font-size:0.75rem; color:var(--text-muted);">Detected Language: <strong style="color:#e2e8f0;">${data.detected_language}</strong></span>
            <span class="badge ${data.linguistic_score > 0.6 ? 'badge-critical' : 'badge-low'}">${data.threat_level} (${(data.linguistic_score * 100).toFixed(0)}%)</span>
          </div>
          ${data.detected_phrases.length > 0 ? `
            <div style="display:flex; gap:0.35rem; flex-wrap:wrap; margin-top:0.4rem;">
              ${data.detected_phrases.map(p => `<span class="badge badge-critical" style="font-size:0.7rem;">Matched: "${p}"</span>`).join('')}
            </div>
          ` : `<span style="font-size:0.75rem; color:var(--accent-emerald);">No coercive social engineering triggers detected. Clean phrase.</span>`}
        </div>
      `;
    } catch (e) {
      resultBox.innerHTML = `<p style="font-size:0.8rem; color:#ef4444;">Error: ${e.message}</p>`;
    }
  },

  async exportIncidentJson(incidentId) {
    try {
      const resp = await fetch(`/api/incidents/${incidentId}`);
      if (!resp.ok) throw new Error('Failed to fetch incident');
      const data = await resp.json();

      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `SENTRY_Forensics_${incidentId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert('Export failed: ' + e.message);
    }
  }
};

window.App = App;
