import { useEffect, useMemo, useRef, useState } from "react";
import ChatWindow from "./components/ChatWindow";
import DomainSwitcher from "./components/DomainSwitcher";
import SentimentBadge from "./components/SentimentBadge";
import VoiceInput from "./components/VoiceInput";
import AdminUploadPanel from "./components/AdminUploadPanel";
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
  const [draft, setDraft] = useState("");
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [ttsStatus, setTtsStatus] = useState("idle");
  const voiceSubmitTimerRef = useRef(null);
  const hasUserInteractedRef = useRef(false);
  const lastSpokenMessageByConversationRef = useRef({});
  const lastConversationKeyRef = useRef(null);
  const currentAudioRef = useRef(null);
  const activeSessionId = chatState.activeSessionByDomain[domain];
  const activeConversationKey = `${domain}:${activeSessionId}`;
  const activeThreads = chatState.threadsByDomain[domain];
  const { messages, sentiment, statusText, suggestions, tickets, connectionState, sendMessage } = useWebSocket({
    domain,
    sessionId: activeSessionId
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
    if (lastConversationKeyRef.current !== activeConversationKey) {
      lastConversationKeyRef.current = activeConversationKey;
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

  return (
    <div className="mx-auto flex h-screen max-w-6xl p-3 text-slate-900 dark:text-[#dbdee1] md:p-5">
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200/70 bg-white/90 p-4 shadow-sm backdrop-blur dark:border-[#1e1f22] dark:bg-[#2b2d31]">
          <div className="flex items-center gap-3">
            <div>
              <p className="text-lg font-bold tracking-tight">AI Support Agent</p>
              <p className="text-xs text-slate-500 dark:text-[#b5bac1]">
                Real-time support chat for {domain}
              </p>
            </div>
          </div>

          <DomainSwitcher activeDomain={domain} onSwitch={handleDomainSwitch} />
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleNewChat}
              className="inline-flex items-center gap-1 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-indigo-500 dark:bg-[#5865f2] dark:hover:bg-[#4752c4]"
            >
              <span>+</span>
              <span>New {domain === "banking" ? "Banking" : "Ecommerce"} Chat</span>
            </button>
            <button
              type="button"
              onClick={() => setIsDarkMode((prev) => !prev)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-100 dark:border-[#1e1f22] dark:bg-[#1e1f22] dark:text-[#dbdee1] dark:hover:bg-[#35373c]"
            >
              {isDarkMode ? "Light Mode" : "Dark Mode"}
            </button>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-[#1e1f22] dark:text-[#b5bac1]">
              {connectionText}
            </span>
            <SentimentBadge sentiment={sentiment} />
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-[#1e1f22] dark:text-[#b5bac1]">
              {ttsStatus === "loading" ? "TTS..." : ttsStatus === "playing" ? "Speaking" : "TTS Ready"}
            </span>
          </div>
        </header>

        <div className="mb-3 flex flex-wrap items-center gap-2 rounded-xl border border-slate-200/70 bg-white/80 p-2 dark:border-[#1e1f22] dark:bg-[#2b2d31]">
          {activeThreads.map((thread) => {
            const isActive = thread.id === activeSessionId;
            return (
              <div
                key={thread.id}
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
              </div>
            );
          })}
        </div>

        <main className="min-h-0 flex-1">
          <AdminUploadPanel domain={domain} />
          <ChatWindow messages={messages} />
        </main>

        {!!tickets.length && (
          <section className="mt-3 rounded-xl border-2 border-amber-300 bg-amber-50 p-3 shadow-sm dark:border-amber-700 dark:bg-amber-950/25">
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
          </section>
        )}

        <form
          onSubmit={handleSubmit}
          className="mt-3 rounded-2xl border border-slate-200/70 bg-white/90 p-3 shadow-sm backdrop-blur dark:border-[#1e1f22] dark:bg-[#2b2d31]"
        >
          {!!statusText && (
            <div className="mb-3 flex items-center gap-2 rounded-lg border border-sky-200 bg-sky-50 px-3 py-2 dark:border-sky-800/60 dark:bg-sky-950/30">
              <span className="h-2 w-2 animate-pulse rounded-full bg-sky-500" />
              <p className="text-xs font-semibold text-sky-800 dark:text-sky-200">{statusText}</p>
            </div>
          )}
          <div className="mb-3">
            <VoiceInput onTranscript={handleVoiceTranscript} />
          </div>
          {!!suggestions.length && (
            <div className="mb-3 rounded-xl border border-indigo-200 bg-indigo-50/60 p-2.5 dark:border-indigo-900/60 dark:bg-indigo-950/25">
              <p className="mb-2 text-[11px] font-bold uppercase tracking-wide text-indigo-700 dark:text-indigo-300">
                Suggested Next Questions
              </p>
              <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion, index) => (
                <button
                  key={`${suggestion}-${index}`}
                  type="button"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="rounded-full border border-indigo-300 bg-white px-3 py-1 text-xs font-semibold text-indigo-700 shadow-sm transition hover:-translate-y-0.5 hover:bg-indigo-100 dark:border-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-200 dark:hover:bg-indigo-900/50"
                >
                  {suggestion}
                </button>
              ))}
              </div>
            </div>
          )}
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={`Ask a ${domain} question...`}
              className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 dark:border-[#1e1f22] dark:bg-[#383a40] dark:text-[#dbdee1] dark:placeholder:text-[#949ba4] dark:focus:border-[#5865f2] dark:focus:ring-[#5865f2]/25"
            />
            <button
              type="submit"
              className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-[#5865f2] dark:hover:bg-[#4752c4]"
              disabled={!draft.trim() || connectionState !== "open"}
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
