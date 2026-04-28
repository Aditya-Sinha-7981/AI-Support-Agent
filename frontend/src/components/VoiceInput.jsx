import { useVoiceRecorder } from "../hooks/useVoiceRecorder";
import { motion } from "framer-motion";

export default function VoiceInput({ onTranscript }) {
  const { isRecording, isTranscribing, transcriptPreview, error, toggleRecording } = useVoiceRecorder({
    onTranscript
  });

  return (
    <div className="flex items-center gap-3">
      <div className="relative">
        {isRecording && (
          <motion.div
            className="absolute -inset-1 rounded-2xl bg-rose-500/25"
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{
              opacity: [0.15, 0.35, 0.15],
              scale: [0.98, 1.06, 0.98],
              transition: { duration: 1.25, repeat: Infinity, ease: "easeInOut" }
            }}
          />
        )}
        <button
          type="button"
          onClick={toggleRecording}
          disabled={isTranscribing}
          className={`relative rounded-xl px-3 py-2 text-sm font-semibold transition ${
            isRecording
              ? "bg-rose-500 text-white shadow-sm"
              : "bg-slate-200 text-slate-700 hover:bg-slate-300 dark:bg-[#1e1f22] dark:text-[#dbdee1] dark:hover:bg-[#35373c]"
          } disabled:cursor-not-allowed disabled:opacity-70`}
        >
          {isRecording ? "Stop Mic" : isTranscribing ? "Transcribing..." : "Voice"}
        </button>
      </div>
      {isRecording && (
        <motion.div
          className="inline-flex items-end gap-1 rounded-lg bg-rose-100 px-2 py-1 dark:bg-rose-900/25"
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <span className="h-2 w-1 animate-pulse rounded-sm bg-rose-500 [animation-delay:-0.2s]" />
          <span className="h-3 w-1 animate-pulse rounded-sm bg-rose-500 [animation-delay:-0.1s]" />
          <span className="h-4 w-1 animate-pulse rounded-sm bg-rose-500" />
          <span className="h-3 w-1 animate-pulse rounded-sm bg-rose-500 [animation-delay:-0.15s]" />
          <span className="h-2 w-1 animate-pulse rounded-sm bg-rose-500 [animation-delay:-0.05s]" />
        </motion.div>
      )}
      <p className="text-xs text-slate-500 dark:text-[#949ba4]">
        {error || transcriptPreview || "Tap Voice and speak your question."}
      </p>
    </div>
  );
}
