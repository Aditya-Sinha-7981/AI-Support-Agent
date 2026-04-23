const SENTIMENT_UI = {
  positive: {
    emoji: "😊",
    label: "Positive",
    className: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/35 dark:text-emerald-200"
  },
  neutral: {
    emoji: "😐",
    label: "Neutral",
    className: "bg-slate-100 text-slate-700 dark:bg-[#1e1f22] dark:text-slate-200"
  },
  frustrated: {
    emoji: "😤",
    label: "Frustrated",
    className: "bg-rose-100 text-rose-800 dark:bg-rose-900/35 dark:text-rose-200"
  }
};

export default function SentimentBadge({ sentiment = "neutral" }) {
  const mood = SENTIMENT_UI[sentiment] || SENTIMENT_UI.neutral;

  return (
    <div className={`rounded-full px-3 py-1 text-xs font-semibold tracking-wide ${mood.className}`}>
      <span className="mr-1">{mood.emoji}</span>
      {mood.label}
    </div>
  );
}
