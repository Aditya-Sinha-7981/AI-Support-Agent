import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app  # noqa: E402


def main() -> None:
    client = TestClient(app)

    resp = client.post("/api/tts", json={"text": "This is a test to see if this thing is working or not, also goddamn sheikh."})
    assert resp.status_code == 200, resp.text
    assert resp.headers.get("content-type", "").startswith("audio/"), resp.headers.get("content-type")
    assert len(resp.content) > 1000, f"Expected audio bytes, got {len(resp.content)}"

    out_path = "tmp_out.mp3"
    with open(out_path, "wb") as f:
        f.write(resp.content)
    print(f"PASS: wrote {len(resp.content)} bytes to {out_path}")


if __name__ == "__main__":
    main()

