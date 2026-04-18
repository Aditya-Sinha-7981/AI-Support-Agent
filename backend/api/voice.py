from fastapi import APIRouter, UploadFile, File
from providers.stt import get_stt_provider

router = APIRouter()

@router.post("/api/voice")
async def voice_input(file: UploadFile = File(...)):
    # read audio file
    audio_bytes = await file.read()

    # get STT provider (Deepgram)
    stt = get_stt_provider()

    # convert speech → text
    transcript = await stt.transcribe(audio_bytes)

    # return clean response
    return {
        "transcript": transcript
    }