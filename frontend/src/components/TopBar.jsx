import DomainSwitcher from "./DomainSwitcher";
import ExportButton from "./ExportButton";
import SentimentBadge from "./SentimentBadge";
import { motion } from "framer-motion";

export default function TopBar({
domain,
activeSessionId,
onDomainSwitch,
onNewChat,
isDarkMode,
onToggleTheme,
connectionText,
sentiment,
ttsStatus,
tone,
onToneChange
}) {
const ttsLabel =
ttsStatus === "loading"
? "TTS..."
: ttsStatus === "playing"
? "Speaking"
: "TTS Ready";

return (
<motion.header
className="mb-4 rounded-2xl border border-slate-200/70 bg-white/90 p-4 shadow-md backdrop-blur dark:border-[#1e1f22] dark:bg-[#2b2d31]/95"
initial={{ opacity: 0, y: -12 }}
animate={{ opacity: 1, y: 0, transition: { duration: 0.3 } }}
>
{/* 🔹 ROW 1 */} <div className="grid grid-cols-[auto_1fr_auto] items-center mb-3">

    {/* Left: Title */}
    <div>
      <p className="text-base font-black tracking-tight text-slate-900 dark:text-white">
        Auxo
      </p>
      <p className="text-xs text-slate-500 dark:text-[#949ba4]">
        Customer Support AI
      </p>
    </div>

    {/* Center: Domain Switch */}
    <div className="flex justify-center">
      <DomainSwitcher
        activeDomain={domain}
        onSwitch={onDomainSwitch}
      />
    </div>

    {/* Right: Export */}
    <div className="flex justify-end">
      <ExportButton sessionId={activeSessionId} />
    </div>
  </div>

  {/* 🔹 ROW 2 */}
  <div className="flex flex-wrap items-center justify-end gap-2">
    
    <button
      onClick={onNewChat}
      className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-xs font-semibold text-white transition hover:bg-indigo-500 hover:shadow-lg active:scale-95 dark:bg-[#5865f2] dark:hover:bg-[#4752c4]"
    >
      <span>+</span>
      <span>
        New {domain === "banking" ? "Banking" : "Ecommerce"} Chat
      </span>
    </button>

    <button
      onClick={onToggleTheme}
      className="rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-100 hover:shadow-md active:scale-95 dark:border-[#2b2d31] dark:bg-[#1e1f22] dark:text-[#dbdee1] dark:hover:bg-[#35373c]"
    >
      {isDarkMode ? "Light Mode" : "Dark Mode"}
    </button>

    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-[#1e1f22] dark:text-[#b5bac1]">
      {connectionText}
    </span>

    <SentimentBadge sentiment={sentiment} />

    <select
      value={tone}
      onChange={(e) => onToneChange(e.target.value)}
      className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-100 dark:border-[#2b2d31] dark:bg-[#1e1f22] dark:text-[#dbdee1] dark:hover:bg-[#35373c]"
      aria-label="Response tone profile"
      title="Response tone profile"
    >
      <option value="neutral">Neutral</option>
      <option value="formal">Formal</option>
      <option value="friendly">Friendly</option>
      <option value="concise">Concise</option>
    </select>

    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-[#1e1f22] dark:text-[#b5bac1]">
      {ttsLabel}
    </span>
  </div>
</motion.header>

);
}
