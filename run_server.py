"""
Quick start server launcher for SENTRY Platform.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import uvicorn
from sentry.core.config import settings

if __name__ == "__main__":
    print(f"============================================================")
    print(f" SENTRY — AI Real-Time Voice Trust & Cyber-Defense Gateway ")
    print(f" Smart India Hackathon 2026 | PS ID: SIH26104              ")
    print(f" 'Hear the Truth.'                                         ")
    print(f"============================================================")
    print(f"[*] Serving web dashboard at: http://localhost:8000")
    print(f"[*] Interactive API docs at:  http://localhost:8000/docs")
    print(f"============================================================\n")
    uvicorn.run("sentry.api.main:app", host="0.0.0.0", port=8000, reload=False)
