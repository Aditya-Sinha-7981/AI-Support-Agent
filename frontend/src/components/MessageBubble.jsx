import StreamingIndicator from "./StreamingIndicator";

function formatTime(timestamp) {
  if (!timestamp) return "";
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function SourcesCard({ sources }) {
  if (!sources?.length) return null;

  return (
    <div className="group mt-3 space-y-2 rounded-xl border border-slate-200/70 bg-gradient-to-b from-white/70 to-slate-50/70 p-3 text-sm shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md dark:border-[#1e1f22] dark:from-[#1e1f22] dark:to-[#1a1b1e] dark:hover:border-[#5865f2]/50">
      <p className="font-semibold text-slate-700 dark:text-[#f2f3f5]">Sources</p>
      <div className="space-y-1.5">
        {sources.map((source, index) => (
          <div
            key={`${source.file}-${source.page}-${index}`}
            className="flex flex-wrap items-center gap-x-2 text-slate-600 dark:text-[#b5bac1]"
          >
            <span className="font-medium">{source.file || "Unknown file"}</span>
            {source.page ? (
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-600 dark:bg-[#2b2d31] dark:text-[#b5bac1]">
                Page {source.page}
              </span>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";
  const showCursor = !isUser && message.isStreaming;
  const timeStr = formatTime(message.timestamp);
  const confidence = message.confidence;
  const level = confidence?.level;

  const confidenceStyles = (() => {
    if (level === "high") {
      return {
        dot: "bg-emerald-500",
        pillBg: "bg-emerald-500/10",
        pillText: "text-emerald-700 dark:text-[#59e3a8]",
      };
    }
    if (level === "medium") {
      return {
        dot: "bg-amber-500",
        pillBg: "bg-amber-500/10",
        pillText: "text-amber-700 dark:text-[#f0c56a]",
      };
    }
    if (level === "low") {
      return {
        dot: "bg-yellow-500",
        pillBg: "bg-yellow-500/10",
        pillText: "text-yellow-800 dark:text-[#f1d36b]",
      };
    }
    return null;
  })();

  return (
    <div className={`flex gap-2 ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[84%] rounded-2xl px-4 py-3 shadow-sm ${
          isUser
            ? "bg-indigo-600 text-white dark:bg-[#5865f2] dark:text-white"
            : "border border-slate-200 bg-white text-slate-900 dark:border-[#1e1f22] dark:bg-[#383a40] dark:text-[#dbdee1]"
        }`}
      >
        <div className="flex items-center justify-between gap-2 mb-1">
          <div className="flex items-center gap-2">
            <p
              className={`text-[11px] font-semibold ${
                isUser
                  ? "text-indigo-100"
                  : "text-slate-500 dark:text-[#949ba4]"
              }`}
            >
              {isUser ? "You" : "Assistant"}
            </p>
            {!isUser && confidenceStyles && (
              <div
                className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 ${confidenceStyles.pillBg} ${confidenceStyles.pillText}`}
                title={
                  typeof confidence?.score === "number"
                    ? `Confidence score: ${confidence.score.toFixed(2)}`
                    : "Confidence"
                }
              >
                <span className={`h-1.5 w-1.5 rounded-full ${confidenceStyles.dot}`} />
                <span className="text-[10px] font-semibold capitalize">
                  {level}
                  {typeof confidence?.score === "number"
                    ? ` (${confidence.score.toFixed(2)})`
                    : ""}
                </span>
              </div>
            )}
          </div>
          {timeStr && (
            <p className={`text-[10px] ${isUser ? "text-indigo-200/60" : "text-slate-400 dark:text-[#6d7680]"}`}>
              {timeStr}
            </p>
          )}
        </div>
        <p className="whitespace-pre-wrap">
          {message.content}
          {showCursor && (
            <span className="ml-0.5 inline-block h-4 w-[2px] animate-pulse rounded-full bg-slate-400 align-[-2px] dark:bg-[#b5bac1]" />
          )}
          {!message.content && message.isStreaming ? "..." : ""}
        </p>
        {!isUser && message.isStreaming && <StreamingIndicator />}
        {!isUser && <SourcesCard sources={message.sources} />}
      </div>
    </div>
  );
}



