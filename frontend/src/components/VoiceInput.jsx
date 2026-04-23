import { useVoiceRecorder } from "../hooks/useVoiceRecorder";

export default function VoiceInput({ onTranscript }) {
  const { isRecording, isTranscribing, transcriptPreview, error, toggleRecording } = useVoiceRecorder({
    onTranscript
  });

  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={toggleRecording}
        disabled={isTranscribing}
        className={`rounded-xl px-3 py-2 text-sm font-semibold transition ${
          isRecording
            ? "bg-rose-500 text-white"
            : "bg-slate-200 text-slate-700 hover:bg-slate-300 dark:bg-[#1e1f22] dark:text-[#dbdee1] dark:hover:bg-[#35373c]"
        } disabled:cursor-not-allowed disabled:opacity-70`}
      >
        {isRecording ? "Stop Mic" : isTranscribing ? "Transcribing..." : "Voice"}
      </button>
      <p className="text-xs text-slate-500 dark:text-[#949ba4]">
        {error || transcriptPreview || "Tap Voice and speak your question."}
      </p>
    </div>
  );
}
