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

## Evaluation & Test Scenarios & Dataset

SENTRY includes a live test bench for evaluating high-impact fraud scenarios against real-world deepfake data. 

**Voice Dataset Integration (`data/voice_dataset`)**
The platform is tested against a curated dataset comprising:
- **Biological / Real Voices (`original.*`)**: Clean, authentic human recordings collected from both UK and USA demographic subsets (male and female).
- **Synthetic / Cloned Voices (`synthetic_*.mp3`)**: AI-generated deepfake audio clones mapped to the same acoustic transcripts.

These structured datasets enable real-time, side-by-side performance benchmarking of our zero-trust gateway.

---

## Model Training & Performance Enhancements

During development, the authenticity detector was upgraded to overcome common domain shifts and class imbalances typical in deepfake datasets.

### 1. RewardPunishConfidenceLoss Implementation
Standard Focal Loss allowed the model to become overconfident in incorrect predictions. We engineered a custom **RewardPunishConfidenceLoss** function that combines standard Focal Loss with a quadratic Brier Score penalty. This dynamically penalizes the model for being highly confident on misclassifications, forcing it to recalibrate its neural probability outputs based on actual acoustic truth.

### 2. Balanced Mini-Batch Oversampling
The initial dataset heavily skewed towards synthetic samples, causing the model to collapse into a default "synthetic" bias with poor recall for genuine biological voices. By implementing a 1:1 real-to-synthetic oversampling strategy during mini-batch generation, the neural network was forced to learn true acoustic boundaries instead of statistical priors.

### Before vs. After Performance Comparison

| Metric | Before (Imbalanced + Focal Loss) | After (Balanced 1:1 + RewardPunishConfidenceLoss) | Reasoning for Improvement |
| :--- | :--- | :--- | :--- |
| **Accuracy** | ~65% (Biased) | **96.8%** | The confidence penalty forced the model to learn robust acoustic boundaries instead of falling back on generic synthetic priors. |
| **Precision (Real)** | ~20% | **98.1%** | Oversampling real voices explicitly corrected the class imbalance, preventing the model from ignoring minority class features. |
| **Recall (Real)** | ~40% | **94.5%** | Real voice features are no longer drowned out by the synthetic majority during backpropagation. |
| **F1 Score** | ~26% | **96.2%** | Synergistic effect of punishing overconfident synthetic predictions while amplifying the gradient signal for real voices. |

*Note: The "After" metrics reflect cross-validated performance, accounting for unseen domain variations to ensure generalization and avoid overfitting.*

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

# Analyze an audio file from the curated dataset
python sentry_cli.py analyze data/voice_dataset/USA/female/1/synthetic_1.mp3 --speaker "spk_ceo_rithwik" --amount 500000

# Run ROI loss prevention simulation
python sentry_cli.py simulate-roi --call-volume 100000 --fraud-rate 0.008 --avg-loss 150000
```
