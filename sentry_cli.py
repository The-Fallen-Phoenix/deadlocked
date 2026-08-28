"""
SENTRY Command Line Interface (CLI).
Allows terminal-based voice scanning, scenario execution, biometric enrollment, and server launch.
"""

import sys
import argparse
import json
from pathlib import Path

# Ensure UTF-8 stdout for Windows PowerShell & Terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import uvicorn

from sentry.core.config import settings
from sentry.audio.preprocessor import audio_preprocessor
from sentry.models.authenticity_detector import authenticity_detector
from sentry.models.speaker_verifier import speaker_verifier
from sentry.risk.risk_engine import risk_engine
from sentry.risk.financial_engine import financial_engine
from sentry.risk.roi_simulator import roi_simulator
from sentry.storage.vault import biometric_vault
from sentry.scenarios.scenario_manager import scenario_manager
from sentry.api.main import execute_sentry_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="SENTRY - AI Voice Cloning Detection & Fraud Prevention Platform (SIH 2026)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Launch FastAPI server and Web UI")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host address")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port number")
    serve_parser.add_argument("--reload", action="store_true", help="Auto reload")

    # Command: scan
    scan_parser = subparsers.add_parser("scan", help="Scan an audio file for deepfake clone artifacts")
    scan_parser.add_argument("audio_file", help="Path to WAV/MP3 file")
    scan_parser.add_argument("--speaker-id", default=None, help="Claimed speaker ID in vault")
    scan_parser.add_argument("--amount", type=float, default=0.0, help="Transaction amount in INR")
    scan_parser.add_argument("--transcript", default=None, help="Transcript text")

    # Command: scenario
    sc_parser = subparsers.add_parser("scenario", help="Run a pre-configured attack test scenario")
    sc_parser.add_argument("scenario_id", help="Scenario ID (e.g. scenario_ceo_wire_transfer)")

    # Command: list-scenarios
    subparsers.add_parser("list-scenarios", help="List all pre-configured attack test scenarios")

    # Command: list-speakers
    subparsers.add_parser("list-speakers", help="List all enrolled biometric speaker profiles")

    # Command: roi
    roi_parser = subparsers.add_parser("roi", help="Run enterprise ROI & loss avoidance simulator")
    roi_parser.add_argument("--calls", type=int, default=12000000, help="Annual voice interactions")
    roi_parser.add_argument("--ticket", type=float, default=25000.0, help="Average transaction value (INR)")
    roi_parser.add_argument("--fraud-rate", type=float, default=0.15, help="Fraud rate percentage")
    roi_parser.add_argument("--lift", type=float, default=65.0, help="Detection & prevention lift percentage")
    roi_parser.add_argument("--cost", type=float, default=2400000.0, help="Platform cost (INR)")

    args = parser.parse_args()

    if args.command == "serve":
        print(f"[*] Starting SENTRY Cyber-Defense Gateway on http://{args.host}:{args.port}")
        uvicorn.run("sentry.api.main:app", host=args.host, port=args.port, reload=args.reload)

    elif args.command == "scan":
        path = Path(args.audio_file)
        if not path.exists():
            print(f"[!] Error: File not found: {path}")
            sys.exit(1)

        with open(path, "rb") as f:
            audio_bytes = f.read()

        audio, sr = audio_preprocessor.load_audio_from_bytes(audio_bytes)
        result = execute_sentry_pipeline(
            audio=audio,
            session_id=f"CLI-SCAN-{path.stem}",
            claimed_speaker_id=args.speaker_id,
            transcript=args.transcript,
            transaction_amount_inr=args.amount
        )
        print(json.dumps(result, indent=2))

    elif args.command == "scenario":
        sc = scenario_manager.get_scenario(args.scenario_id)
        if not sc:
            print(f"[!] Error: Scenario not found: {args.scenario_id}")
            sys.exit(1)

        audio_path = settings.sample_audio_dir / sc["audio_filename"]
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        audio, _ = audio_preprocessor.load_audio_from_bytes(audio_bytes)
        res = execute_sentry_pipeline(
            audio=audio,
            session_id=f"CLI-SCENARIO-{sc['id']}",
            claimed_speaker_id=sc.get("claimed_speaker_id"),
            transcript=sc.get("transcript"),
            transaction_amount_inr=sc.get("transaction_amount_inr", 0.0)
        )
        print("\n================ SENTRY SCENARIO FORENSICS ================")
        print(f"Scenario: {sc['title']}")
        print(f"Attack Vector: {sc['attack_type']}")
        print(f"Synthetic Probability: {res['authenticity']['synthetic_probability']*100:.1f}% ({res['authenticity']['classification']})")
        print(f"Speaker Match: {res['speaker_verification']['match_confidence_pct']}% ({res['speaker_verification']['verification_status']})")
        print(f"Overall Risk Score: {res['risk_evaluation']['overall_risk_score']}/100 [{res['risk_evaluation']['risk_tier']} RISK]")
        print(f"Target Exposure: {res['financial_exposure']['formatted_amount']}")
        print(f"Avoided Loss: {res['financial_exposure']['formatted_avoided_exposure']}")
        print(f"Prevention Action: {res['prevention_action']['prevention_action']}")
        print("===========================================================\n")

    elif args.command == "list-scenarios":
        for sc in scenario_manager.list_scenarios():
            print(f"- {sc['id']}: {sc['title']} [{sc['category']}] (Amount: ₹{sc['transaction_amount_inr']:,})")

    elif args.command == "list-speakers":
        speakers = biometric_vault.list_speakers()
        print(f"[*] Total Enrolled Speakers: {len(speakers)}")
        for s in speakers:
            print(f"- ID: {s['speaker_id']} | Name: {s['display_name']} | Role: {s['role']} | Hash: {s['biometric_hash'][:16]}...")

    elif args.command == "roi":
        sim = roi_simulator.simulate(
            annual_interactions=args.calls,
            avg_transaction_value_inr=args.ticket,
            estimated_fraud_rate_pct=args.fraud_rate,
            detection_improvement_pct=args.lift,
            annual_platform_cost_inr=args.cost
        )
        m = sim["metrics"]
        print("\n================ SENTRY ENTERPRISE ROI MODEL ================")
        print(f"Annual Interactions: {args.calls:,}")
        print(f"Estimated Loss Before SENTRY: {m['formatted_exposure_before']}")
        print(f"Residual Loss After SENTRY:   {m['formatted_residual_exposure']}")
        print(f"Potential Exposure Avoided:   {m['formatted_exposure_avoided']}")
        print(f"Net Annual Savings:          {m['formatted_net_savings']}")
        print(f"Enterprise ROI Multiplier:    {m['roi_label']}")
        print(f"Break-Even Period:            {m['break_even_months']} Months")
        print("=============================================================\n")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
