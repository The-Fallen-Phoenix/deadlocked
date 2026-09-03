"""
Quick start server launcher for SENTRY Platform.
Automatically detects port conflicts and selects an available port.
"""

import os
import sys
import socket

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import uvicorn
from sentry.core.config import settings


def is_port_available(port: int, host: str = "0.0.0.0") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def get_available_port(preferred_port: int, candidate_ports=(8000, 8080, 8081, 8050)) -> int:
    if is_port_available(preferred_port):
        return preferred_port
    for p in candidate_ports:
        if p != preferred_port and is_port_available(p):
            return p
    return preferred_port


if __name__ == "__main__":
    cli_port = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        cli_port = int(sys.argv[1])

    target_port = cli_port or int(os.environ.get("PORT", settings.port))
    resolved_port = get_available_port(target_port)

    if resolved_port != target_port:
        print(f"[!] Port {target_port} is already in use by another application.")
        print(f"[*] SENTRY automatically selected free port: {resolved_port}\n")

    print(f"============================================================")
    print(f" SENTRY — AI Real-Time Voice Trust & Cyber-Defense Gateway ")
    print(f" Smart India Hackathon 2026 | PS ID: SIH26104              ")
    print(f" 'Hear the Truth.'                                         ")
    print(f"============================================================")
    print(f"[*] Serving web dashboard at: http://localhost:{resolved_port}")
    print(f"[*] Interactive API docs at:  http://localhost:{resolved_port}/docs")
    print(f"============================================================\n")

    uvicorn.run("sentry.api.main:app", host="0.0.0.0", port=resolved_port, reload=False)
