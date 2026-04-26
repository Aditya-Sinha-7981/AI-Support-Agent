const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function getWsProtocol() {
  return API_BASE_URL.startsWith("https://") ? "wss" : "ws";
}

function getWsHost() {
  return API_BASE_URL.replace(/^https?:\/\//, "");
}

export function buildChatWsUrl(sessionId, domain) {
  const protocol = getWsProtocol();
  const host = getWsHost();
  return `${protocol}://${host}/ws/chat/${sessionId}?domain=${domain}`;
}

export async function sendVoiceAudio(audioBlob) {
  const formData = new FormData();
  formData.append("audio", audioBlob, "voice.webm");

  const response = await fetch(`${API_BASE_URL}/api/voice`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    throw new Error("Voice transcription request failed.");
  }

  return response.json();
}

export async function synthesizeSpeech(text) {
  const response = await fetch(`${API_BASE_URL}/api/tts`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ text })
  });

  if (!response.ok) {
    throw new Error("TTS synthesis request failed.");
  }

  return response.blob();
}
