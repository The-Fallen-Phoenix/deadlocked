# SENTRY: System Architecture & Technical Specification

## 1. Architectural Principles

SENTRY is designed as a **Zero-Trust Voice Security Gateway** tailored for high-volume banking core processors, fintech payment rails (UPI/IMPS), telecommunications SIP trunking, and contact centers.

```
+-----------------------------------------------------------------------------------------------+
|                                      SENTRY PLATFORM                                          |
|                                                                                               |
|  [ Ingestion Layer ]                                                                          |
|  Live WebRTC Stream / Audio Worklet / 16kHz PCM Buffer / SIP Audio Adapter                    |
|                                         |                                                     |
|                                         v                                                     |
|  [ Acoustic Processing Layer ]                                                                |
|  Pre-Emphasis (0.97) -> Energy/Entropy VAD -> 80-bin Mel Spectrogram -> 40-bin LFCC Map      |
|                                         |                                                     |
|                                         v                                                     |
|  +-----------------------------------------------------------------------------------------+  |
|  | Multi-Layer AI Inference Core                                                           |  |
|  |                                                                                         |  |
|  |  [ Layer 1: Authenticity ]     [ Layer 2: Biometrics ]     [ Layer 3: Threat NLP ]      |  |
|  |  - ResNet-2D Spectrogram       - 256-d TDNN Embedding      - Intent / Keyword Scanner   |  |
|  |  - Temporal Self-Attention     - Unit Hypersphere L2       - Coercion & Urgency Rules   |  |
|  |  - Vocoder HF Cutoff           - Cosine Similarity Sc      - Acoustic Cadence Stress    |  |
|  |  - Jitter / Shimmer Physics    - Biometric Hash Vault      - Behavioral Score (0.0-1.0) |  |
|  +-----------------------------------------------------------------------------------------+  |
|                                         |                                                     |
|                                         v                                                     |
|  [ Layer 4: Multi-Factor Financial & Fraud Risk Engine ]                                      |
|  Risk = w1*P_synth + w2*(1 - S_match) + w3*Exposure_Factor + w4*Behavioral + w5*Context       |
|  Tiering: LOW (0-30) | MODERATE (31-60) | HIGH (61-80) | CRITICAL (81-100)                     |
|                                         |                                                     |
|                                         v                                                     |
|  [ Layer 5: Active Prevention Gateway & Circuit-Breaker ]                                     |
|  - CRITICAL (>=80): Automated Transaction Freeze & Lock (Cryptographic Hold Token)            |
|  - HIGH (61-79): Dynamic Step-Up Challenge (Unpredictable time-limited token verification)   |
|  - MODERATE (31-60): Real-Time Warning Banner & Step-Up Recommendation                         |
|  - LOW (0-30): Normal Clearance & Approved Interaction                                        |
|                                         |                                                     |
|                                         v                                                     |
|  [ Forensics & SOC Integration ]                                                              |
|  Tamper-Evident HMAC-SHA256 Signed Dossiers -> Real-Time SIEM Audit Stream (JSONL)            |
+-----------------------------------------------------------------------------------------------+
```

---

## 2. Deep Neural Network Specifications

### 2.1 Acoustic Authenticity Classifier (`SentryAcousticClassifier`)
- **Inputs:**
  - Log-Mel Spectrogram: $\mathbf{X}_{\text{mel}} \in \mathbb{R}^{B \times 1 \times 80 \times T}$
  - Linear Frequency Cepstral Coefficients: $\mathbf{X}_{\text{lfcc}} \in \mathbb{R}^{B \times 1 \times 40 \times T}$
- **Feature Extractors:**
  - Mel Branch: 2D Residual Convolutional Blocks ($1 \to 32 \to 64 \to 128$) with frequency pooling.
  - LFCC Branch: 2D Residual Convolutional Blocks ($1 \to 32 \to 64$).
- **Temporal Attention & Recurrent Pooling:**
  - Multi-Head Attention ($\text{embed\_dim}=192, \text{num\_heads}=4$).
  - Bidirectional GRU ($\text{hidden\_size}=96$, output dimension $192$).
- **Calibration & Vocoder Fusion:**
  - Softmax Classification Head ($[P_{\text{genuine}}, P_{\text{synth\_neural}}]$).
  - Physics-Informed Vocoder Fusion:
    $$P_{\text{synth}} = 0.60 \cdot P_{\text{synth\_neural}} + 0.40 \cdot S_{\text{vocoder\_artifacts}}$$

### 2.2 Biometric Speaker Embedding Network (`SentrySpeakerEmbeddingNet`)
- **Architecture:** 1D Time-Delay Neural Network (TDNN) with dilated convolutions (dilation rates 1, 2, 3) and statistical temporal pooling (mean and standard deviation).
- **Embedding Space:** 256-dimensional unit hypersphere ($\|\mathbf{e}\|_2 = 1.0$).
- **Matching Metric:** Normalized Cosine Similarity:
  $$S_C(\mathbf{e}_{\text{test}}, \mathbf{e}_{\text{ref}}) = \frac{\mathbf{e}_{\text{test}} \cdot \mathbf{e}_{\text{ref}}}{\|\mathbf{e}_{\text{test}}\|_2 \|\mathbf{e}_{\text{ref}}\|_2}$$

---

## 3. Privacy-by-Design & Security Controls

1. **Ephemeral Voice Memory:** Raw audio PCM buffers are processed in memory and purged immediately after feature extraction. No unencrypted audio recordings are written to disk unless explicitly designated for administrative enrollment.
2. **Biometric Pseudonymization:** Speaker voiceprints stored in `data/vault/` are stored as mathematical vectors accompanied by salted HMAC-SHA256 checksums to prevent reverse reconstruction.
3. **Cryptographic Incident Integrity:** Every forensic incident dossier is timestamped and signed with a cryptographic HMAC hash to prevent audit log tampering.
