import io
import sys
import wave
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app  # noqa: E402


def _make_silence_wav_bytes(duration_s: float = 0.5, sample_rate: int = 16000) -> bytes:
    frames = int(duration_s * sample_rate)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * frames)
    return buf.getvalue()


def main() -> None:
    client = TestClient(app)

    wav_bytes = _make_silence_wav_bytes()
    files = {"audio": ("test.wav", wav_bytes, "audio/wav")}
    resp = client.post("/api/voice", files=files)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "transcript" in data, data
    assert isinstance(data["transcript"], str), data
    print(f"PASS: /api/voice returned transcript={data['transcript']!r}")


if __name__ == "__main__":
    main()

