function SourcesCard({ sources }) {
  if (!sources?.length) return null;

  return (
    <div className="mt-3 space-y-2 rounded-xl border border-slate-200 bg-slate-50/80 p-3 text-sm dark:border-[#1e1f22] dark:bg-[#1e1f22]">
      <p className="font-semibold text-slate-700 dark:text-[#f2f3f5]">Sources</p>
      {sources.map((source, index) => (
        <div
          key={`${source.file}-${source.page}-${index}`}
          className="text-slate-600 dark:text-[#b5bac1]"
        >
          <span className="font-medium">{source.file || "Unknown file"}</span>
          {source.page ? ` - Page ${source.page}` : ""}
        </div>
      ))}
    </div>
  );
}

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[84%] rounded-2xl px-4 py-3 shadow-sm ${
          isUser
            ? "bg-indigo-600 text-white dark:bg-[#5865f2] dark:text-white"
            : "border border-slate-200 bg-white text-slate-900 dark:border-[#1e1f22] dark:bg-[#383a40] dark:text-[#dbdee1]"
        }`}
      >
        <p className={`mb-1 text-[11px] font-semibold ${isUser ? "text-indigo-100" : "text-slate-500 dark:text-[#949ba4]"}`}>
          {isUser ? "You" : "Assistant"}
        </p>
        <p className="whitespace-pre-wrap">{message.content || (message.isStreaming ? "..." : "")}</p>
        {!isUser && message.isStreaming && (
          <p className="mt-2 text-xs italic text-slate-500 dark:text-[#949ba4]">Assistant is thinking...</p>
        )}
        {!isUser && <SourcesCard sources={message.sources} />}
      </div>
    </div>
  );
}
