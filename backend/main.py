import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from api.export import router as export_router
from api.voice import router as voice_router
from api.tts import router as tts_router
from api.chat import router as chat_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


app = FastAPI(title="AI Support Agent API")

# Allow frontend to connect (important later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(export_router)
app.include_router(voice_router)
app.include_router(tts_router)
app.include_router(chat_router)

@app.get("/")
def home():
    return {"message": "AI Support Agent backend is running."}


@app.get("/health")
def health():
    return {"status": "ok"}