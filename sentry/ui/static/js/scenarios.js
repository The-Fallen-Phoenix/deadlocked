/**
 * Attack Scenario Studio & Test Bench for SENTRY
 */

const Scenarios = {
  activeScenarioId: null,

  async loadScenarios(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    try {
      const res = await fetch('/api/scenarios');
      const scenarios = await res.json();

      container.innerHTML = scenarios.map(sc => `
        <div class="scenario-card" onclick="Scenarios.selectScenario('${sc.id}')" id="card-${sc.id}">
          <div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
              <span class="badge ${sc.is_synthetic_ground_truth ? 'badge-critical' : 'badge-low'}">
                ${sc.is_synthetic_ground_truth ? 'AI Attack Vector' : 'Genuine Baseline'}
              </span>
              <span style="font-size:0.75rem; color:var(--text-muted);">${sc.category}</span>
            </div>
            <h3>${sc.title}</h3>
            <p>${sc.description}</p>
          </div>
          <div style="border-top:1px solid rgba(255,255,255,0.05); padding-top:0.6rem; margin-top:0.4rem; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <span style="font-size:0.7rem; color:var(--text-muted); display:block;">Amount / Exposure</span>
              <strong style="color:var(--accent-cyan); font-size:0.9rem;">₹${sc.transaction_amount_inr.toLocaleString()}</strong>
            </div>
            <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); Scenarios.runScenario('${sc.id}')">
              Execute Attack Test
            </button>
          </div>
        </div>
      `).join('');

      // Auto-select first scenario
      if (scenarios.length > 0) {
        this.selectScenario(scenarios[0].id);
      }
    } catch (e) {
      console.error('Failed to load scenarios:', e);
    }
  },

  selectScenario(scenarioId) {
    this.activeScenarioId = scenarioId;
    document.querySelectorAll('.scenario-card').forEach(c => c.classList.remove('active'));
    const card = document.getElementById(`card-${scenarioId}`);
    if (card) card.classList.add('active');
  },

  async runScenario(scenarioId) {
    this.selectScenario(scenarioId);
    const resultBox = document.getElementById('scenario-result-view');
    if (!resultBox) return;

    resultBox.innerHTML = `
      <div style="text-align:center; padding:3rem 1rem;">
        <div class="pulse-dot" style="margin:0 auto 1rem; width:16px; height:16px;"></div>
        <p style="color:var(--text-secondary);">Streaming audio through SENTRY 4-Layer Neural Pipeline...</p>
      </div>
    `;

    try {
      const resp = await fetch(`/api/scenarios/run/${scenarioId}`, { method: 'POST' });
      if (!resp.ok) throw new Error('Scenario execution failed');
      const data = await resp.json();

      this.renderScenarioResult(resultBox, data);
    } catch (e) {
      resultBox.innerHTML = `<div class="prevention-banner CRITICAL"><p>Error executing scenario: ${e.message}</p></div>`;
    }
  },

  renderScenarioResult(container, data) {
    const sc = data.scenario_meta;
    const auth = data.authenticity;
    const spk = data.speaker_verification;
    const threat = data.threat_intelligence;
    const risk = data.risk_evaluation;
    const fin = data.financial_exposure;
    const prev = data.prevention_action;

    let bannerHtml = '';
    if (prev.notification_banner) {
      bannerHtml = `
        <div class="prevention-banner ${prev.notification_banner.severity}">
          <svg style="width:24px; height:24px; flex-shrink:0;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
          </svg>
          <div>
            <strong>${prev.notification_banner.title}</strong>
            <p style="font-size:0.85rem; margin-top:0.2rem;">${prev.notification_banner.message}</p>
          </div>
        </div>
      `;
    }

    container.innerHTML = `
      ${bannerHtml}
      
      <div style="background:rgba(0,0,0,0.3); border-radius:8px; padding:0.85rem 1rem; margin-bottom:1.25rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
        <div>
          <span style="font-size:0.75rem; color:var(--text-muted);">Audio File</span>
          <p style="font-size:0.85rem; font-weight:600; color:#e2e8f0;">${sc.audio_filename} (${data.audio_duration_sec}s)</p>
        </div>
        <audio controls src="/api/audio/sample/${sc.audio_filename}" style="height:34px;"></audio>
      </div>

      <!-- 4 Intelligence Layer Breakdown Cards -->
      <div class="grid-2" style="margin-bottom:1.25rem;">
        
        <!-- Layer 1: Voice Authenticity -->
        <div class="glass-card">
          <div class="card-header">
            <div class="card-title">
              <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z"/></svg>
              Layer 1: Voice Authenticity
            </div>
            <span class="badge ${auth.synthetic_probability > 0.7 ? 'badge-critical' : 'badge-low'}">${auth.classification}</span>
          </div>
          <div class="metric-row">
            <div class="metric-header">
              <span>Synthetic Clone Probability</span>
              <strong>${(auth.synthetic_probability * 100).toFixed(1)}%</strong>
            </div>
            <div class="progress-track">
              <div class="progress-fill" style="width:${auth.synthetic_probability * 100}%; background:${auth.synthetic_probability > 0.7 ? '#ef4444' : '#10b981'};"></div>
            </div>
          </div>
          <div style="font-size:0.78rem; color:var(--text-muted); display:grid; grid-template-columns:1fr 1fr; gap:0.4rem; margin-top:0.6rem;">
            <div>HF Cutoff: <strong style="color:#e2e8f0;">${auth.vocoder_metrics.hf_attenuation_ratio || 'N/A'}</strong></div>
            <div>Pitch Jitter: <strong style="color:#e2e8f0;">${auth.vocoder_metrics.pitch_jitter || 'N/A'}</strong></div>
            <div>Spectral Flux: <strong style="color:#e2e8f0;">${auth.vocoder_metrics.spectral_flux || 'N/A'}</strong></div>
            <div>Vocoder Score: <strong style="color:#e2e8f0;">${auth.vocoder_metrics.vocoder_artifact_score || 'N/A'}</strong></div>
          </div>
        </div>

        <!-- Layer 2: Speaker Biometric Verification -->
        <div class="glass-card">
          <div class="card-header">
            <div class="card-title">
              <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
              Layer 2: Speaker Identity
            </div>
            <span class="badge ${spk.is_match ? 'badge-low' : (spk.verification_status === 'UNENROLLED' ? 'badge-moderate' : 'badge-critical')}">
              ${spk.verification_status}
            </span>
          </div>
          <div class="metric-row">
            <div class="metric-header">
              <span>Biometric Similarity (Cosine)</span>
              <strong>${spk.match_confidence_pct}%</strong>
            </div>
            <div class="progress-track">
              <div class="progress-fill" style="width:${spk.match_confidence_pct}%; background:${spk.is_match ? '#10b981' : '#ef4444'};"></div>
            </div>
          </div>
          <p style="font-size:0.8rem; color:var(--text-secondary); margin-top:0.4rem;">
            Claimed Identity: <strong>${spk.claimed_speaker}</strong>
          </p>
          <p style="font-size:0.75rem; color:var(--text-muted); margin-top:0.2rem;">
            ${spk.description}
          </p>
        </div>

      </div>

      <div class="grid-2">

        <!-- Layer 3: NLP Threat & Coercion -->
        <div class="glass-card">
          <div class="card-header">
            <div class="card-title">
              <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
              Layer 3: Threat & Urgency NLP
            </div>
            <span class="badge ${threat.is_coercive_threat ? 'badge-critical' : 'badge-low'}">
              ${threat.text_analysis.threat_level}
            </span>
          </div>
          <div class="metric-row">
            <div class="metric-header">
              <span>Behavioral Coercion Score</span>
              <strong>${(threat.behavioral_threat_score * 100).toFixed(0)}%</strong>
            </div>
            <div class="progress-track">
              <div class="progress-fill" style="width:${threat.behavioral_threat_score * 100}%; background:${threat.behavioral_threat_score > 0.5 ? '#ef4444' : '#10b981'};"></div>
            </div>
          </div>
          <div style="background:rgba(0,0,0,0.3); border-radius:6px; padding:0.5rem 0.75rem; margin-top:0.5rem; font-size:0.78rem; font-style:italic; color:var(--text-secondary);">
            "${sc.transcript}"
          </div>
          ${threat.text_analysis.detected_phrases.length > 0 ? `
            <div style="margin-top:0.5rem; display:flex; gap:0.35rem; flex-wrap:wrap;">
              ${threat.text_analysis.detected_phrases.map(p => `<span class="badge badge-critical" style="font-size:0.7rem;">Trigger: "${p}"</span>`).join('')}
            </div>
          ` : ''}
        </div>

        <!-- Layer 4: Financial Risk & Prevention Action -->
        <div class="glass-card" style="border-color:${risk.tier_color};">
          <div class="card-header">
            <div class="card-title">
              <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              Layer 4: Fraud Risk & Decision
            </div>
            <span class="badge" style="background:${risk.tier_color}33; color:${risk.tier_color}; border:1px solid ${risk.tier_color};">
              ${risk.risk_tier} RISK (${risk.overall_risk_score}/100)
            </span>
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.6rem; margin-bottom:0.75rem;">
            <div style="background:rgba(0,0,0,0.3); padding:0.5rem; border-radius:6px;">
              <span style="font-size:0.7rem; color:var(--text-muted); display:block;">Target Exposure</span>
              <strong style="color:var(--text-primary); font-size:1.05rem;">${fin.formatted_amount}</strong>
            </div>
            <div style="background:rgba(0,0,0,0.3); padding:0.5rem; border-radius:6px;">
              <span style="font-size:0.7rem; color:var(--text-muted); display:block;">Estimated Avoided Loss</span>
              <strong style="color:var(--accent-emerald); font-size:1.05rem;">${fin.formatted_avoided_exposure}</strong>
            </div>
          </div>
          <div style="background:rgba(6,182,212,0.08); border-left:3px solid ${risk.tier_color}; padding:0.5rem 0.75rem; border-radius:4px; font-size:0.8rem;">
            <strong>Action Executed:</strong> ${prev.prevention_action}
            <p style="font-size:0.75rem; color:var(--text-secondary); margin-top:0.2rem;">${risk.recommendation}</p>
          </div>
        </div>

      </div>
    `;
  }
};

window.Scenarios = Scenarios;
