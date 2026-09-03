"""
Cybersecurity Audit Logger & SOC Event Stream for SENTRY.
"""

import json
import logging
import time
from collections import deque
from pathlib import Path
from typing import List, Dict, Any, Optional

from sentry.core.config import settings

# Configure standard logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [SENTRY-SOC] %(message)s"
)
logger = logging.getLogger("sentry.soc")


class CyberAuditLogger:
    """Maintains enterprise security incident logs and provides real-time event feeds."""

    def __init__(self, max_in_memory: int = 500):
        self.events_buffer: deque = deque(maxlen=max_in_memory)
        self.log_file = settings.incidents_dir / "audit_trail.jsonl"
        self._load_existing_events()

    def _load_existing_events(self):
        """Loads events from disk or initializes realistic cyber audit stream."""
        if self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line_s = line.strip()
                        if line_s:
                            self.events_buffer.appendleft(json.loads(line_s))
            except Exception as e:
                logger.error(f"Error loading audit trail: {e}")

        if len(self.events_buffer) == 0:
            now = time.time()
            seed_events = [
                {
                    "timestamp": now - 3600,
                    "formatted_time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now - 3600)),
                    "session_id": "SES-SCENARIO-CEO-9605",
                    "event_type": "TRANSACTION_FREEZE_TRIGGERED",
                    "caller_id": "Rithwik Sriram (Executive Profile)",
                    "risk_level": "CRITICAL",
                    "risk_score": 94.2,
                    "action_taken": "AUTOMATED_HOLD",
                    "details": {"hold_id": "HOLD-CEO-8821", "amount": 500000.0}
                },
                {
                    "timestamp": now - 1800,
                    "formatted_time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now - 1800)),
                    "session_id": "SES-SCENARIO-POLICE-4412",
                    "event_type": "AI_CLONE_ATTACK_MITIGATED",
                    "caller_id": "Inspector Verma (Claimed Official)",
                    "risk_level": "CRITICAL",
                    "risk_score": 89.6,
                    "action_taken": "AUTOMATED_TRANSACTION_HOLD",
                    "details": {"hold_id": "HOLD-CBI-3942", "amount": 250000.0}
                },
                {
                    "timestamp": now - 900,
                    "formatted_time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now - 900)),
                    "session_id": "SES-SCENARIO-MED-7719",
                    "event_type": "VOICE_BIOMETRIC_MISMATCH_LOGGED",
                    "caller_id": "Emergency Casualty Desk",
                    "risk_level": "HIGH",
                    "risk_score": 84.5,
                    "action_taken": "STEP_UP_DYNAMIC_VOICE_CHALLENGE",
                    "details": {"hold_id": "HOLD-MED-1094", "amount": 180000.0}
                },
                {
                    "timestamp": now - 450,
                    "formatted_time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now - 450)),
                    "session_id": "SES-SCENARIO-SUPPORT-2210",
                    "event_type": "TELEPHONY_SPEECH_VERIFIED",
                    "caller_id": "Sahil Singh (Enrolled Support Officer)",
                    "risk_level": "LOW",
                    "risk_score": 14.2,
                    "action_taken": "ALLOW_INTERACTION",
                    "details": {"verification_status": "VERIFIED_BIOMETRIC_MATCH"}
                }
            ]
            for ev in reversed(seed_events):
                self.events_buffer.appendleft(ev)
                try:
                    with open(self.log_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(ev) + "\n")
                except Exception:
                    pass

    def log_event(
        self,
        event_type: str,
        risk_level: str,
        risk_score: float,
        details: Dict[str, Any],
        action_taken: str,
        caller_id: Optional[str] = "ANONYMOUS",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Logs a structured cyber defense event."""
        event = {
            "timestamp": time.time(),
            "formatted_time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "session_id": session_id or f"SES-{int(time.time()*1000)%1000000:06d}",
            "event_type": event_type,
            "caller_id": caller_id,
            "risk_level": risk_level,
            "risk_score": round(risk_score, 2),
            "action_taken": action_taken,
            "details": details
        }

        self.events_buffer.appendleft(event)
        logger.info(f"[{event_type}] Level: {risk_level} | Risk: {risk_score} | Action: {action_taken}")

        # Persist to disk in append mode
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist audit log to disk: {e}")

        return event

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns the most recent security events."""
        return list(self.events_buffer)[:limit]


audit_logger = CyberAuditLogger()
