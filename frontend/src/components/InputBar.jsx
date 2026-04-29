import VoiceInput from "./VoiceInput";

export default function InputBar({
  domain,
  draft,
  setDraft,
  onSubmit,
  statusText,
  suggestions,
  onSuggestionClick,
  onVoiceTranscript,
  connectionState
}) {
  return (
    <form
      onSubmit={onSubmit}
      className="mt-2 rounded-2xl border border-slate-200/70 bg-white/90 p-2.5 shadow-sm backdrop-blur dark:border-[#1e1f22] dark:bg-[#2b2d31] md:mt-3 md:p-3"
    >
      {!!statusText && (
        <div className="mb-3 flex items-center gap-2 rounded-lg border border-sky-200 bg-sky-50 px-3 py-2 dark:border-sky-800/60 dark:bg-sky-950/30">
          <span className="h-2 w-2 animate-pulse rounded-full bg-sky-500" />
          <p className="text-xs font-semibold text-sky-800 dark:text-sky-200">{statusText}</p>
        </div>
      )}

      <div className="mb-2 md:mb-3">
        <VoiceInput onTranscript={onVoiceTranscript} />
      </div>

      {!!suggestions.length && (
        <div className="mb-2 rounded-xl border border-indigo-200 bg-indigo-50/60 p-2 dark:border-indigo-900/60 dark:bg-indigo-950/25 md:mb-3 md:p-2.5">
          <p className="mb-2 text-[11px] font-bold uppercase tracking-wide text-indigo-700 dark:text-indigo-300">
            Suggested Next Questions
          </p>
          <div className="flex max-h-24 flex-wrap gap-2 overflow-y-auto md:max-h-none">
            {suggestions.map((suggestion, index) => (
              <button
                key={`${suggestion}-${index}`}
                type="button"
                onClick={() => onSuggestionClick(suggestion)}
                className="rounded-full border border-indigo-300 bg-white px-3 py-1 text-xs font-semibold text-indigo-700 shadow-sm transition hover:-translate-y-0.5 hover:bg-indigo-100 dark:border-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-200 dark:hover:bg-indigo-900/50"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center gap-2 md:gap-3">
        <input
          type="text"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={`Ask a ${domain} question...`}
          className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 dark:border-[#2b2d31] dark:bg-[#383a40] dark:text-[#dbdee1] dark:placeholder:text-[#949ba4] dark:focus:border-[#5865f2] dark:focus:ring-[#5865f2]/30 md:px-4"
        />
        <button
          type="submit"
          className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 hover:shadow-lg active:scale-95 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:shadow-none dark:bg-[#5865f2] dark:hover:bg-[#4752c4] md:px-6"
          disabled={!draft.trim() || connectionState !== "open"}
        >
          Send
        </button>
      </div>
    </form>
  );
}

