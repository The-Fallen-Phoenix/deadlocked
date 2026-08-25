"""
Procedural audio waveform and attack scenario synthesis generator for SENTRY.
Generates realistic genuine and synthetic speech audio signals with configurable acoustic artifacts.
"""

from typing import Dict, Any, Tuple
import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal
from pathlib import Path

from sentry.core.config import settings


class AudioScenarioGenerator:
    """Generates synthetic and genuine audio samples for realistic test scenarios."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def generate_formant_speech(
        self,
        duration_sec: float = 3.5,
        base_f0: float = 140.0,
        is_synthetic: bool = False,
        vocoder_noise: float = 0.05,
        tempo_stress: float = 1.0
    ) -> np.ndarray:
        """
        Synthesizes realistic human or cloned speech acoustics using source-filter vocal tract modeling.
        - Genuine: Natural pitch micro-tremor, breath noise, dynamic formants F1-F4, natural cadence.
        - Synthetic: Neural vocoder phase artifacts, pitch over-quantization, high-frequency cutoff, harmonic rigidity.
        """
        t = np.linspace(0, duration_sec, int(self.sample_rate * duration_sec), endpoint=False)
        
        # 1. Pitch Contour (F0)
        if is_synthetic:
            # Synthetic TTS often has overly quantized or robotic linear pitch slopes
            f0_contour = base_f0 + 15.0 * np.sin(2 * np.pi * 1.2 * t * tempo_stress)
            # Add vocoder phase quantization
            phase = np.cumsum(2 * np.pi * f0_contour / self.sample_rate)
            # Pulse train with harmonic buzz
            glottal = signal.sawtooth(phase, width=0.7)
            # Add vocoder harmonic artifact
            glottal += 0.3 * np.sin(2 * phase) + 0.15 * np.sin(4 * phase)
        else:
            # Natural human pitch: Micro-jitter, subharmonic breathiness, smooth inflection
            jitter = 0.03 * np.random.randn(len(t))
            f0_contour = base_f0 + 25.0 * np.sin(2 * np.pi * 0.8 * t * tempo_stress) + 8.0 * np.sin(2 * np.pi * 2.5 * t) + jitter
            phase = np.cumsum(2 * np.pi * f0_contour / self.sample_rate)
            glottal = signal.sawtooth(phase, width=0.5)
            # Natural breath aspiration noise
            glottal += 0.05 * np.random.randn(len(t))

        # 2. Vocal Tract Formants (F1, F2, F3, F4)
        # Formants vary over time to simulate phonemes /a/, /i/, /u/, /e/
        f1_center = 650.0 + 200.0 * np.sin(2 * np.pi * 2.0 * t)
        f2_center = 1700.0 + 400.0 * np.cos(2 * np.pi * 1.5 * t)
        f3_center = 2600.0 + 200.0 * np.sin(2 * np.pi * 1.0 * t)
        f4_center = 3600.0

        # Resonant filtering
        def apply_resonator(x, f_center, bandwidth=120.0):
            r = np.exp(-np.pi * bandwidth / self.sample_rate)
            theta = 2 * np.pi * f_center / self.sample_rate
            b = [1.0 - r, 0.0, 0.0]
            a = [1.0, -2.0 * r * np.cos(theta), r * r]
            return signal.lfilter(b, a, x)

        filtered = apply_resonator(glottal, 700.0, 100.0) * 1.2
        filtered += apply_resonator(glottal, 1600.0, 150.0) * 0.8
        filtered += apply_resonator(glottal, 2500.0, 200.0) * 0.4
        filtered += apply_resonator(glottal, 3500.0, 300.0) * 0.2

        # 3. Speech Syllable Envelope Modulator
        syllable_rate = 4.5 * tempo_stress  # 4.5 syllables per second
        envelope = 0.5 * (1.0 + np.sin(2 * np.pi * syllable_rate * t))
        envelope = np.clip(envelope ** 1.8, 0.02, 1.0)
        
        # Add micro pauses between sentences
        if duration_sec > 2.0:
            pause_start = int(self.sample_rate * 1.6)
            pause_end = int(self.sample_rate * 1.9)
            if pause_end < len(envelope):
                envelope[pause_start:pause_end] *= 0.05

        speech = filtered * envelope

        # 4. Neural Vocoder Post-Processing vs Natural Room Acoustic
        if is_synthetic:
            # Neural vocoder artifact: Steep high-frequency attenuation cutoff at ~5.5kHz
            sos = signal.butter(6, 5500.0, btype="lowpass", fs=self.sample_rate, output="sos")
            speech = signal.sosfilt(sos, speech)
            # Add synthetic quantization noise
            speech += np.random.normal(0, vocoder_noise * 0.05, len(speech))
        else:
            # Natural room acoustics: Subtle room reverberation reflection
            reverb_delay = int(self.sample_rate * 0.035)  # 35ms reflection
            if len(speech) > reverb_delay:
                speech[reverb_delay:] += 0.15 * speech[:-reverb_delay]

        # 5. Normalization
        max_v = np.max(np.abs(speech))
        if max_v > 0:
            speech = speech / max_v * 0.85

        return speech.astype(np.float32)

    def save_wav(self, audio: np.ndarray, filepath: Path):
        """Saves float32 numpy array as 16-bit PCM WAV file."""
        int16_audio = (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)
        wavfile.write(str(filepath), self.sample_rate, int16_audio)

    def generate_all_demo_scenarios(self):
        """Generates pre-packaged attack scenarios for SIH 2026 demonstration."""
        scenarios = [
            {
                "id": "scenario_ceo_wire_transfer",
                "filename": "ceo_urgent_wire_cloned.wav",
                "speaker": "Rithwik Sriram (Executive Profile)",
                "base_f0": 130.0,
                "is_synthetic": True,
                "duration": 4.0,
                "vocoder_noise": 0.08,
                "tempo_stress": 1.35
            },
            {
                "id": "scenario_digital_arrest_police",
                "filename": "digital_arrest_coercion_cloned.wav",
                "speaker": "Inspector Verma (Claimed Official)",
                "base_f0": 110.0,
                "is_synthetic": True,
                "duration": 4.5,
                "vocoder_noise": 0.06,
                "tempo_stress": 1.2
            },
            {
                "id": "scenario_grandchild_emergency",
                "filename": "grandchild_hospital_cloned.wav",
                "speaker": "Aarav (Enrolled Grandchild)",
                "base_f0": 180.0,
                "is_synthetic": True,
                "duration": 3.8,
                "vocoder_noise": 0.07,
                "tempo_stress": 1.4
            },
            {
                "id": "scenario_legitimate_bank_support",
                "filename": "legitimate_support_genuine.wav",
                "speaker": "Sahil Singh (Enrolled Support Rep)",
                "base_f0": 135.0,
                "is_synthetic": False,
                "duration": 4.2,
                "vocoder_noise": 0.01,
                "tempo_stress": 1.0
            },
            {
                "id": "scenario_enrolled_executive_genuine",
                "filename": "rithwik_executive_enrolled_reference.wav",
                "speaker": "Rithwik Sriram (Executive Profile)",
                "base_f0": 132.0,
                "is_synthetic": False,
                "duration": 5.0,
                "vocoder_noise": 0.01,
                "tempo_stress": 1.0
            }
        ]

        for sc in scenarios:
            audio = self.generate_formant_speech(
                duration_sec=sc["duration"],
                base_f0=sc["base_f0"],
                is_synthetic=sc["is_synthetic"],
                vocoder_noise=sc["vocoder_noise"],
                tempo_stress=sc["tempo_stress"]
            )
            filepath = settings.sample_audio_dir / sc["filename"]
            self.save_wav(audio, filepath)

        print(f"Generated {len(scenarios)} audio demonstration samples in {settings.sample_audio_dir}")


scenario_generator = AudioScenarioGenerator()
