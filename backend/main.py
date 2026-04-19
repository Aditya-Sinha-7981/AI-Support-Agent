from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.voice import router as voice_router
from api.chat import router as chat_router


app = FastAPI()

# Allow frontend to connect (important later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(voice_router)
app.include_router(chat_router)

@app.get("/")
def home():
    return {"message": "hello"}