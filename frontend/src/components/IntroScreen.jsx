import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";

export default function IntroScreen({ isVisible, onDone }) {
  const [isMounted, setIsMounted] = useState(isVisible);

  useEffect(() => {
    setIsMounted(isVisible);
  }, [isVisible]);

  useEffect(() => {
    if (!isMounted) return;
    // Hero screen visible for 3.5s, then fades out over 0.8s
    const t = window.setTimeout(() => {
      onDone?.();
    }, 3500);
    return () => window.clearTimeout(t);
  }, [isMounted, onDone]);

  return (
    <AnimatePresence>
      {isMounted && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-white via-white to-slate-50 dark:from-[#0a0a0a] dark:via-[#1e1f22] dark:to-[#2b2d31]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1, transition: { duration: 0.35 } }}
          exit={{ opacity: 0, transition: { duration: 0.8, ease: "easeInOut" } }}
        >
          {/* Animated background gradient */}
          <motion.div
            className="absolute inset-0 opacity-40 dark:opacity-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, transition: { duration: 0.5 } }}
            exit={{ opacity: 0, transition: { duration: 0.6 } }}
          >
            <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-300 dark:bg-indigo-600 rounded-full filter blur-3xl opacity-20 dark:opacity-10" />
            <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-300 dark:bg-purple-600 rounded-full filter blur-3xl opacity-20 dark:opacity-10" />
          </motion.div>

          <motion.div
            className="relative z-10 text-center px-6 max-w-4xl"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0, transition: { duration: 0.65, ease: "easeOut", delay: 0.15 } }}
            exit={{ opacity: 0, scale: 0.95, y: -30, transition: { duration: 0.6, ease: "easeInOut" } }}
          >
            {/* Tagline */}
            <motion.p
              className="text-sm sm:text-base font-semibold tracking-widest uppercase text-indigo-600 dark:text-indigo-400 mb-6"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0, transition: { delay: 0.25, duration: 0.4 } }}
            >
              Experience liftoff
            </motion.p>

            {/* Main heading - MASSIVE */}
            <motion.h1
              className="select-none text-[120px] sm:text-[160px] md:text-[220px] lg:text-[280px] font-black leading-none tracking-tighter text-slate-900 dark:text-white mb-2"
              initial={{ opacity: 0, scale: 0.8, y: 40 }}
              animate={{
                opacity: 1,
                scale: 1,
                y: 0,
                transition: { duration: 0.75, ease: "easeOut", delay: 0.1 }
              }}
              exit={{ opacity: 0, scale: 0.85, y: -40, transition: { duration: 0.6 } }}
            >
              Auxo
            </motion.h1>

            {/* Subtitle */}
            <motion.p
              className="mt-8 text-base sm:text-lg md:text-xl font-semibold text-slate-600 dark:text-[#b5bac1] max-w-xl mx-auto"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0, transition: { delay: 0.4, duration: 0.4 } }}
              exit={{ opacity: 0, transition: { duration: 0.5 } }}
            >
              AI that grows with your customer needs
            </motion.p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

