from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from providers.tts import get_tts_provider

router = APIRouter()


class TTSRequest(BaseModel):
    text: str


@router.post("/api/tts")
async def tts(req: TTSRequest):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required.")

    provider = get_tts_provider()
    audio = await provider.synthesize(text)
    if not audio:
        raise HTTPException(status_code=500, detail="TTS synthesis failed.")

    return Response(content=audio, media_type="audio/mpeg")

