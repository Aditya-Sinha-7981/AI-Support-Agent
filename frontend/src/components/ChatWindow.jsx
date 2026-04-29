import { useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import MessageBubble from "./MessageBubble";

export default function ChatWindow({ messages }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!messages.length) {
    return (
      <div className="flex min-h-0 flex-1 items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white/85 text-slate-500 dark:border-[#1e1f22] dark:bg-[#313338] dark:text-[#949ba4]">
        Start the conversation by sending a message.
      </div>
    );
  }

  return (
    <div className="min-h-0 flex-1 space-y-3 overflow-y-auto rounded-2xl border border-slate-200/80 bg-white/75 p-3 shadow-inner dark:border-[#1e1f22] dark:bg-[#313338] md:space-y-4 md:p-5">
      <AnimatePresence initial={false}>
        {messages.map((message) => (
          <motion.div
            key={message.id}
            layout="position"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0, transition: { duration: 0.18 } }}
            exit={{ opacity: 0, y: -8, transition: { duration: 0.12 } }}
          >
            <MessageBubble message={message} />
          </motion.div>
        ))}
      </AnimatePresence>
      <div ref={bottomRef} />
    </div>
  );
}
