# Owner: M3
# REST endpoint — POST /api/voice

from fastapi import APIRouter, UploadFile, File
from providers.stt import get_stt_provider

router = APIRouter()
stt = get_stt_provider()

@router.post("/api/voice")
async def voice_endpoint(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    transcript = await stt.transcribe(audio_bytes)
    return {"transcript": transcript}
