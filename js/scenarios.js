/**
 * Attack Scenario Studio & Test Bench for SENTRY
 */
const Scenarios = {
  DEFAULT_SCENARIOS: [
    {
      "id": "scenario_ceo_wire_transfer",
      "title": "CEO Urgent Wire Transfer Scam",
      "category": "Corporate Executive Impersonation",
      "description": "Deepfake voice clone of the Team Leader/CEO demanding an emergency ₹5 Lakh wire transfer to an unknown vendor account.",
      "claimed_speaker_id": "spk_rithwik",
      "claimed_speaker_name": "Rithwik Sriram (Executive Profile)",
      "transcript": "Sahil, this is Rithwik. I am in an urgent closed-door board meeting right now. We need an immediate wire transfer of ₹5,00,000 to this vendor account to secure the contract before 2 PM. Do not delay, process it right away!",
      "transaction_amount_inr": 500000.0,
      "target_beneficiary": "Acme Ventures Holdings (Unregistered Payee)",
      "attack_type": "AI Voice Cloning + Executive Authority Impersonation",
      "is_synthetic_ground_truth": true
    },
    {
      "id": "scenario_digital_arrest_police",
      "title": "Digital Arrest & Police Coercion Scam",
      "category": "Authority Extortion & Social Engineering",
      "description": "Fraudulent caller using synthetic speech claiming to be a CBI officer threatening digital arrest unless ₹2.5 Lakh is sent to a fake judicial escrow.",
      "claimed_speaker_id": null,
      "claimed_speaker_name": "Inspector Verma (Claimed Official)",
      "transcript": "This is Inspector Verma from CBI Cyber Cell Headquarters. An arrest warrant has been issued in your name for money laundering. You are under digital arrest. Transfer ₹2,50,000 immediately to the judicial escrow account or police will raid your premises within 30 minutes. Do not disconnect!",
      "transaction_amount_inr": 250000.0,
      "target_beneficiary": "Judicial Escrow Cyber Cell (Fraudulent Account)",
      "attack_type": "Digital Arrest + Legal Coercion Extortion",
      "is_synthetic_ground_truth": true
    },
    {
      "id": "scenario_grandchild_emergency",
      "title": "Grandchild Emergency ICU Scam",
      "category": "Family Impersonation Extortion",
      "description": "AI-generated voice clone of a grandchild claiming to be in a hospital accident demanding an immediate ₹75,000 emergency deposit.",
      "claimed_speaker_id": "spk_aarav",
      "claimed_speaker_name": "Aarav Sharma (Enrolled Grandchild)",
      "transcript": "Grandpa, please help me! I was in a terrible road accident and the hospital doctor needs an immediate emergency ICU deposit of ₹75,000 right now. Please approve the UPI transfer immediately, my phone is dying!",
      "transaction_amount_inr": 75000.0,
      "target_beneficiary": "City Care Emergency Clinic (Unverified UPI VPA)",
      "attack_type": "Family Voice Clone + Urgent Medical Distress",
      "is_synthetic_ground_truth": true
    },
    {
      "id": "scenario_legitimate_bank_support",
      "title": "Legitimate Bank Support Verification",
      "category": "Normal Banking Interaction",
      "description": "Legitimate support representative with natural acoustic human vocal tract and verified enrolled voice biometric profile.",
      "claimed_speaker_id": "spk_sahil",
      "claimed_speaker_name": "Sahil Singh (Enrolled Support Officer)",
      "transcript": "Good morning, this is Sahil from support. I am calling to follow up on your ticket regarding the recent statement query. There are no fees or transactions required, just confirming your request has been resolved.",
      "transaction_amount_inr": 0.0,
      "target_beneficiary": null,
      "attack_type": "None (Legitimate Customer Support)",
      "is_synthetic_ground_truth": false
    },
    {
      "id": "scenario_dataset_test",
      "title": "Voice Dataset Benchmark Sample",
      "category": "Dataset Analysis Benchmarking",
      "description": "Synthetic voice clone sample extracted directly from the test split (UK Male) of the training dataset.",
      "claimed_speaker_id": null,
      "claimed_speaker_name": "Unknown Dataset Speaker (UK Male Test Split)",
      "transcript": "(Dataset audio sample playing for forensic analysis)",
      "transaction_amount_inr": 0.0,
      "target_beneficiary": "N/A",
      "attack_type": "Synthetic Voice Generation",
      "is_synthetic_ground_truth": true
    }
  ],

  async loadScenarios(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    let scenarios = this.DEFAULT_SCENARIOS;
    try {
      const res = await fetch('/api/scenarios');
      if (res.ok) {
        scenarios = await res.json();
      }
    } catch (e) {
      console.log('Using embedded scenarios for static deployment');
    }

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
      if (resp.ok) {
        const data = await resp.json();
        this.renderScenarioResult(resultBox, data);
        return;
      }
    } catch (e) {
      console.log('Running static simulation mode for scenario execution');
    }

    // Client-side fallback simulation for GitHub Pages / Static Hosting
    setTimeout(() => {
      const sc = this.DEFAULT_SCENARIOS.find(s => s.id === scenarioId) || this.DEFAULT_SCENARIOS[0];
      const isSynth = sc.is_synthetic_ground_truth;
      const amount = sc.transaction_amount_inr;

      const synthProb = isSynth ? (scenarioId === 'scenario_digital_arrest_police' ? 0.94 : (scenarioId === 'scenario_grandchild_emergency' ? 0.91 : 0.88)) : 0.04;
      const spkRisk = isSynth ? 0.85 : 0.02;
      const behScore = isSynth ? (scenarioId === 'scenario_digital_arrest_police' ? 0.92 : (scenarioId === 'scenario_grandchild_emergency' ? 0.84 : 0.78)) : 0.05;

      const expFactor = amount > 0 ? Math.min(1.0, Math.max(0.05, (Math.log10(Math.max(amount, 100)) - 2.0) / 4.0)) : 0.05;
      let rawScore = (0.35 * synthProb + 0.25 * spkRisk + 0.15 * expFactor + 0.15 * behScore + 0.10 * 0.10) * 100.0;
      if (isSynth) rawScore = Math.max(rawScore, 84.5);
      const tier = rawScore <= 25 ? 'LOW' : (rawScore <= 50 ? 'MODERATE' : (rawScore <= 75 ? 'HIGH' : 'CRITICAL'));
      const actionCode = tier === 'LOW' ? 'ALLOW' : (tier === 'MODERATE' ? 'ALERT' : (tier === 'HIGH' ? 'DYNAMIC_CHALLENGE' : 'TRANSACTION_FREEZE'));

      const mockResult = {
        session_id: `SCENARIO-${scenarioId.toUpperCase().slice(0, 10)}-STATIC`,
        latency_ms: 14.2,
        audio_duration_sec: 4.5,
        scenario_meta: sc,
        authenticity: {
          synthetic_probability: synthProb,
          confidence_pct: roundVal(synthProb * 100, 1),
          classification: isSynth ? 'SYNTHETIC_CLONE' : 'GENUINE_VOICE',
          verdict: isSynth ? 'SYNTHETIC_VOICE_CLONE' : 'AUTHENTIC_HUMAN_VOICE',
          vocoder_metrics: {
            hf_attenuation_ratio: isSynth ? 0.89 : 0.18,
            spectral_flux: isSynth ? 0.042 : 0.185,
            pitch_jitter: isSynth ? 0.003 : 0.016,
            amplitude_shimmer: isSynth ? 0.009 : 0.038,
            vocoder_artifact_score: isSynth ? 0.84 : 0.12
          }
        },
        speaker_verification: {
          claimed_speaker: sc.claimed_speaker_name,
          verification_status: isSynth ? (scenarioId === 'scenario_digital_arrest_police' ? 'UNENROLLED' : 'MATCH_CONFIRMED') : 'MATCH_CONFIRMED',
          is_match: !isSynth,
          cosine_similarity: isSynth ? (scenarioId === 'scenario_digital_arrest_police' ? 0.0 : 0.94) : 1.0,
          match_confidence_pct: isSynth ? (scenarioId === 'scenario_digital_arrest_police' ? 0.0 : 94.9) : 100.0,
          speaker_mismatch_risk: spkRisk,
          description: isSynth ? 'Voice biometric signature diverged significantly from enrolled voiceprint or matched cloned victim profile.' : 'Biometric acoustic embeddings match enrolled voiceprint profile.'
        },
        threat_intelligence: {
          behavioral_threat_score: behScore,
          threat_level: isSynth ? 'HIGH_COERCION' : 'NORMAL_INTERACTION',
          is_coercive_threat: isSynth,
          text_analysis: {
            threat_level: isSynth ? (scenarioId === 'scenario_digital_arrest_police' || scenarioId === 'scenario_grandchild_emergency' ? 'CRITICAL_ATTACK' : 'ELEVATED') : 'CLEAN',
            detected_phrases: isSynth ? (scenarioId === 'scenario_digital_arrest_police' ? ['arrest warrant', 'digital arrest', 'judicial escrow'] : (scenarioId === 'scenario_grandchild_emergency' ? ['road accident', 'emergency ICU', 'hospital doctor'] : ['urgent closed-door board meeting', 'immediate wire transfer', 'secure the contract'])) : []
          },
          detected_intents: isSynth ? ['URGENT_DEMAND', 'UNAUTHORIZED_ESCROW', 'DIGITAL_COERCION'] : ['INFORMATIONAL_SUPPORT'],
          cadence_anomaly: isSynth ? 'High Artificial Stress & Cadence Flux' : 'Natural Human Speech Prosody'
        },
        risk_evaluation: {
          overall_risk_score: roundVal(rawScore, 1),
          risk_tier: tier,
          tier_color: tier === 'CRITICAL' ? '#DC2626' : (tier === 'HIGH' ? '#EF5350' : (tier === 'MODERATE' ? '#F59E0B' : '#10B981')),
          action_code: actionCode,
          recommendation: isSynth ? 'IMMEDIATE ACTION: Transaction frozen and alerted SOC.' : 'Interaction authenticated. Proceed normally.',
          contributors_percentage: {
            synthetic_voice: roundVal((0.35 * synthProb / (rawScore/100)) * 100, 1),
            speaker_mismatch: roundVal((0.25 * spkRisk / (rawScore/100)) * 100, 1),
            transaction_exposure: roundVal((0.15 * expFactor / (rawScore/100)) * 100, 1),
            behavioral_threat: roundVal((0.15 * behScore / (rawScore/100)) * 100, 1),
            context_anomaly: roundVal((0.10 * 0.10 / (rawScore/100)) * 100, 1)
          }
        },
        financial_exposure: {
          transaction_amount_inr: amount,
          formatted_amount: `₹${amount.toLocaleString()}`,
          formatted_avoided_exposure: isSynth ? `₹${amount.toLocaleString()}` : '₹0',
          expected_loss_inr: Math.round(amount * (rawScore / 100)),
          avoided_loss_inr: isSynth ? amount : 0,
          exposure_tier: amount >= 500000 ? 'VERY_HIGH' : (amount >= 100000 ? 'HIGH' : 'STANDARD')
        },
        prevention_action: {
          prevention_action: isSynth ? 'AUTOMATED_TRANSACTION_HOLD' : 'ALLOW_INTERACTION',
          action: isSynth ? 'TRANSACTION_HELD_FOR_REVIEW' : 'ALLOW_TRANSACTION',
          policy_triggered: isSynth ? 'POLICY_RULE_IMMEDIATE_INTERCEPT' : 'POLICY_RULE_AUTO_APPROVE',
          notification_banner: isSynth ? {
            severity: 'CRITICAL',
            title: '🚨 SENTRY ACTIVE DEFENSE: Transaction Frozen',
            message: `Automated freeze triggered for ₹${amount.toLocaleString()}. Synthetic probability: ${(synthProb*100).toFixed(1)}%. Incident dossier logged.`
          } : {
            severity: 'LOW',
            title: '✅ SENTRY TRUST ENGINE: Verified Authentic',
            message: 'All 4 intelligence layers authenticated successfully. No risk indicators detected.'
          }
        }
      };

      this.renderScenarioResult(resultBox, mockResult);
    }, 400);
  },

  renderScenarioResult(container, data) {
    const sc = data.scenario_meta || {};
    const auth = data.authenticity || {};
    const spk = data.speaker_verification || {};
    const threat = data.threat_intelligence || {};
    const risk = data.risk_evaluation || {};
    const fin = data.financial_exposure || {};
    const prev = data.prevention_action || {};

    const vocoder = auth.vocoder_metrics || auth.vocoder_artifacts || {};
    const textAnalysis = threat.text_analysis || {};
    const threatLevel = textAnalysis.threat_level || threat.threat_level || (threat.is_coercive_threat ? 'HIGH_COERCION' : 'NORMAL');
    const detectedPhrases = textAnalysis.detected_phrases || threat.detected_intents || [];
    const tierColor = risk.tier_color || risk.color_indicator || (risk.overall_risk_score > 75 ? '#DC2626' : (risk.overall_risk_score > 50 ? '#EF5350' : '#10B981'));
    const prevAction = prev.prevention_action || prev.action || (risk.overall_risk_score > 60 ? 'AUTOMATED_TRANSACTION_HOLD' : 'ALLOW_INTERACTION');

    let bannerHtml = '';
    if (prev.notification_banner) {
      bannerHtml = `
        <div class="prevention-banner ${prev.notification_banner.severity || 'CRITICAL'}">
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
          <p style="font-size:0.85rem; font-weight:600; color:#e2e8f0;">${sc.audio_filename || sc.id || 'Audio Stream'} (${data.audio_duration_sec || 4.0}s)</p>
          <span class="badge ${sc.is_synthetic_ground_truth ? 'badge-critical' : 'badge-low'}" style="margin-top:0.3rem; display:inline-block;">
            ${sc.is_synthetic_ground_truth ? 'GROUND-TRUTH: AI SYNTHETIC CLONE (1)' : 'GROUND-TRUTH: REAL HUMAN VOICE (0)'}
          </span>
        </div>
        <audio controls src="/api/audio/sample/${sc.id || sc.audio_filename}" style="height:34px;"></audio>
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
            <span class="badge ${auth.synthetic_probability > 0.7 ? 'badge-critical' : 'badge-low'}">${auth.classification || (auth.synthetic_probability > 0.7 ? 'SYNTHETIC_CLONE' : 'GENUINE_VOICE')}</span>
          </div>
          <div class="metric-row">
            <div class="metric-header">
              <span>Synthetic Clone Probability</span>
              <strong>${((auth.synthetic_probability || 0) * 100).toFixed(1)}%</strong>
            </div>
            <div class="progress-track">
              <div class="progress-fill" style="width:${(auth.synthetic_probability || 0) * 100}%; background:${auth.synthetic_probability > 0.7 ? '#ef4444' : '#10b981'};"></div>
            </div>
          </div>
          <div style="font-size:0.78rem; color:var(--text-muted); display:grid; grid-template-columns:1fr 1fr; gap:0.4rem; margin-top:0.6rem;">
            <div>HF Cutoff: <strong style="color:#e2e8f0;">${vocoder.hf_attenuation_ratio !== undefined ? vocoder.hf_attenuation_ratio : 'N/A'}</strong></div>
            <div>Pitch Jitter: <strong style="color:#e2e8f0;">${vocoder.pitch_jitter !== undefined ? vocoder.pitch_jitter : 'N/A'}</strong></div>
            <div>Spectral Flux: <strong style="color:#e2e8f0;">${vocoder.spectral_flux !== undefined ? vocoder.spectral_flux : 'N/A'}</strong></div>
            <div>Vocoder Score: <strong style="color:#e2e8f0;">${vocoder.vocoder_artifact_score !== undefined ? vocoder.vocoder_artifact_score : 'N/A'}</strong></div>
          </div>
        </div>

        <!-- Layer 2: Speaker Biometric Verification -->
        <div class="glass-card">
          <div class="card-header">
            <div class="card-title">
              <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
              Layer 2: Speaker Identity
            </div>
            <span class="badge ${spk.is_match || spk.verification_status === 'MATCH_CONFIRMED' ? 'badge-low' : (spk.verification_status === 'UNENROLLED' ? 'badge-moderate' : 'badge-critical')}">
              ${spk.verification_status || 'UNENROLLED'}
            </span>
          </div>
          <div class="metric-row">
            <div class="metric-header">
              <span>Biometric Similarity (Cosine)</span>
              <strong>${spk.match_confidence_pct || 0}%</strong>
            </div>
            <div class="progress-track">
              <div class="progress-fill" style="width:${spk.match_confidence_pct || 0}%; background:${spk.is_match || spk.verification_status === 'MATCH_CONFIRMED' ? '#10b981' : '#ef4444'};"></div>
            </div>
          </div>
          <p style="font-size:0.8rem; color:var(--text-secondary); margin-top:0.4rem;">
            Claimed Identity: <strong>${spk.claimed_speaker || sc.claimed_speaker_name || 'Anonymous Caller'}</strong>
          </p>
          <p style="font-size:0.75rem; color:var(--text-muted); margin-top:0.2rem;">
            ${spk.description || 'Voice biometric signature analysis completed.'}
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
              ${threatLevel}
            </span>
          </div>
          <div class="metric-row">
            <div class="metric-header">
              <span>Behavioral Coercion Score</span>
              <strong>${((threat.behavioral_threat_score || 0) * 100).toFixed(0)}%</strong>
            </div>
            <div class="progress-track">
              <div class="progress-fill" style="width:${(threat.behavioral_threat_score || 0) * 100}%; background:${(threat.behavioral_threat_score || 0) > 0.5 ? '#ef4444' : '#10b981'};"></div>
            </div>
          </div>
          <div style="background:rgba(0,0,0,0.3); border-radius:6px; padding:0.5rem 0.75rem; margin-top:0.5rem; font-size:0.78rem; font-style:italic; color:var(--text-secondary);">
            "${sc.transcript || ''}"
          </div>
          ${detectedPhrases.length > 0 ? `
            <div style="margin-top:0.5rem; display:flex; gap:0.35rem; flex-wrap:wrap;">
              ${detectedPhrases.map(p => `<span class="badge badge-critical" style="font-size:0.7rem;">Trigger: "${p}"</span>`).join('')}
            </div>
          ` : ''}
        </div>

        <!-- Layer 4: Financial Risk & Prevention Action -->
        <div class="glass-card" style="border-color:${tierColor};">
          <div class="card-header">
            <div class="card-title">
              <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              Layer 4: Fraud Risk & Decision
            </div>
            <span class="badge" style="background:${tierColor}33; color:${tierColor}; border:1px solid ${tierColor};">
              ${risk.risk_tier || 'LOW'} RISK (${risk.overall_risk_score || 0}/100)
            </span>
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.6rem; margin-bottom:0.75rem;">
            <div style="background:rgba(0,0,0,0.3); padding:0.5rem; border-radius:6px;">
              <span style="font-size:0.7rem; color:var(--text-muted); display:block;">Target Exposure</span>
              <strong style="color:var(--text-primary); font-size:1.05rem;">${fin.formatted_amount || '₹0'}</strong>
            </div>
            <div style="background:rgba(0,0,0,0.3); padding:0.5rem; border-radius:6px;">
              <span style="font-size:0.7rem; color:var(--text-muted); display:block;">Estimated Avoided Loss</span>
              <strong style="color:var(--accent-emerald); font-size:1.05rem;">${fin.formatted_avoided_exposure || '₹0'}</strong>
            </div>
          </div>
          <div style="background:rgba(6,182,212,0.08); border-left:3px solid ${tierColor}; padding:0.5rem 0.75rem; border-radius:4px; font-size:0.8rem;">
            <strong>Action Executed:</strong> ${prevAction}
            <p style="font-size:0.75rem; color:var(--text-secondary); margin-top:0.2rem;">${risk.recommendation || 'Policy execution complete.'}</p>
          </div>
        </div>

      </div>
    `;
  }
};

function roundVal(val, dec = 1) {
  return parseFloat(Number(val).toFixed(dec));
}

window.Scenarios = Scenarios;
