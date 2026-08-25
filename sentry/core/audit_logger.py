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
