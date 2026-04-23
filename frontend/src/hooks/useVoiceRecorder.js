import { useCallback, useRef, useState } from "react";
import { sendVoiceAudio } from "../services/api";

export function useVoiceRecorder({ onTranscript }) {
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcriptPreview, setTranscriptPreview] = useState("");
  const [error, setError] = useState("");

  const startRecording = useCallback(async () => {
    setError("");
    setTranscriptPreview("");

    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Microphone is not supported in this browser.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data?.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const audioBlob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        if (!audioBlob.size) {
          setError("No audio captured. Please try again.");
          return;
        }

        setIsTranscribing(true);
        try {
          const result = await sendVoiceAudio(audioBlob);
          const transcript = (result?.transcript || "").trim();
          if (!transcript) {
            setError("No transcript returned. Please try again.");
            return;
          }
          setTranscriptPreview(transcript);
          onTranscript?.(transcript);
        } catch {
          setError("Voice transcription failed. Please try again.");
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
    } catch {
      setError("Microphone permission denied or unavailable.");
    }
  }, [onTranscript]);

  const stopRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
    setIsRecording(false);
  }, []);

  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
      return;
    }
    startRecording();
  }, [isRecording, startRecording, stopRecording]);

  return {
    isRecording,
    isTranscribing,
    transcriptPreview,
    error,
    toggleRecording
  };
}
