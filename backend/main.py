from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Support Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers registered here as M3 builds them
# from api.chat import router as chat_router
# from api.voice import router as voice_router
# app.include_router(chat_router)
# app.include_router(voice_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
