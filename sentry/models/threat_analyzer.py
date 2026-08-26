"""
Behavioral & Social Engineering Threat Analyzer for SENTRY.
Detects urgency markers, financial coercion patterns, digital arrest threats,
and acoustic speech tempo stress.
"""

import re
from typing import Dict, Any, List, Optional
import numpy as np


class ThreatAnalyzer:
    """Evaluates contextual social engineering and coercive fraud indicators."""

    # Threat Categories & Keyword Patterns
    PATTERNS = {
        "DIGITAL_ARREST_AUTHORITY": [
            r"\b(digital arrest|cbi|police|customs|narcotics|crime branch|arrest warrant|supreme court|trafficking)\b",
            r"\b(stay on line|don't disconnect|confidential investigation|official summons|legal penalty)\b"
        ],
        "FINANCIAL_URGENCY_EXTORTION": [
            r"\b(transfer immediately|wire money|send funds|urgent payment|overdue penalty|account frozen)\b",
            r"\b(otp|cvv|upi pin|netbanking password|approve the transaction|authorize now|immediate rtgs)\b"
        ],
        "FAMILY_EMERGENCY_SCAM": [
            r"\b(hospital|icu deposit|accident|emergency surgery|arrested|police bail|kidnapped|ransom)\b",
            r"\b(please help|send cash immediately|doctor needs deposit|life in danger)\b"
        ],
        "PRESSURE_AND_SECRECY": [
            r"\b(do not tell anyone|keep this secret|confidential|do not consult|right now|hurry up)\b",
            r"\b(before it expires|last warning|final notice|immediate action required)\b"
        ]
    }

    def __init__(self):
        self.compiled_patterns = {
            category: [re.compile(p, re.IGNORECASE) for p in pattern_list]
            for category, pattern_list in self.PATTERNS.items()
        }

    def analyze_text_intent(self, transcript_or_intent: str) -> Dict[str, Any]:
        """
        Analyzes conversation transcript or recognized speech text for coercion & urgency triggers,
        with full support for English, Hindi, and Hinglish code-switching.
        """
        from sentry.models.transcription_ai import multilingual_parser
        ml_res = multilingual_parser.parse_transcript(transcript_or_intent)

        matched_categories = {}
        total_matches = 0
        all_matched_phrases = []

        for category, patterns in self.compiled_patterns.items():
            category_matches = []
            for pat in patterns:
                found = pat.findall(transcript_or_intent)
                if found:
                    category_matches.extend(found)
                    all_matched_phrases.extend(found)
            
            if category_matches:
                matched_categories[category] = {
                    "count": len(category_matches),
                    "phrases": list(set(category_matches))
                }
                total_matches += len(category_matches)

        # Merge multilingual results
        total_matches = max(total_matches, ml_res["total_threat_markers"])
        for k, v in ml_res["matched_categories"].items():
            if k not in matched_categories:
                matched_categories[k] = {"count": len(v), "phrases": v}
        all_matched_phrases = list(set(all_matched_phrases + ml_res["detected_phrases"]))

        # Threat score scaled by intensity of indicators
        threat_score = max(ml_res["linguistic_score"], 0.05)
        threat_level = ml_res["threat_level"]

        return {
            "linguistic_threat_score": round(threat_score, 3),
            "threat_level": threat_level,
            "total_threat_markers": total_matches,
            "matched_categories": matched_categories,
            "detected_phrases": all_matched_phrases,
            "detected_language": ml_res["detected_language"]
        }

    def analyze_acoustic_cadence(self, audio: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """
        Analyzes acoustic speech rate, abrupt tempo spikes, and stress dynamics.
        Attackers and simulated distress scripts exhibit unnatural tempo bursts.
        """
        if len(audio) < sample_rate:
            return {"cadence_stress_score": 0.1, "is_high_tempo": False, "syllable_rate_hz": 4.0}

        # Energy envelope to estimate syllable peak pulse rate
        hop = int(sample_rate * 0.01)  # 10ms
        env = np.array([np.mean(audio[i:i+hop]**2) for i in range(0, len(audio)-hop, hop)])
        
        # Smooth envelope
        if len(env) > 10:
            smooth_env = np.convolve(env, np.ones(5)/5.0, mode="same")
            # Peak detection above average energy
            threshold = np.mean(smooth_env) * 1.2
            peaks = np.where((smooth_env[1:-1] > smooth_env[:-2]) & 
                             (smooth_env[1:-1] > smooth_env[2:]) & 
                             (smooth_env[1:-1] > threshold))[0]
            duration_sec = len(audio) / sample_rate
            syllables_per_sec = len(peaks) / max(duration_sec, 0.5)
        else:
            syllables_per_sec = 4.2

        # Normal conversational speech is 3.5 - 5.2 syllables/sec
        # Coercive urgency or accelerated playback exceeds 6.0 syllables/sec
        if syllables_per_sec > 6.5:
            cadence_score = 0.80
            is_stressed = True
        elif syllables_per_sec > 5.5:
            cadence_score = 0.45
            is_stressed = True
        else:
            cadence_score = 0.10
            is_stressed = False

        return {
            "cadence_stress_score": round(float(cadence_score), 2),
            "syllable_rate_hz": round(float(syllables_per_sec), 2),
            "is_high_tempo_stress": is_stressed
        }

    def analyze_interaction(
        self,
        transcript_text: Optional[str] = None,
        audio: Optional[np.ndarray] = None,
        interaction_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Combines linguistic intent analysis and acoustic stress into an overall behavioral risk score.
        """
        text = transcript_text or ""
        text_analysis = self.analyze_text_intent(text)

        if audio is not None and len(audio) > 0:
            cadence_analysis = self.analyze_acoustic_cadence(audio)
        else:
            cadence_analysis = {"cadence_stress_score": 0.1, "syllable_rate_hz": 4.0, "is_high_tempo_stress": False}

        # Behavioral Score: 70% Linguistic Intent + 30% Acoustic Cadence Stress
        behavioral_score = 0.70 * text_analysis["linguistic_threat_score"] + 0.30 * cadence_analysis["cadence_stress_score"]

        # If high financial context flags exist (e.g. unknown new payee, uncharacteristic high value transfer)
        if interaction_context:
            if interaction_context.get("is_new_beneficiary", False):
                behavioral_score = min(behavioral_score + 0.15, 1.0)
            if interaction_context.get("is_off_hours", False):
                behavioral_score = min(behavioral_score + 0.10, 1.0)

        return {
            "behavioral_threat_score": round(float(behavioral_score), 3),
            "text_analysis": text_analysis,
            "cadence_analysis": cadence_analysis,
            "is_coercive_threat": bool(behavioral_score > 0.50)
        }


threat_analyzer = ThreatAnalyzer()
