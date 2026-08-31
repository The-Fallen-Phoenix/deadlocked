# SENTRY: AI-Powered Real-Time Voice Cloning Detection & Financial Fraud Prevention Platform

**Smart India Hackathon (SIH) 2026**  
- **Problem Statement ID:** SIH26104  
- **Title:** AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks  
- **Organization:** All India Council for Technical Education (AICTE)  
- **Category:** Software  
- **Theme:** Miscellaneous  
- **Team Name:** Deadlocked  
- **Institution:** Indian Institute of Technology Madras (IIT Madras BS Degree Programme)  
- **Team Leader:** Rithwik Sriram (24f3001829)

---

## Executive Overview

SENTRY is an enterprise-grade, zero-trust voice defense platform engineered to detect AI-cloned speech, verify biometric identity, assess social engineering threat context, and execute automated financial fraud prevention in real-time.

Unlike conventional binary classifiers that evaluate recorded audio post-incident, SENTRY processes live streaming audio with sub-second latency, fusing acoustic signal processing, deep neural networks, biometric verification, and automated transaction hold gateways before fraudulent transfers succeed.

---

## Core System Architecture

SENTRY operates through four integrated intelligence and prevention layers:

```
[Voice Stream] ──► [Audio Preprocessing] ──► [4-Layer Intelligence Engine] ──► [Active Prevention Gateway]
                                                  ├── 1. Voice Authenticity           ├── Automated Transaction Hold
                                                  ├── 2. Biometric Verification       ├── Dynamic Step-Up Challenge
                                                  ├── 3. Coercion & Threat NLP       └── Signed Forensic Audit Logs
                                                  └── 4. Financial Risk Engine
```

### Layer 1: Voice Authenticity & Deepfake Detection
- **Acoustic Signal Analysis:** Evaluates physical vocoder artifacts, including Linear Frequency Cepstral Coefficients (LFCC), Log-Mel Spectrograms, spectral flux, and high-frequency energy cutoffs ($>5.5\text{ kHz}$).
- **Deep Learning Ensemble:** Fuses spectro-temporal ResNet attention architectures, SpecRNet channel-attention blocks, and transformer acoustic encoders.
- **Micro-Perturbation Forensics:** Measures pitch jitter and amplitude shimmer to distinguish biological vocal tract micro-variations from synthetic speech rigidity.

### Layer 2: Biometric Speaker Identity Verification
- **256-Dimensional Voiceprint Embeddings:** Extracts speaker identity representations onto a normalized unit hypersphere.
- **Encrypted Biometric Vault:** Compares live speech against enrolled voiceprints using cosine similarity and HMAC-SHA256 signatures.

### Layer 3: Coercion & Social Engineering Threat NLP
- **Multilingual Threat Parsing:** Identifies high-risk fraud patterns across English, Hindi, and Hinglish (e.g., Digital Arrest impersonation, urgent UPI transfer demands, emergency medical extortion).
- **Acoustic Cadence Analysis:** Evaluates speech rate and vocal stress markers to detect coerced script delivery.

### Layer 4: Multi-Factor Financial Risk & Active Prevention
- **Dynamic Risk Scoring (0 - 100):** Aggregates deepfake probability, biometric similarity divergence, transaction amount exposure, and threat markers.
- **Automated Circuit Breaker:**
  - **LOW (0 - 30):** Normal transaction processing.
  - **MODERATE (31 - 60):** Enhanced passive monitoring.
  - **HIGH (61 - 80):** Out-of-band dynamic step-up challenge triggered.
  - **CRITICAL (81 - 100):** Automated transaction freeze and account security hold.

---

## Evaluation & Test Scenarios

SENTRY includes pre-configured test vectors covering high-impact fraud scenarios:

1. **Executive Impersonation (CEO Wire Transfer):** High-value corporate fund transfer request using cloned executive voice.
2. **Digital Arrest Police Extortion:** Coercive authority impersonation demanding immediate escrow transfer.
3. **Emergency Family Extortion:** Synthetic voice clone asserting urgent medical bail/deposit needs.
4. **Legitimate Support Call:** Normal genuine human customer interaction baseline.

---

## Technical Stack

- **Backend Framework:** Python 3.10+, PyTorch, Torchaudio, SciPy, NumPy, Scikit-Learn, FastAPI, Uvicorn.
- **Neural Architectures:** Dual-Branch ResNet-Attention, SpecRNet (Squeeze-and-Excitation), Transformer Acoustic Encoders, TDNN Biometric Verifier.
- **Security & Logging:** Ephemeral audio memory buffers, HMAC-SHA256 vector hashing, JSONL SIEM audit trails.
- **User Interface:** Real-time web dashboard featuring live audio streaming, risk gauge visualizers, scenario runners, and ROI simulators.

---

## Getting Started

### Prerequisites & Installation

```bash
# Clone repository
git clone https://github.com/The-Fallen-Phoenix/deadlocked.git
cd deadlocked

# Install dependencies
pip install -r requirements.txt
```

### Running System Tests

```bash
python -m pytest tests/ -v
```

### Launching the Application

```bash
python run_server.py
```

Access the interface at `http://localhost:8000` and API documentation at `http://localhost:8000/docs`.

### CLI Operations

```bash
# Execute pre-packaged test scenarios
python sentry_cli.py demo

# Analyze an audio file
python sentry_cli.py analyze data/sample_audio/ceo_clone_attack.wav --speaker "spk_ceo_rithwik" --amount 500000

# Run ROI loss prevention simulation
python sentry_cli.py simulate-roi --call-volume 100000 --fraud-rate 0.008 --avg-loss 150000
```
