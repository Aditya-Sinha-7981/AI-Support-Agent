from fastapi import APIRouter, File, HTTPException, UploadFile
from providers.stt import get_stt_provider

router = APIRouter()
ALLOWED_AUDIO_TYPES = {"audio/webm", "audio/wav", "audio/x-wav", "audio/wave"}


def _normalize_content_type(content_type: str | None) -> str:
    if not content_type:
        return ""
    return content_type.split(";", 1)[0].strip().lower()


@router.post("/api/voice")
async def voice_input(audio: UploadFile = File(...)):
    normalized_type = _normalize_content_type(audio.content_type)
    if normalized_type and normalized_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format. Use webm or wav.",
        )

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file.")

    stt = get_stt_provider()
    try:
        transcript = await stt.transcribe(audio_bytes)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Speech transcription failed.") from exc

    return {"transcript": (transcript or "").strip()}
