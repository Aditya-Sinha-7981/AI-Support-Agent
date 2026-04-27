export default function StreamingIndicator({ label = "Assistant is thinking..." }) {
  return (
    <div className="mt-2 inline-flex items-center gap-2 text-xs italic text-slate-500 dark:text-[#949ba4]">
      <span>{label}</span>
      <span className="flex items-center gap-1">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current [animation-delay:-0.2s]" />
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current [animation-delay:-0.1s]" />
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
      </span>
    </div>
  );
}
