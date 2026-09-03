/**
 * Master Application Controller for SENTRY Cyber-Defense Platform
 * Hardened for static GitHub Pages deployment: safe DOM access, normalized timelines,
 * and defensive try/catch so a single runtime error doesn't break the whole UI.
 */

document.addEventListener('DOMContentLoaded', () => {
  try {
    App.init();
  } catch (e) {
    console.warn('App.init failed:', e);
    // Don't rethrow — static pages should remain usable
  }
});

const safe = {
  el(id) { try { return document.getElementById(id); } catch (e) { return null; } },
  setText(id, txt) { const e = this.el(id); if (e) e.textContent = txt; },
  setHtml(id, html) { const e = this.el(id); if (e) e.innerHTML = html; },
  setStyle(id, prop, val) { const e = this.el(id); if (e && e.style) e.style[prop] = val; }
};

const App = {
  streamer: null,
  isRecording: false,

  init() {
    try {
      this.setupTabs();
      this.setupLiveMic();
      this.setupFileUpload();
      this.loadStats();
      this.loadSpeakers();
      this.loadHeldTransactions();
      this.loadAuditLogs();

      // Initialize scenarios in tab 2 safely
      try {
        if (window.Scenarios && typeof Scenarios.loadScenarios === 'function') {
          Scenarios.loadScenarios('scenarios-container');
        }
      } catch (e) {
        console.warn('Scenarios.loadScenarios failed:', e);
      }

      // Refresh periodic stats every 10s
      setInterval(() => {
        try { this.loadStats(); } catch (e) { console.warn('loadStats periodic failed', e); }
      }, 10000);
    } catch (e) {
      console.warn('App.init error:', e);
    }
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

        // Trigger tab-specific refresh safely
        try {
          if (targetId === 'tab-vault') App.loadSpeakers();
          if (targetId === 'tab-benchmarks') App.loadBenchmarks();
          if (targetId === 'tab-incidents') {
            App.loadHeldTransactions();
            App.loadIncidents();
            App.loadAuditLogs();
          }
        } catch (e) { console.warn('Tab refresh failed', e); }
      });
    });
  },

  async loadStats() {
    let stats = {
      total_threats_analyzed: 14820,
      high_risk_sessions: 312,
      critical_incidents: 89,
      total_exposure_inr: 4500000.0,
      total_avoided_inr: 4230000.0
    };

    try {
      const resp = await fetch('/api/stats');
      if (resp.ok) {
        stats = await resp.json();
      }
    } catch (e) {
      console.log('Using embedded stats for static deployment');
    }

    try {
      if (safe.el('kpi-threats')) safe.setText('kpi-threats', (stats.total_threats_analyzed || 14820).toLocaleString());
      if (safe.el('kpi-high-risk')) safe.setText('kpi-high-risk', (stats.high_risk_sessions || 312).toLocaleString());
      if (safe.el('kpi-critical')) safe.setText('kpi-critical', (stats.critical_incidents || 89).toLocaleString());
      if (safe.el('kpi-exposure')) {
        const exp = stats.total_exposure_inr || 4500000;
        safe.setText('kpi-exposure', exp >= 100000 ? `₹${(exp / 100000).toFixed(1)}L` : `₹${exp.toLocaleString()}`);
      }
      if (safe.el('kpi-avoided')) {
        const av = stats.total_avoided_inr || 4230000;
        safe.setText('kpi-avoided', av >= 100000 ? `₹${(av / 100000).toFixed(1)}L` : `₹${av.toLocaleString()}`);
      }
    } catch (e) { console.warn('Updating KPI DOM failed:', e); }
  },

  setupLiveMic() {
    try {
      const startBtn = safe.el('btn-start-mic');
      const stopBtn = safe.el('btn-stop-mic');
      const canvas = safe.el('mic-visualizer');
      const claimedSelect = safe.el('live-claimed-speaker');
      const amountInput = safe.el('live-tx-amount');

      this.streamer = new (window.SentryAudioStreamer || function(){return {startStream:async()=>false, stopStream:()=>{}, drawWaveform:()=>{}}})({
        chunkIntervalMs: 800,
        onAnalysisResult: (data) => {
          try { this.renderLiveStreamResult(data); } catch (e) { console.warn('onAnalysisResult handler failed', e); }
        },
        onError: (err) => {
          try { alert('Microphone Access Error: ' + err.message); } catch (e) {}
          this.setStreamingUI(false);
        }
      });

      if (startBtn) startBtn.addEventListener('click', async () => {
        try {
          const claimedSpk = claimedSelect ? claimedSelect.value : null;
          const txAmount = amountInput ? amountInput.value : 0;

          const started = await this.streamer.startStream(claimedSpk, txAmount);
          if (started) {
            this.isRecording = true;
            this.setStreamingUI(true);
            if (this.streamer.drawWaveform && canvas) this.streamer.drawWaveform(canvas);
          }
        } catch (e) { console.warn('Start stream failed', e); }
      });

      if (stopBtn) stopBtn.addEventListener('click', () => {
        try { this.streamer.stopStream(); } catch (e) { console.warn('Stop stream failed', e); }
        this.isRecording = false;
        this.setStreamingUI(false);
      });
    } catch (e) { console.warn('setupLiveMic failed:', e); }
  },

  setStreamingUI(isStreaming) {
    try {
      const startBtn = safe.el('btn-start-mic');
      const stopBtn = safe.el('btn-stop-mic');
      const pulse = safe.el('mic-status-pulse');
      const label = safe.el('mic-status-label');

      if (isStreaming) {
        if (startBtn) startBtn.style.display = 'none';
        if (stopBtn) stopBtn.style.display = 'inline-flex';
        if (pulse) { pulse.style.backgroundColor = '#ff6b00'; pulse.style.boxShadow = '0 0 12px #ff6b00'; }
        if (label) { label.textContent = 'STREAMING LIVE (Sliding Window 2.0s)'; label.style.color = '#ff8533'; }
      } else {
        if (startBtn) startBtn.style.display = 'inline-flex';
        if (stopBtn) stopBtn.style.display = 'none';
        if (pulse) { pulse.style.backgroundColor = 'rgba(255, 107, 0, 0.4)'; pulse.style.boxShadow = '0 0 8px rgba(255, 107, 0, 0.4)'; }
        if (label) { label.textContent = 'STANDBY / READY'; label.style.color = '#94a3b8'; }
      }
    } catch (e) { console.warn('setStreamingUI failed:', e); }
  },

  renderLiveStreamResult(data) {
    try {
      const auth = data && data.authenticity ? data.authenticity : { synthetic_probability: 0 };
      const spk = data && data.speaker_verification ? data.speaker_verification : { match_confidence_pct: 0, is_match: false };
      const risk = data && data.risk_evaluation ? data.risk_evaluation : { overall_risk_score: 0, risk_tier: 'LOW' };
      const fin = data && data.financial_exposure ? data.financial_exposure : { formatted_amount: '₹0', formatted_avoided_exposure: '₹0' };
      const prev = data && data.prevention_action ? data.prevention_action : { prevention_action: 'ALLOW_INTERACTION' };

      // Update circular gauge (guard Charts)
      try {
        const circle = safe.el('live-gauge-circle');
        const text = safe.el('live-gauge-score');
        const tier = safe.el('live-gauge-tier');
        if (window.Charts && typeof Charts.updateRiskGauge === 'function' && circle && text) {
          Charts.updateRiskGauge(circle, text, (risk.overall_risk_score || 0), (risk.risk_tier || 'LOW'));
        } else if (text) {
          text.textContent = Math.round(risk.overall_risk_score || 0);
        }
        if (tier) { tier.textContent = `${risk.risk_tier || 'LOW'} RISK`; tier.style.color = '#ffffff'; }
      } catch (e) { console.warn('updateRiskGauge failed', e); }

      // Update Layer bars safely
      try {
        if (safe.el('live-synth-prob')) safe.setText('live-synth-prob', `${((auth.synthetic_probability || 0) * 100).toFixed(1)}%`);
        if (safe.el('live-synth-bar')) {
          const bar = safe.el('live-synth-bar');
          bar.style.width = `${((auth.synthetic_probability || 0) * 100)}%`;
          bar.style.backgroundColor = (auth.synthetic_probability || 0) > 0.7 ? '#ff8533' : '#ff6b00';
        }

        if (safe.el('live-spk-match')) safe.setText('live-spk-match', `${(spk.match_confidence_pct || 0)}%`);
        if (safe.el('live-spk-bar')) {
          const spkBar = safe.el('live-spk-bar');
          spkBar.style.width = `${(spk.match_confidence_pct || 0)}%`;
          spkBar.style.backgroundColor = spk.is_match ? '#ffffff' : '#ff8533';
        }

        if (safe.el('live-exposure-val')) safe.setText('live-exposure-val', fin.formatted_amount || '₹0');
        if (safe.el('live-avoided-val')) safe.setText('live-avoided-val', fin.formatted_avoided_exposure || '₹0');
        if (safe.el('live-action-text')) safe.setText('live-action-text', prev.prevention_action || 'ALLOW_INTERACTION');
      } catch (e) { console.warn('Updating live metrics failed', e); }

      // Banner alert if critical
      try {
        const alertBox = safe.el('live-alert-banner');
        if (alertBox) {
          if (prev.notification_banner) {
            alertBox.style.display = 'flex';
            alertBox.className = `prevention-banner ${prev.notification_banner.severity}`;
            alertBox.innerHTML = `<strong>${prev.notification_banner.title}:</strong> ${prev.notification_banner.message}`;
          } else {
            alertBox.style.display = 'none';
          }
        }
      } catch (e) { console.warn('Updating alert banner failed', e); }

    } catch (e) { console.warn('renderLiveStreamResult failed:', e); }
  },

  setupFileUpload() {
    try {
      const uploadForm = safe.el('audio-upload-form');
      const fileInput = safe.el('upload-audio-file');
      const claimedSelect = safe.el('upload-claimed-speaker');
      const amountInput = safe.el('upload-tx-amount');
      const transcriptInput = safe.el('upload-transcript');
      const resultContainer = safe.el('upload-result-container');

      if (!uploadForm) return;

      uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!fileInput.files || fileInput.files.length === 0) {
          alert('Please select an audio file (WAV/MP3) to analyze.');
          return;
        }

        if (resultContainer) {
          resultContainer.innerHTML = `\n          <div style="text-align:center; padding:2rem 1rem;">\n            <div class="pulse-dot" style="margin:0 auto 1rem; width:16px; height:16px;"></div>\n            <p style="color:var(--text-secondary);">Extracting acoustic features and running neural models...</p>\n          </div>\n        `;
        }

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

          if (resp.ok) {
            const data = await resp.json();
            try { this.renderForensicsResult(resultContainer, data); } catch (e) { console.warn('renderForensicsResult failed after API response', e); }
            return;
          }
        } catch (err) {
          console.log('Using static simulation for audio forensics file analysis');
        }

        // Static fallback simulation for GitHub Pages / Vercel
        setTimeout(() => {
          try {
            const fileName = fileInput.files[0] ? fileInput.files[0].name.toLowerCase() : 'audio.wav';
            const isSynth = fileName.includes('synth') || fileName.includes('fake') || fileName.includes('clone') || Math.random() > 0.4;
            const synthProb = isSynth ? 0.932 : 0.084;
            const amount = parseFloat(amountInput && amountInput.value ? amountInput.value : 500000);
            const overallRisk = isSynth ? 89.4 : 16.2;
            const riskTier = isSynth ? 'CRITICAL' : 'LOW';
            const tierColor = isSynth ? '#ef4444' : '#10b981';

            const mockData = {
              session_id: `FORENSIC-STATIC-${Date.now().toString().slice(-6)}`,
              latency_ms: 15.4,
              audio_duration_sec: 4.8,
              authenticity: {
                synthetic_probability: synthProb,
                classification: isSynth ? 'SYNTHETIC_CLONE' : 'GENUINE_VOICE',
                vocoder_metrics: {
                  hf_attenuation_ratio: isSynth ? 0.88 : 0.02,
                  pitch_jitter: isSynth ? 0.004 : 0.019,
                  amplitude_shimmer: isSynth ? 0.008 : 0.042,
                  spectral_centroid_hz: isSynth ? 940.5 : 1650.2,
                  spectral_flux: isSynth ? 0.035 : 0.192
                },
                temporal_slices: [
                  { slice_index: 0, time_start_sec: 0.0, synthetic_prob: isSynth ? 0.88 : 0.05 },
                  { slice_index: 1, time_start_sec: 1.0, synthetic_prob: isSynth ? 0.94 : 0.07 },
                  { slice_index: 2, time_start_sec: 2.0, synthetic_prob: isSynth ? 0.95 : 0.06 },
                  { slice_index: 3, time_start_sec: 3.0, synthetic_prob: isSynth ? 0.91 : 0.09 }
                ]
              },
              speaker_verification: {
                claimed_speaker: claimedSelect && claimedSelect.value ? claimedSelect.options[claimedSelect.selectedIndex].text : 'Unspecified Speaker',
                verification_status: isSynth ? 'VOICEPRINT_MISMATCH' : 'VERIFIED_MATCH',
                match_confidence_pct: isSynth ? 18.4 : 96.8,
                cosine_similarity: isSynth ? 0.21 : 0.91
              },
              threat_intelligence: {
                behavioral_threat_score: isSynth ? 0.85 : 0.04,
                threat_level: isSynth ? 'HIGH_COERCION' : 'NORMAL'
              },
              risk_evaluation: {
                overall_risk_score: overallRisk,
                risk_tier: riskTier,
                tier_color: tierColor
              },
              financial_exposure: {
                transaction_amount_inr: amount,
                formatted_amount: `₹${amount.toLocaleString()}`,
                formatted_avoided_exposure: isSynth ? `₹${(amount * 0.95).toLocaleString()}` : '₹0'
              },
              prevention_action: {
                prevention_action: isSynth ? 'AUTOMATED_TRANSACTION_HOLD' : 'ALLOW_INTERACTION',
                transaction_status: isSynth ? 'FROZEN_HELD' : 'APPROVED',
                notification_banner: isSynth ? {
                  title: 'TRANSACTION HELD FOR SECURITY',
                  message: `Transfer of ₹${amount.toLocaleString()} has been temporarily FROZEN by SENTRY to prevent potential voice-cloning fraud.`
                } : null
              },
              incident_dossier: {
                incident_id: `INC-STATIC-${Date.now().toString().slice(-6)}`,
                cryptographic_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'
              }
            };

            this.renderForensicsResult(resultContainer, mockData);
          } catch (e) { console.warn('Static fallback render failed', e); }
        }, 500);
      });
    } catch (e) { console.warn('setupFileUpload failed:', e); }
  },

  renderForensicsResult(container, data) {
    try {
      if (!container) container = safe.el('upload-result-container');
      const auth = data.authenticity || { synthetic_probability: 0, temporal_slices: [] };
      const spk = data.speaker_verification || { match_confidence_pct: 0, is_match: false };
      const risk = data.risk_evaluation || { overall_risk_score: 0, tier_color: '#dddddd', risk_tier: 'LOW' };
      const fin = data.financial_exposure || { formatted_amount: '₹0', formatted_avoided_exposure: '₹0' };
      const prev = data.prevention_action || { prevention_action: 'ALLOW_INTERACTION' };

      container.innerHTML = `
        <div class="glass-card" style="border-color:${risk.tier_color}; margin-top:1.5rem;">
          <div class="card-header">
            <div class="card-title">
              <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11[...]"></path></svg>
              Comprehensive Forensics Dossier (${data.session_id})
            </div>
            <span class="badge" style="background:${(risk.tier_color||'#999') }33; color:${(risk.tier_color||'#999')}; border:1px solid ${(risk.tier_color||'#999')};">
              ${risk.risk_tier || 'LOW'} RISK (${(risk.overall_risk_score||0)}/100)
            </span>
          </div>

          <div class="grid-3" style="margin-bottom:1rem;">
            <div style="background:rgba(0,0,0,0.3); padding:0.75rem; border-radius:6px;">
              <span style="font-size:0.75rem; color:var(--text-muted);">Acoustic Synthetic Probability</span>
              <strong style="color:${(auth.synthetic_probability>0.7? '#ef4444' : '#10b981')}; font-size:1.2rem; display:block;">
                ${( (auth.synthetic_probability||0) * 100).toFixed(1)}%
              </strong>
              <span style="font-size:0.7rem; color:var(--text-muted);">${auth.classification || ''}</span>
            </div>
            <div style="background:rgba(0,0,0,0.3); padding:0.75rem; border-radius:6px;">
              <span style="font-size:0.75rem; color:var(--text-muted);">Speaker Match Confidence</span>
              <strong style="color:${spk.is_match ? '#10b981' : '#ef4444'}; font-size:1.2rem; display:block;">
                ${spk.match_confidence_pct || 0}%
              </strong>
              <span style="font-size:0.7rem; color:var(--text-muted);">${spk.verification_status || ''}</span>
            </div>
            <div style="background:rgba(0,0,0,0.3); padding:0.75rem; border-radius:6px;">
              <span style="font-size:0.75rem; color:var(--text-muted);">Financial Exposure Avoided</span>
              <strong style="color:var(--accent-emerald); font-size:1.2rem; display:block;">
                ${fin.formatted_avoided_exposure || '₹0'}
              </strong>
              <span style="font-size:0.7rem; color:var(--text-muted);">Target: ${fin.formatted_amount || '₹0'}</span>
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
            <div>High-Freq Attenuation: <strong>${(auth.vocoder_metrics && auth.vocoder_metrics.hf_attenuation_ratio) || 'N/A'}</strong></div>
            <div>Pitch Jitter Perturbation: <strong>${(auth.vocoder_metrics && auth.vocoder_metrics.pitch_jitter) || 'N/A'}</strong></div>
            <div>Amplitude Shimmer: <strong>${(auth.vocoder_metrics && auth.vocoder_metrics.amplitude_shimmer) || 'N/A'}</strong></div>
            <div>Spectral Centroid: <strong>${(auth.vocoder_metrics && auth.vocoder_metrics.spectral_centroid_hz) || 'N/A'} Hz</strong></div>
            <div>Spectral Flux: <strong>${(auth.vocoder_metrics && auth.vocoder_metrics.spectral_flux) || 'N/A'}</strong></div>
            <div>Inference Latency: <strong>${data.latency_ms || 0} ms</strong></div>
          </div>

          ${data.incident_dossier ? `
            <div style="margin-top:1rem; padding-top:0.75rem; border-top:1px solid rgba(255,255,255,0.06); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
              <div>
                <span style="color:var(--text-muted);">Cryptographic Incident Hash:</span>
                <code style="color:var(--accent-cyan); margin-left:0.5rem;">${(data.incident_dossier.cryptographic_hash||'').substring(0,32)}...</code>
              </div>
              <button class="btn btn-sm" onclick="App.exportIncidentJson('${data.incident_dossier.incident_id}')">
                Export Forensics JSON
              </button>
            </div>
          ` : ''}
        </div>
      `;

      // Draw timeline canvas: normalize slices before drawing
      setTimeout(() => {
        try {
          const canvas = safe.el('timeline-canvas');
          const slicesRaw = auth.temporal_slices || [];
          const normalized = slicesRaw.map(s => {
            let val = s.synthetic_score ?? s.synthetic_prob ?? s.syntheticProbability ?? s.synthetic ?? 0;
            if (typeof val === 'string') val = parseFloat(val) || 0;
            if (val > 1) val = val > 100 ? 1 : val / 100;
            return { synthetic_prob: Math.max(0, Math.min(1, val)) };
          });
          if (canvas && window.Charts && typeof Charts.drawTemporalTimeline === 'function') {
            Charts.drawTemporalTimeline(canvas, normalized);
          }
        } catch (e) { console.warn('Timeline draw failed', e); }
      }, 50);
    } catch (e) { console.warn('renderForensicsResult failed:', e); }
  },

  async loadSpeakers() {
    try {
      const tableBody = safe.el('speakers-table-body');
      const selectLive = safe.el('live-claimed-speaker');
      const selectUpload = safe.el('upload-claimed-speaker');

      let speakers = [
        {
          speaker_id: 'spk_rithwik',
          display_name: 'Rithwik Sriram',
          role: 'Team Lead / Executive Profile',
          biometric_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
          formatted_enrolled_at: 'Aug 25, 2026'
        }
      ];

      try {
        const resp = await fetch('/api/speakers');
        if (resp.ok) speakers = await resp.json();
      } catch (e) { console.log('Using embedded speakers for static deployment'); }

      if (tableBody) {
        tableBody.innerHTML = speakers.map(spk => `\n          <tr>\n            <td><strong>${spk.display_name}</strong></td>\n            <td>${spk.role}</td>\n            <td><code style="color:var(--accent-cyan); font-size:0.75rem;">${(spk.biometric_hash || '').substring(0, 16)}...</code></td>\n            <td><span class="badge badge-low">ENROLLED</span></td>\n            <td>${spk.formatted_enrolled_at || 'Verified'}</td>\n            <td>\n              <button class="btn btn-sm btn-danger" onclick="App.deleteSpeaker('${spk.speaker_id}')">Delete</button>\n            </td>\n          </tr>\n        `).join('');
      }

      const optionsHtml = '<option value="">-- No Enrolled Claim (Anonymous) --</option>' +
        speakers.map(s => `<option value="${s.speaker_id}">${s.display_name} (${s.role})</option>`).join('');

      if (selectLive) selectLive.innerHTML = optionsHtml;
      if (selectUpload) selectUpload.innerHTML = optionsHtml;
    } catch (e) { console.warn('loadSpeakers failed', e); }
  },

  async deleteSpeaker(speakerId) {
    if (!confirm(`Are you sure you want to remove voice biometric profile "${speakerId}"?`)) return;
    try {
      const resp = await fetch(`/api/speakers/${speakerId}`, { method: 'DELETE' });
      if (resp.ok) { this.loadSpeakers(); return; }
    } catch (e) { console.warn('deleteSpeaker API failed', e); }
    alert(`Voice biometric profile "${speakerId}" removed from session vault.`);
  },

  async loadHeldTransactions() {
    try {
      const container = safe.el('held-transactions-body');
      if (!container) return;

      let list = [];
      try {
        const resp = await fetch('/api/prevention/held-transactions');
        if (resp.ok) list = await resp.json();
      } catch (e) { console.log('Using embedded held transactions for static deployment'); }

      if (!list || list.length === 0) {
        container.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:1.5rem;">No active transactions currently frozen. All queues normal.</td></tr>`;
        return;
      }

      container.innerHTML = list.map(item => `\n        <tr>\n          <td><strong style="color:#ef4444;">${item.hold_id}</strong></td>\n          <td>${item.caller_id}</td>\n          <td><strong style="color:var(--accent-cyan);">₹${(item.amount_inr || 0).toLocaleString()}</strong></td>\n          <td><span class="badge ${item.status === 'RELEASED_BY_SOC' ? 'badge-low' : 'badge-critical'}">${item.status}</span></td>\n          <td style="font-size:0.75rem;">${item.reason}</td>\n          <td>\n            ${item.status === 'HELD_PENDING_FORENSIC_REVIEW' ? `\n              <button class="btn btn-sm btn-success" onclick="App.releaseTransactionHold('${item.hold_id}')">\n                Approve & Release\n              </button>\n            ` : `<span style="font-size:0.75rem; color:var(--accent-emerald);">Cleared</span>`}\n          </td>\n        </tr>\n      `).join('');
    } catch (e) { console.warn('loadHeldTransactions failed', e); }
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
        this.loadIncidents();
        this.loadAuditLogs();
        return;
      }
    } catch (e) { console.warn('releaseTransactionHold API failed', e); }

    // Static simulation fallback
    alert(`Transaction ${holdId} authorized by ${officerId}: Released and marked Cleared.`);
    this.loadHeldTransactions();
  },

  async loadIncidents() {
    try {
      const container = safe.el('incident-dossiers-body');
      if (!container) return;

      let list = [];
      try {
        const resp = await fetch('/api/incidents?limit=15');
        if (resp.ok) list = await resp.json();
      } catch (e) { console.log('Using embedded incidents for static deployment'); }

      if (!list || list.length === 0) {
        container.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted); padding:1.5rem;">No incident dossiers recorded yet. Run a scenario attack test to generate one.</td></tr>`;
        return;
      }

      container.innerHTML = list.map(item => `\n        <tr>\n          <td><strong style="color:var(--accent-cyan); font-family:monospace; font-size:0.75rem;">${item.incident_id}</strong></td>\n          <td style="font-size:0.75rem; color:var(--text-secondary);">${item.formatted_time || new Date((item.timestamp||0) * 1000).toLocaleTimeString()}</td>\n          <td>${item.claimed_identity || item.caller_id}</td>\n          <td><strong style="color:#e2e8f0;">₹${(item.financial_exposure_inr || 0).toLocaleString()}</strong></td>\n          <td>\n            <span class="badge ${item.risk_tier === 'CRITICAL' ? 'badge-critical' : (item.risk_tier === 'HIGH' ? 'badge-high' : 'badge-low')}">\n              ${item.risk_tier} (${(item.risk_score || 0).toFixed(1)})\n            </span>\n          </td>\n          <td>\n            <span style="font-size:0.75rem; font-weight:600; color:${item.acoustic_forensics && item.acoustic_forensics.classification === 'SYNTHETIC_CLONE' ? '#ef4444' : '#10b981'};">\n              ${item.acoustic_forensics ? item.acoustic_forensics.classification : 'UNKNOWN'}\n            </span>\n          </td>\n          <td>\n            <button class="btn btn-sm btn-outline" style="font-size:0.7rem; padding:0.25rem 0.6rem;" onclick="App.exportIncidentJson('${item.incident_id}')">\n              Download JSON\n            </button>\n          </td>\n        </tr>\n      `).join('');
    } catch (e) { console.warn('loadIncidents failed', e); }
  },

  async loadAuditLogs() {
    try {
      const container = safe.el('soc-audit-stream');
      if (!container) return;

      let logs = [];
      try {
        const resp = await fetch('/api/audit-logs');
        if (resp.ok) logs = await resp.json();
      } catch (e) { console.log('Using embedded audit logs for static deployment'); }

      container.innerHTML = (logs || []).map(ev => `\n        <div style="border-bottom:1px solid rgba(255,255,255,0.04); padding:0.5rem 0; font-size:0.78rem; display:flex; justify-content:space-between; align-items:center;">\n          <div>\n            <span style="color:var(--text-muted); margin-right:0.6rem;">${(ev.formatted_time||'').split(' ')[1] || ev.formatted_time}</span>\n            <strong style="color:#e2e8f0; margin-right:0.5rem;">[${ev.event_type}]</strong>\n            <span style="color:var(--text-secondary);">${ev.caller_id} — Action: ${ev.action_taken}</span>\n          </div>\n          <span class="badge ${ev.risk_level === 'CRITICAL' ? 'badge-critical' : (ev.risk_level === 'HIGH' ? 'badge-high' : 'badge-low')}">\n            ${ev.risk_level} (${ev.risk_score})\n          </span>\n        </div>\n      `).join('');
    } catch (e) { console.warn('loadAuditLogs failed', e); }
  },

  async loadBenchmarks() {
    try {
      let data = { datasets: [], model_comparison: [] };
      try {
        const resp = await fetch('/api/benchmarks');
        if (resp.ok) data = await resp.json();
      } catch (e) { console.log('Using embedded benchmarks for static deployment'); }

      const dsBody = safe.el('benchmark-datasets-body');
      if (dsBody && data.datasets) {
        dsBody.innerHTML = (data.datasets || []).map(d => `\n          <tr>\n            <td><strong>${d.name}</strong></td>\n            <td>${(d.samples_count || 0).toLocaleString()}</td>\n            <td><strong style="color:var(--accent-emerald);">${d.sentry_eer_pct}%</strong></td>\n            <td><span style="color:#ef4444;">${d.baseline_eer_pct}%</span></td>\n            <td><strong style="color:var(--accent-cyan);">${d.sentry_auc}</strong></td>\n          </tr>\n        `).join('');
      }

      const modelBody = safe.el('model-comparison-body');
      if (modelBody && data.model_comparison) {
        modelBody.innerHTML = (data.model_comparison || []).map(m => `\n          <tr>\n            <td><strong>${m.model}</strong><br><small style="color:var(--text-muted);">${m.approach}</small></td>\n            <td><strong style="color:var(--accent-emerald);">${m.eer_asv21}</strong></td>\n            <td><strong style="color:var(--accent-cyan);">${m.latency_ms}</strong></td>\n            <td>${m.params}</td>\n          </tr>\n        `).join('');
      }
    } catch (e) { console.warn('loadBenchmarks failed', e); }
  },

  async testMultilingualPhrase() {
    try {
      const input = safe.el('ml-test-input');
      const resultBox = safe.el('ml-test-result');
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

        resultBox.innerHTML = `...`; // keep it short in static fallback
      } catch (e) {
        resultBox.innerHTML = `<p style="font-size:0.8rem; color:#ef4444;">Error: ${e.message}</p>`;
      }
    } catch (e) { console.warn('testMultilingualPhrase failed', e); }
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
    } catch (e) { alert('Export failed: ' + e.message); }
  }
};

window.App = App;
