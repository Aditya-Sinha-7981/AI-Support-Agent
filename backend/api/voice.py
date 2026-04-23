from fastapi import APIRouter, File, HTTPException, UploadFile
from providers.stt import get_stt_provider

router = APIRouter()
ALLOWED_AUDIO_TYPES = {"audio/webm", "audio/wav", "audio/x-wav", "audio/wave"}


@router.post("/api/voice")
async def voice_input(audio: UploadFile = File(...)):
    if audio.content_type and audio.content_type.lower() not in ALLOWED_AUDIO_TYPES:
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
