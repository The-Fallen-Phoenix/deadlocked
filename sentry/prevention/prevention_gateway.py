"""
Active Prevention Gateway & Policy Enforcement Engine for SENTRY.
Translates risk scores into automated defense actions:
Transaction Freeze/Hold, Step-Up Dynamic Verification, Alert Overlays, and Incident Escalations.
"""

import time
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from sentry.core.config import settings
from sentry.core.security import security_manager
from sentry.core.audit_logger import audit_logger


class PreventionGateway:
    """Dispatches automated prevention countermeasures based on dynamic risk thresholds."""

    def __init__(self):
        self.holds_file = settings.incidents_dir / "held_transactions.json"
        self.held_transactions: Dict[str, Dict[str, Any]] = {}
        self._load_held_transactions()

    def _load_held_transactions(self):
        """Loads held transactions from disk or seeds realistic initial records."""
        if self.holds_file.exists():
            try:
                with open(self.holds_file, "r", encoding="utf-8") as f:
                    self.held_transactions = json.load(f)
                    return
            except Exception as e:
                print(f"[!] Error loading held transactions: {e}")

        # Seed realistic attack-vector held transactions
        now = time.time()
        self.held_transactions = {
            "HOLD-CEO-8821": {
                "hold_id": "HOLD-CEO-8821",
                "session_id": "SES-SCENARIO-CEO-9605",
                "caller_id": "Rithwik Sriram (Executive Profile)",
                "amount_inr": 500000.0,
                "beneficiary": "Acme Ventures Holdings (Unregistered Payee)",
                "risk_score": 94.2,
                "reason": "CRITICAL AI Voice Cloning & Executive Impersonation (94.2% Synthetic Risk)",
                "status": "HELD_PENDING_FORENSIC_REVIEW",
                "timestamp": now - 3600
            },
            "HOLD-CBI-3942": {
                "hold_id": "HOLD-CBI-3942",
                "session_id": "SES-SCENARIO-POLICE-4412",
                "caller_id": "Inspector Verma (Claimed Official)",
                "amount_inr": 250000.0,
                "beneficiary": "Judicial Escrow Account #8821 (Fraudulent)",
                "risk_score": 89.6,
                "reason": "CRITICAL Digital Arrest Coercion & Synthetic Police Impersonation",
                "status": "HELD_PENDING_FORENSIC_REVIEW",
                "timestamp": now - 1800
            },
            "HOLD-MED-1094": {
                "hold_id": "HOLD-MED-1094",
                "session_id": "SES-SCENARIO-MED-7719",
                "caller_id": "Emergency Casualty Desk (Claimed Hospital)",
                "amount_inr": 180000.0,
                "beneficiary": "City Care Hospital ICU Escrow",
                "risk_score": 84.5,
                "reason": "CRITICAL Voice Biometric Mismatch & Extortion Urgency",
                "status": "HELD_PENDING_FORENSIC_REVIEW",
                "timestamp": now - 900
            }
        }
        self._save_held_transactions()

    def _save_held_transactions(self):
        """Persists held transactions to disk."""
        try:
            with open(self.holds_file, "w", encoding="utf-8") as f:
                json.dump(self.held_transactions, f, indent=2)
        except Exception as e:
            print(f"[!] Error saving held transactions: {e}")

    def execute_policy(
        self,
        risk_evaluation: Dict[str, Any],
        transaction_amount_inr: float = 0.0,
        caller_id: str = "ANONYMOUS",
        beneficiary: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Applies policy rules and triggers active prevention mechanisms.
        """
        risk_score = risk_evaluation["overall_risk_score"]
        risk_tier = risk_evaluation["risk_tier"]
        sess_id = session_id or f"SES-{uuid.uuid4().hex[:8].upper()}"

        action_result = {
            "session_id": sess_id,
            "timestamp": time.time(),
            "risk_score": risk_score,
            "risk_tier": risk_tier,
            "transaction_status": "NORMAL",
            "challenge_required": False,
            "challenge_details": None,
            "prevention_action": "ALLOW",
            "notification_banner": None,
            "hold_id": None
        }

        # Policy Rule 1: CRITICAL Risk (>= 80.0) -> Auto Freeze / Hold
        if risk_score >= settings.prevention.auto_freeze_risk_threshold:
            hold_id = f"HOLD-{uuid.uuid4().hex[:8].upper()}"
            hold_record = {
                "hold_id": hold_id,
                "session_id": sess_id,
                "caller_id": caller_id,
                "amount_inr": transaction_amount_inr,
                "beneficiary": beneficiary or "Unknown External Account",
                "risk_score": risk_score,
                "reason": "CRITICAL AI Voice Cloning & Impersonation Attack Detected",
                "status": "HELD_PENDING_FORENSIC_REVIEW",
                "timestamp": time.time()
            }
            self.held_transactions[hold_id] = hold_record
            self._save_held_transactions()

            action_result.update({
                "transaction_status": "FROZEN_HELD",
                "prevention_action": "AUTOMATED_TRANSACTION_HOLD",
                "hold_id": hold_id,
                "notification_banner": {
                    "severity": "CRITICAL",
                    "title": "TRANSACTION HELD FOR SECURITY",
                    "message": f"Transfer of ₹{transaction_amount_inr:,.0f} has been temporarily FROZEN by SENTRY to prevent potential voice-cloning fraud."
                }
            })

            # Audit event
            audit_logger.log_event(
                event_type="TRANSACTION_FREEZE_TRIGGERED",
                risk_level="CRITICAL",
                risk_score=risk_score,
                details=hold_record,
                action_taken="AUTOMATED_HOLD",
                caller_id=caller_id,
                session_id=sess_id
            )

        # Policy Rule 2: HIGH Risk (61.0 - 79.9) or Moderate Risk with High Value
        elif (
            risk_score >= settings.prevention.step_up_auth_risk_threshold
            or (risk_score >= settings.prevention.alert_overlay_risk_threshold and transaction_amount_inr >= settings.prevention.require_secondary_challenge_amount)
        ):
            challenge = security_manager.generate_step_up_challenge()
            action_result.update({
                "transaction_status": "PENDING_STEP_UP_CHALLENGE",
                "challenge_required": True,
                "challenge_details": challenge,
                "prevention_action": "STEP_UP_DYNAMIC_VOICE_CHALLENGE",
                "notification_banner": {
                    "severity": "HIGH",
                    "title": "STEP-UP AUTHENTICATION REQUIRED",
                    "message": "Impersonation risk detected. Out-of-band acoustic challenge phrase issued."
                }
            })

            audit_logger.log_event(
                event_type="STEP_UP_CHALLENGE_ISSUED",
                risk_level=risk_tier,
                risk_score=risk_score,
                details={"amount": transaction_amount_inr, "challenge_id": challenge["challenge_id"]},
                action_taken="CHALLENGE_ISSUED",
                caller_id=caller_id,
                session_id=sess_id
            )

        # Policy Rule 3: MODERATE Risk (31.0 - 60.0) -> Warning Banner
        elif risk_score >= settings.prevention.alert_overlay_risk_threshold:
            action_result.update({
                "transaction_status": "FLAGGED_MONITORING",
                "prevention_action": "ALERT_OVERLAY",
                "notification_banner": {
                    "severity": "WARNING",
                    "title": "VOICE ANOMALY DETECTED",
                    "message": "Acoustic or behavioral irregularities detected. Monitor interaction closely."
                }
            })

            audit_logger.log_event(
                event_type="SUSPICIOUS_VOICE_ALERT",
                risk_level="MODERATE",
                risk_score=risk_score,
                details={"amount": transaction_amount_inr},
                action_taken="ALERT_DISPATCHED",
                caller_id=caller_id,
                session_id=sess_id
            )

        # Policy Rule 4: LOW Risk (0 - 30.0) -> Allowed
        else:
            action_result.update({
                "transaction_status": "APPROVED",
                "prevention_action": "ALLOW_INTERACTION",
                "notification_banner": None
            })

        return action_result

    def get_all_held_transactions(self) -> List[Dict[str, Any]]:
        """Returns all currently held transactions."""
        return list(self.held_transactions.values())

    def release_hold(self, hold_id: str, officer_id: str = "SOC_ANALYST_1") -> Optional[Dict[str, Any]]:
        """Releases a held transaction after manual SOC clearance."""
        if hold_id in self.held_transactions:
            record = self.held_transactions[hold_id]
            record["status"] = "RELEASED_BY_SOC"
            record["released_by"] = officer_id
            record["release_timestamp"] = time.time()
            self._save_held_transactions()
            
            audit_logger.log_event(
                event_type="TRANSACTION_HOLD_RELEASED",
                risk_level="INFO",
                risk_score=record["risk_score"],
                details={"hold_id": hold_id, "officer_id": officer_id},
                action_taken="MANUAL_RELEASE",
                session_id=record["session_id"]
            )
            return record
        return None


prevention_gateway = PreventionGateway()
