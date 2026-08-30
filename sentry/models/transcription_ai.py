"""
Multilingual Indian Speech & Intent Parser for SENTRY.
Supports English, Hindi, and Hinglish Code-Switched Fraud Phrases.
"""

import re
from typing import Dict, Any, List, Optional
import numpy as np


class MultilingualIntentParser:
    """
    Parses spoken transcripts and phonetics in English, Hindi, and Hinglish for voice fraud indicators.
    """

    # Extended Multilingual Fraud Intent Patterns (English + Hindi + Hinglish)
    MULTILINGUAL_PATTERNS = {
        "DIGITAL_ARREST_POLICE": [
            # English
            r"\b(digital arrest|cbi|police|customs|narcotics|arrest warrant|supreme court)\b",
            # Hindi / Hinglish
            r"\b(police thana|arrest ho jaoge|giraftari warrant|cbi investigation|cyber cell se bol rahe hain)\b",
            r"\b(line mat kaatna|call disconnect mat karo|court ka order hai)\b"
        ],
        "URGENT_UPI_TRANSFER": [
            # English
            r"\b(transfer immediately|wire money|send funds|urgent payment|overdue penalty|account frozen)\b",
            # Hindi / Hinglish
            r"\b(turant paise bhejo|upi pin dalo|otp share karo|paisa transfer karo|account block ho jayega)\b",
            r"\b(abhi approve karo|jaldi bhejo|bank account freeze ho raha hai)\b"
        ],
        "FAMILY_HOSPITAL_EMERGENCY": [
            # English
            r"\b(hospital|icu deposit|accident|emergency surgery|arrested|police bail|kidnapped)\b",
            # Hindi / Hinglish
            r"\b(hospital me admit hai|accident ho gaya|doctor ko advance chahiye|emergency me hu)\b",
            r"\b(bachao mujhe|jaldi madad karo|police pakad li hai)\b"
        ],
        "COERCION_SECRECY": [
            # English
            r"\b(do not tell anyone|keep this secret|confidential|do not consult|right now)\b",
            # Hindi / Hinglish
            r"\b(kisi ko mat batana|secret rakhna|kisi se baat mat karo|abhi ke abhi)\b"
        ]
    }

    def __init__(self):
        self.compiled_rules = {
            cat: [re.compile(p, re.IGNORECASE) for p in pats]
            for cat, pats in self.MULTILINGUAL_PATTERNS.items()
        }

    def parse_transcript(self, text: str) -> Dict[str, Any]:
        """
        Scans multilingual transcript for high-risk threat categories.
        """
        matched_flags = {}
        detected_phrases = []
        total_hits = 0

        for category, patterns in self.compiled_rules.items():
            cat_hits = []
            for pat in patterns:
                matches = pat.findall(text)
                if matches:
                    cat_hits.extend(matches)
                    detected_phrases.extend(matches)

            if cat_hits:
                matched_flags[category] = list(set(cat_hits))
                total_hits += len(cat_hits)

        # Compute linguistic threat multiplier
        if total_hits == 0:
            score = 0.05
            threat_level = "CLEAN"
        elif total_hits == 1:
            score = 0.45
            threat_level = "ELEVATED"
        elif total_hits <= 3:
            score = 0.80
            threat_level = "HIGH_COERCION"
        else:
            score = 0.98
            threat_level = "CRITICAL_ATTACK"

        # Detect language / dialect indicators
        has_hindi = bool(re.search(r"[\u0900-\u097F]", text)) or any(
            w in text.lower() for w in ["karo", "bhejo", "mat", "hai", "thana", "giraftari", "abhi", "jaldi", "ho gaya"]
        )

        return {
            "linguistic_score": round(score, 3),
            "threat_level": threat_level,
            "total_threat_markers": total_hits,
            "detected_phrases": list(set(detected_phrases)),
            "matched_categories": matched_flags,
            "detected_language": "Hindi / Hinglish (Code-Switched)" if has_hindi else "English (Indian Dialect)"
        }


multilingual_parser = MultilingualIntentParser()
