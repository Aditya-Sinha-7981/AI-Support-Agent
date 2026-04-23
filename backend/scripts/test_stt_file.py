#!/usr/bin/env python3
"""
Test /api/voice with a real local audio file (wav/webm) using FastAPI TestClient.

Usage (from backend/):
  python scripts/test_stt_file.py --file test_audio.wav
  python scripts/test_stt_file.py --file path/to/recording.webm
  python scripts/test_stt_file.py --file test_audio.wav --content-type audio/wav
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app  # noqa: E402


def _guess_content_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".wav":
        return "audio/wav"
    if ext == ".webm":
        return "audio/webm"
    return "application/octet-stream"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post a local audio file to /api/voice and print transcript."
    )
    parser.add_argument("--file", required=True, help="Path to local audio file (.wav/.webm).")
    parser.add_argument(
        "--content-type",
        default=None,
        help="Override MIME type (default: inferred from file extension).",
    )
    args = parser.parse_args()

    audio_path = Path(args.file).expanduser().resolve()
    if not audio_path.exists():
        raise SystemExit(f"File not found: {audio_path}")

    content_type = args.content_type or _guess_content_type(audio_path)

    client = TestClient(app)
    with audio_path.open("rb") as f:
        files = {"audio": (audio_path.name, f.read(), content_type)}
    resp = client.post("/api/voice", files=files)

    print(f"Status: {resp.status_code}")
    try:
        body = resp.json()
    except Exception:  # noqa: BLE001
        body = resp.text
    print("Response:", body)

    if resp.status_code != 200:
        raise SystemExit(1)

    transcript = body.get("transcript", "") if isinstance(body, dict) else ""
    print("Transcript:", repr(transcript))


if __name__ == "__main__":
    main()

