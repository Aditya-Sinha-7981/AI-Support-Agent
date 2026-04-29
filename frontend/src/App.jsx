
import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import ChatWindow from "./components/ChatWindow";
import AdminUploadPanel from "./components/AdminUploadPanel";
import InputBar from "./components/InputBar";
import IntroScreen from "./components/IntroScreen";
import TopBar from "./components/TopBar";
import { useWebSocket } from "./hooks/useWebSocket";
import { synthesizeSpeech } from "./services/api";

function makeSessionId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function createInitialChatState() {
  const bankingId = makeSessionId();
  const ecommerceId = makeSessionId();
  const now = Date.now();
  return {
    activeSessionByDomain: {
      banking: bankingId,
      ecommerce: ecommerceId
    },
    threadsByDomain: {
      banking: [{ id: bankingId, title: "Banking Chat 1", updatedAt: now }],
      ecommerce: [{ id: ecommerceId, title: "Ecommerce Chat 1", updatedAt: now }]
    }
  };
}

function loadStoredChatState() {
  try {
    const raw = window.localStorage.getItem("chatStateByDomain");
    if (!raw) return createInitialChatState();
    const parsed = JSON.parse(raw);
    const bankingThreads = Array.isArray(parsed?.threadsByDomain?.banking)
      ? parsed.threadsByDomain.banking
      : [];
    const ecommerceThreads = Array.isArray(parsed?.threadsByDomain?.ecommerce)
      ? parsed.threadsByDomain.ecommerce
      : [];
    const bankingActive = parsed?.activeSessionByDomain?.banking;
    const ecommerceActive = parsed?.activeSessionByDomain?.ecommerce;
    if (!bankingThreads.length || !ecommerceThreads.length || !bankingActive || !ecommerceActive) {
      return createInitialChatState();
    }
    return parsed;
  } catch {
    return createInitialChatState();
  }
}

export default function App() {
  const [domain, setDomain] = useState("banking");
  const [chatState, setChatState] = useState(loadStoredChatState);
  const [toneByDomain, setToneByDomain] = useState({
    banking: "neutral",
    ecommerce: "neutral"
  });
  const [draft, setDraft] = useState("");
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [ttsStatus, setTtsStatus] = useState("idle");
  const [showIntro, setShowIntro] = useState(true);
  const voiceSubmitTimerRef = useRef(null);
  const hasUserInteractedRef = useRef(false);
  const lastSpokenMessageByConversationRef = useRef({});
  const conversationActivatedAtRef = useRef(Date.now());
  const currentAudioRef = useRef(null);
  const activeSessionId = chatState.activeSessionByDomain[domain];
  const activeConversationKey = `${domain}:${activeSessionId}`;
  const activeThreads = chatState.threadsByDomain[domain];
  const tone = toneByDomain[domain] || "neutral";
  const { messages, sentiment, statusText, suggestions, tickets, connectionState, sendMessage } = useWebSocket({
    domain,
    sessionId: activeSessionId,
    tone
  });

  const connectionText = useMemo(() => {
    if (connectionState === "open") return "Connected";
    if (connectionState === "connecting") return "Connecting...";
    if (connectionState === "error") return "Connection error";
    return "Disconnected";
  }, [connectionState]);

  const updateActiveThreadDetails = (messageText) => {
    const trimmed = messageText.trim();
    if (!trimmed) return;
    setChatState((prev) => {
      const updatedThreads = prev.threadsByDomain[domain].map((thread) => {
        if (thread.id !== prev.activeSessionByDomain[domain]) return thread;
        const isDefaultTitle = thread.title.toLowerCase().includes("chat ");
        return {
          ...thread,
          title: isDefaultTitle ? trimmed.slice(0, 32) : thread.title,
          updatedAt: Date.now()
        };
      });

      return {
        ...prev,
        threadsByDomain: {
          ...prev.threadsByDomain,
          [domain]: updatedThreads.sort((a, b) => b.updatedAt - a.updatedAt)
        }
      };
    });
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    hasUserInteractedRef.current = true;
    const sent = sendMessage(draft);
    if (sent) {
      updateActiveThreadDetails(draft);
      setDraft("");
    }
  };

  const handleDomainSwitch = (nextDomain) => {
    if (nextDomain === domain) return;
    setDomain(nextDomain);
    setDraft("");
  };

  const handleNewChat = () => {
    const newSessionId = makeSessionId();
    setChatState((prev) => {
      const nextIndex = prev.threadsByDomain[domain].length + 1;
      return {
        activeSessionByDomain: {
          ...prev.activeSessionByDomain,
          [domain]: newSessionId
        },
        threadsByDomain: {
          ...prev.threadsByDomain,
          [domain]: [
            {
              id: newSessionId,
              title: `${domain === "banking" ? "Banking" : "Ecommerce"} Chat ${nextIndex}`,
              updatedAt: Date.now()
            },
            ...prev.threadsByDomain[domain]
          ]
        }
      };
    });
    setDraft("");
  };

  const handleSelectChat = (sessionId) => {
    setChatState((prev) => ({
      ...prev,
      activeSessionByDomain: {
        ...prev.activeSessionByDomain,
        [domain]: sessionId
      }
    }));
    setDraft("");
  };

  const handleDeleteChat = (sessionId) => {
    setChatState((prev) => {
      const domainThreads = prev.threadsByDomain[domain];
      const remainingThreads = domainThreads.filter((thread) => thread.id !== sessionId);
      const isDeletingActive = prev.activeSessionByDomain[domain] === sessionId;

      let nextThreads = remainingThreads;
      let nextActiveId = prev.activeSessionByDomain[domain];

      if (!nextThreads.length) {
        const replacementId = makeSessionId();
        nextThreads = [
          {
            id: replacementId,
            title: `${domain === "banking" ? "Banking" : "Ecommerce"} Chat 1`,
            updatedAt: Date.now()
          }
        ];
        nextActiveId = replacementId;
      } else if (isDeletingActive) {
        nextActiveId = nextThreads[0].id;
      }

      return {
        ...prev,
        activeSessionByDomain: {
          ...prev.activeSessionByDomain,
          [domain]: nextActiveId
        },
        threadsByDomain: {
          ...prev.threadsByDomain,
          [domain]: nextThreads
        }
      };
    });
    setDraft("");
  };

  const handleVoiceTranscript = (transcript) => {
    hasUserInteractedRef.current = true;
    setDraft(transcript);
    if (voiceSubmitTimerRef.current) {
      window.clearTimeout(voiceSubmitTimerRef.current);
    }
    voiceSubmitTimerRef.current = window.setTimeout(() => {
      const sent = sendMessage(transcript);
      if (sent) {
        updateActiveThreadDetails(transcript);
        setDraft("");
      }
    }, 250);
  };

  const handleSuggestionClick = (suggestedText) => {
    hasUserInteractedRef.current = true;
    const sent = sendMessage(suggestedText);
    if (sent) {
      updateActiveThreadDetails(suggestedText);
      setDraft("");
    }
  };

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDarkMode);
  }, [isDarkMode]);

  useEffect(() => {
    const savedTheme = window.localStorage.getItem("theme");
    if (savedTheme === "light") {
      setIsDarkMode(false);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("theme", isDarkMode ? "dark" : "light");
  }, [isDarkMode]);

  useEffect(() => {
    window.localStorage.setItem("chatStateByDomain", JSON.stringify(chatState));
  }, [chatState]);

  useEffect(() => {
    conversationActivatedAtRef.current = Date.now();
  }, [activeConversationKey]);

  useEffect(() => {
    return () => {
      if (voiceSubmitTimerRef.current) {
        window.clearTimeout(voiceSubmitTimerRef.current);
      }
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    const latestCompletedAssistant = [...messages]
      .reverse()
      .find((message) => message.role === "assistant" && message.isComplete && message.content);

    if (!latestCompletedAssistant) return;

    // Avoid auto-playing cached assistant history when switching/opening conversations.
    const messageTimestamp = latestCompletedAssistant.timestamp || 0;
    if (messageTimestamp < conversationActivatedAtRef.current) {
      lastSpokenMessageByConversationRef.current[activeConversationKey] = latestCompletedAssistant.id;
      return;
    }

    if (!hasUserInteractedRef.current) return;
    if (
      latestCompletedAssistant.id ===
      lastSpokenMessageByConversationRef.current[activeConversationKey]
    ) {
      return;
    }

    let isCancelled = false;
    let audioUrl = "";

    const speakLatestAssistant = async () => {
      try {
        setTtsStatus("loading");
        const audioBlob = await synthesizeSpeech(latestCompletedAssistant.content);
        if (isCancelled) return;
        audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.onended = () => {
          if (!isCancelled) {
            setTtsStatus("idle");
          }
          if (audioUrl) {
            URL.revokeObjectURL(audioUrl);
            audioUrl = "";
          }
        };
        currentAudioRef.current = audio;
        await audio.play();
        if (!isCancelled) {
          setTtsStatus("playing");
          lastSpokenMessageByConversationRef.current[activeConversationKey] =
            latestCompletedAssistant.id;
        }
      } catch {
        if (!isCancelled) {
          setTtsStatus("error");
        }
      }
    };

    speakLatestAssistant();

    return () => {
      isCancelled = true;
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [messages, activeConversationKey]);

  const uiVariants = useMemo(
    () => ({
      hidden: { opacity: 0 },
      show: { opacity: 1, transition: { staggerChildren: 0.06, delayChildren: showIntro ? 0.15 : 0 } }
    }),
    [showIntro]
  );

  const itemVariants = useMemo(
    () => ({
      hidden: { opacity: 0, y: 10, scale: 0.99 },
      show: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.28, ease: "easeOut" } }
    }),
    []
  );

  return (
    <div className="mx-auto flex h-[100dvh] max-w-6xl overflow-hidden p-2 text-slate-900 dark:text-[#dbdee1] md:p-5">
      <IntroScreen isVisible={showIntro} onDone={() => setShowIntro(false)} />
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <motion.div
          variants={uiVariants}
          initial="hidden"
          animate={showIntro ? "hidden" : "show"}
          className="flex h-full min-h-0 flex-col overflow-hidden"
        >
          <div className="min-h-0 flex-1 overflow-y-auto pr-1">
            <motion.div variants={itemVariants} className="shrink-0">
              <TopBar
                domain={domain}
                activeSessionId={activeSessionId}
                onDomainSwitch={handleDomainSwitch}
                onNewChat={handleNewChat}
                isDarkMode={isDarkMode}
                onToggleTheme={() => setIsDarkMode((prev) => !prev)}
                connectionText={connectionText}
                sentiment={sentiment}
                ttsStatus={ttsStatus}
                tone={tone}
                onToneChange={(nextTone) => {
                  const value = nextTone || "neutral";
                  setToneByDomain((prev) => ({ ...prev, [domain]: value }));
                }}
              />
            </motion.div>

            <motion.div variants={itemVariants} className="shrink-0">
              <motion.div
                className="mb-3 flex flex-wrap items-center gap-2 rounded-xl border border-slate-200/70 bg-white/80 p-2 dark:border-[#1e1f22] dark:bg-[#2b2d31]"
                initial="hidden"
                animate="show"
                variants={{
                  hidden: { opacity: 0, y: 10 },
                  show: { opacity: 1, y: 0, transition: { staggerChildren: 0.04 } }
                }}
              >
                <AnimatePresence initial={false}>
                  {activeThreads.map((thread) => {
                    const isActive = thread.id === activeSessionId;
                    return (
                      <motion.div
                        key={thread.id}
                        layout
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0, transition: { duration: 0.18 } }}
                        exit={{ opacity: 0, y: -8, transition: { duration: 0.12 } }}
                        className={`group relative rounded-lg pr-5 ${
                          isActive ? "bg-indigo-600 dark:bg-[#5865f2]" : "bg-slate-100 dark:bg-[#1e1f22]"
                        }`}
                      >
                        <button
                          type="button"
                          onClick={() => handleSelectChat(thread.id)}
                          className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                            isActive
                              ? "text-white"
                              : "text-slate-700 hover:bg-slate-200 dark:text-[#b5bac1] dark:hover:bg-[#35373c]"
                          }`}
                        >
                          {thread.title}
                        </button>
                        <button
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            handleDeleteChat(thread.id);
                          }}
                          className={`absolute right-1 top-1/2 -translate-y-1/2 rounded px-1 text-[10px] font-bold transition ${
                            isActive
                              ? "text-white/80 hover:bg-white/20 hover:text-white"
                              : "text-slate-500 hover:bg-slate-200 hover:text-slate-800 dark:text-[#949ba4] dark:hover:bg-[#35373c] dark:hover:text-[#dbdee1]"
                          }`}
                          aria-label={`Delete ${thread.title}`}
                          title="Delete chat"
                        >
                          ×
                        </button>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              </motion.div>
            </motion.div>

            <motion.main
              variants={itemVariants}
              className="flex min-h-[42dvh] flex-1 flex-col overflow-hidden md:min-h-0"
            >
              <AdminUploadPanel domain={domain} />
              <div className="min-h-[28dvh] flex-1 md:min-h-0">
                <ChatWindow messages={messages} />
              </div>
            </motion.main>

            <AnimatePresence initial={false}>
              {!!tickets.length && (
                <motion.section
                  key="tickets"
                  variants={itemVariants}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0, transition: { duration: 0.22, ease: "easeOut" } }}
                  exit={{ opacity: 0, y: -8, transition: { duration: 0.14 } }}
                  className="mt-3 rounded-xl border-2 border-amber-300 bg-amber-50 p-3 shadow-sm dark:border-amber-700 dark:bg-amber-950/25"
                >
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <p className="text-xs font-bold uppercase tracking-wide text-amber-900 dark:text-amber-200">
                      Escalated Tickets
                    </p>
                    <span className="rounded-full bg-amber-200 px-2 py-0.5 text-[10px] font-bold text-amber-900 dark:bg-amber-800/60 dark:text-amber-100">
                      {tickets.length} ACTIVE
                    </span>
                  </div>
                  <div className="space-y-1">
                    {tickets.map((ticket) => (
                      <div
                        key={ticket.ticket_id}
                        className="rounded-lg border border-amber-300/80 bg-white px-3 py-2 text-xs text-amber-900 dark:border-amber-700/70 dark:bg-amber-950/30 dark:text-amber-100"
                      >
                        <span className="font-semibold">#{ticket.ticket_id}</span>
                        <span className="mx-2">•</span>
                        <span>{ticket.summary}</span>
                      </div>
                    ))}
                  </div>
                </motion.section>
              )}
            </AnimatePresence>
          </div>

          <motion.div variants={itemVariants} className="shrink-0 pb-[max(0.4rem,env(safe-area-inset-bottom))]">
            <InputBar
              domain={domain}
              draft={draft}
              setDraft={setDraft}
              onSubmit={handleSubmit}
              statusText={statusText}
              suggestions={suggestions}
              onSuggestionClick={handleSuggestionClick}
              onVoiceTranscript={handleVoiceTranscript}
              connectionState={connectionState}
            />
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
