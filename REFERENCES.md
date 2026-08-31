# References & Academic Citations — SENTRY Platform

**Smart India Hackathon (SIH) 2026 — Problem Statement SIH26104**  
**Team Deadlocked | Indian Institute of Technology Madras (IIT Madras BS)**

This document provides complete academic citations, open-source repository references, and theoretical foundations utilized in the design, architecture, and benchmarking of the **SENTRY** AI-powered real-time voice cloning detection and prevention platform.

---

## 1. Speech Anti-Spoofing & Deepfake Detection Repositories

1. **AASIST: Integrated Spectro-Temporal Graph Attention Networks**
   - **Authors:** Jee-weon Jung, Hee-Soo Heo, Hemant A. Patil, et al. (Interspeech 2021 / IEEE TASLP 2022)
   - **Repository:** [clovaai/aasist](https://github.com/clovaai/aasist)
   - **Contribution to SENTRY:** Spectro-temporal attention mechanisms and Linear Frequency Cepstral Coefficient (LFCC) feature representations.

2. **SpecRNet: Spectrogram Residual Network with Squeeze-and-Excitation**
   - **Authors:** Piotr Kawa et al. (IEEE / Interspeech 2023)
   - **Repository:** [piotrkawa/specrnet](https://github.com/piotrkawa/specrnet)
   - **Contribution to SENTRY:** Implementation of SE-ResNet residual blocks with Attentive Statistical Pooling in `sentry/models/specrnet.py`.

3. **Improved DeepFake Detection Using Whisper Features**
   - **Authors:** Piotr Kawa et al. (Interspeech 2024)
   - **Repository:** [piotrkawa/deepfake-whisper-features](https://github.com/piotrkawa/deepfake-whisper-features)
   - **Contribution to SENTRY:** Transformer self-attention acoustic encoder using speech representation tokens in `sentry/models/whisper_encoder.py`.

4. **AUDDT: Audio Deepfake Detection Benchmarking Toolkit**
   - **Authors:** MuSAE Lab, INRS-EMT
   - **Repository:** [MUSAELab/AUDDT](https://github.com/MUSAELab/AUDDT)
   - **Contribution to SENTRY:** Evaluation metric protocols (Equal Error Rate - EER, min t-DCF) in `sentry/data_engine/benchmark_evaluator.py`.

---

## 2. Benchmark Datasets & Challenges

1. **ASVspoof 2021 Challenge (Logical Access & Deepfake Tracks)**
   - **Citation:** Yamagishi, J., Wang, X., Todisco, M., Sahidullah, M., et al. (2021). *ASVspoof 2021: Towards Spoofed and Deepfake Speech Detection in the Wild.*
   - **URL:** [https://www.asvspoof.org](https://www.asvspoof.org)

2. **ASVspoof 2019: Automatic Speaker Verification Spoofing and Countermeasures**
   - **Citation:** Todisco, M., Wang, X., Vestman, V., Sahidullah, M., et al. (2019). *ASVspoof 2019: Future Horizons in Spoofed and Fake Audio Detection.*

3. **WaveFake: A Data Set for Audio Deepfake Detection**
   - **Citation:** Frank, J., & Schönherr, L. (2021). *WaveFake: A Data Set for Audio Deepfake Detection.* Proc. NeurIPS / Interspeech.
   - **Vocoders Analyzed:** HiFi-GAN, MelGAN, Parallel WaveGAN, Multi-band MelGAN, WaveGlow, FullBand MelGAN.

4. **VoxCeleb 1 & 2: Large-Scale Speaker Verification Benchmarks**
   - **Citation:** Nagrani, A., Chung, J. S., & Zisserman, A. (2017). *VoxCeleb: a large-scale speaker identification dataset.* Proc. Interspeech.

---

## 3. Biometrics, Foundation Models & Privacy

1. **SpeechBrain: A General-Purpose Speech Toolkit**
   - **Authors:** Ravanelli, M., Parcollet, T., Plantinga, P., et al. (2021). *SpeechBrain: A General-Purpose Speech Toolkit.*
   - **Repository:** [speechbrain/speechbrain](https://github.com/speechbrain/speechbrain)
   - **Contribution to SENTRY:** ECAPA-TDNN architecture principles for 256-d unit-hypersphere biometric voiceprint embeddings.

2. **IndicTTS & Indian Multilingual Speech Corpora**
   - **Source:** SYSPIN & IndicTTS Project, IIT Madras Speech Lab.
   - **Contribution to SENTRY:** Speech intent patterns for Hindi, Hinglish, and Indian regional dialects.

3. **SafeEar: Privacy-Preserving Audio Deepfake Detection**
   - **Citation:** ACM Conference on Computer and Communications Security (CCS 2024).
   - **Contribution to SENTRY:** Pseudonymized biometric vector storage via HMAC-SHA256 signatures in `sentry/storage/vault.py`.
