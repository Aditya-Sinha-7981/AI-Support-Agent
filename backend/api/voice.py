from fastapi import APIRouter, UploadFile, File
from providers.stt import get_stt_provider

router = APIRouter()


@router.post("/api/voice")
async def voice_input(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()

    stt = get_stt_provider()
    transcript = await stt.transcribe(audio_bytes)

    return {"transcript": transcript}
