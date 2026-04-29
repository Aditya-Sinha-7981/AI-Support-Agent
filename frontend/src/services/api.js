const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function getWsProtocol() {
  return API_BASE_URL.startsWith("https://") ? "wss" : "ws";
}

function getWsHost() {
  return API_BASE_URL.replace(/^https?:\/\//, "");
}

export function buildChatWsUrl(sessionId, domain, tone = "neutral") {
  const protocol = getWsProtocol();
  const host = getWsHost();
  return `${protocol}://${host}/ws/chat/${sessionId}?domain=${encodeURIComponent(
    domain
  )}&tone=${encodeURIComponent(tone)}`;
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

export async function uploadAdminDocument(domain, file) {
  const formData = new FormData();
  formData.append("domain", domain);
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/admin/ingest`, {
    method: "POST",
    body: formData
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Document ingestion request failed.");
  }

  return payload;
}

export async function exportConversation(sessionId) {
  if (!sessionId) {
    throw new Error("Session ID is required for export.");
  }

  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/export`);
  if (!response.ok) {
    throw new Error("Conversation export request failed.");
  }
  return response.blob();
}
