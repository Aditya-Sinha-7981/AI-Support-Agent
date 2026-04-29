import { useCallback, useEffect, useRef, useState } from "react";
import { buildChatWsUrl } from "../services/api";

const CONVERSATION_CACHE_KEY = "conversationCacheByDomainSession";

function makeId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function useWebSocket({ domain, sessionId, tone }) {
  const wsRef = useRef(null);
  const pendingAssistantIdRef = useRef(null);
  const conversationCacheRef = useRef(null);
  const pendingOutboundRef = useRef(null);
  const activeConversationKey = `${domain}:${sessionId}`;

  const [messages, setMessages] = useState([]);
  const [connectionState, setConnectionState] = useState("connecting");
  const [sentiment, setSentiment] = useState("neutral");
  const [statusText, setStatusText] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [tickets, setTickets] = useState([]);

  if (!conversationCacheRef.current) {
    try {
      const raw = window.localStorage.getItem(CONVERSATION_CACHE_KEY);
      const parsed = raw ? JSON.parse(raw) : {};
      conversationCacheRef.current = new Map(Object.entries(parsed));
    } catch {
      conversationCacheRef.current = new Map();
    }
  }

  const finalizePendingAssistantTurn = useCallback((fallbackText = "") => {
    const pendingId = pendingAssistantIdRef.current;
    if (!pendingId) return;

    setMessages((prev) =>
      prev.map((message) =>
        message.id === pendingId
          ? {
              ...message,
              content: message.content || fallbackText,
              isStreaming: false,
              isComplete: true
            }
          : message
      )
    );
    pendingAssistantIdRef.current = null;
  }, []);

  const connect = useCallback(() => {
    const ws = new WebSocket(buildChatWsUrl(sessionId, domain, tone));
    wsRef.current = ws;
    setConnectionState("connecting");

    ws.onopen = () => {
      setConnectionState("open");
      const queued = pendingOutboundRef.current;
      if (queued) {
        ws.send(queued);
        pendingOutboundRef.current = null;
      }
    };

    ws.onclose = () => {
      finalizePendingAssistantTurn("Connection closed before response completed. Please retry.");
      setConnectionState("closed");
    };

    ws.onerror = () => {
      finalizePendingAssistantTurn("Connection error while generating response. Please retry.");
      setConnectionState("error");
    };

    ws.onmessage = (event) => {
      const payload = JSON.parse(event.data);

      if (payload.type === "status") {
        setStatusText(payload.content || "");
        return;
      }

      if (payload.type === "token") {
        setMessages((prev) =>
          prev.map((message) =>
            message.id === pendingAssistantIdRef.current
              ? {
                  ...message,
                  content: message.content + (payload.content || ""),
                  isStreaming: true
                }
              : message
          )
        );
        return;
      }

      if (payload.type === "sources") {
        setMessages((prev) =>
          prev.map((message) =>
            message.id === pendingAssistantIdRef.current
              ? {
                  ...message,
                  sources: Array.isArray(payload.content) ? payload.content : []
                }
              : message
          )
        );
        return;
      }

      if (payload.type === "sentiment") {
        const value = payload.content || "neutral";
        setSentiment(value);
        setMessages((prev) =>
          prev.map((message) =>
            message.id === pendingAssistantIdRef.current
              ? {
                  ...message,
                  sentiment: value
                }
              : message
          )
        );
        return;
      }

      if (payload.type === "confidence") {
        const confidence = payload.content || null;
        setMessages((prev) =>
          prev.map((message) =>
            message.id === pendingAssistantIdRef.current
              ? {
                  ...message,
                  confidence
                }
              : message
          )
        );
        return;
      }

      if (payload.type === "done") {
        setStatusText("");
        finalizePendingAssistantTurn();
        return;
      }

      if (payload.type === "suggestions") {
        setSuggestions(Array.isArray(payload.content) ? payload.content : []);
        return;
      }

      if (payload.type === "ticket") {
        const next = payload.content;
        if (!next || !next.ticket_id) return;
        setTickets((prev) => {
          if (prev.some((ticket) => ticket.ticket_id === next.ticket_id)) {
            return prev;
          }
          return [next, ...prev];
        });
      }
    };
  }, [domain, sessionId, tone, finalizePendingAssistantTurn]);

  const resetConversation = useCallback(() => {
    conversationCacheRef.current.delete(activeConversationKey);
    setMessages([]);
    setSentiment("neutral");
    setStatusText("");
    setSuggestions([]);
    setTickets([]);
    pendingAssistantIdRef.current = null;
  }, [activeConversationKey]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    pendingOutboundRef.current = null;
  }, []);

  useEffect(() => {
    const cachedConversation = conversationCacheRef.current.get(activeConversationKey);
    if (cachedConversation) {
      setMessages(cachedConversation.messages);
      setSentiment(cachedConversation.sentiment);
      setStatusText(cachedConversation.statusText || "");
      setSuggestions(
        Array.isArray(cachedConversation.suggestions) ? cachedConversation.suggestions : []
      );
      setTickets(Array.isArray(cachedConversation.tickets) ? cachedConversation.tickets : []);
    } else {
      setMessages([]);
      setSentiment("neutral");
      setStatusText("");
      setSuggestions([]);
      setTickets([]);
    }
    pendingAssistantIdRef.current = null;
    pendingOutboundRef.current = null;
  }, [activeConversationKey]);

  useEffect(() => {
    disconnect();
    connect();

    return () => {
      disconnect();
    };
  }, [domain, sessionId, tone, connect, disconnect]);

  useEffect(() => {
    conversationCacheRef.current.set(activeConversationKey, {
      messages,
      sentiment,
      statusText,
      suggestions,
      tickets
    });
    try {
      const asObject = Object.fromEntries(conversationCacheRef.current.entries());
      window.localStorage.setItem(CONVERSATION_CACHE_KEY, JSON.stringify(asObject));
    } catch {
      // ignore localStorage quota/serialization failures and keep in-memory cache
    }
  }, [activeConversationKey, messages, sentiment, statusText, suggestions, tickets]);

  const sendMessage = useCallback(
    (text) => {
      const trimmed = text.trim();
      if (!trimmed || pendingAssistantIdRef.current) {
        return false;
      }

      const now = Date.now();
      const userMessage = {
        id: makeId(),
        role: "user",
        content: trimmed,
        isComplete: true,
        isStreaming: false,
        sources: [],
        sentiment: null,
        confidence: null,
        timestamp: now
      };

      const assistantMessageId = makeId();
      const assistantMessage = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        isComplete: false,
        isStreaming: true,
        sources: [],
        sentiment: null,
        confidence: null,
        timestamp: now
      };

      pendingAssistantIdRef.current = assistantMessageId;
      setSuggestions([]);
      setMessages((prev) => [...prev, userMessage, assistantMessage]);

      const payload = JSON.stringify({ message: trimmed });
      const ws = wsRef.current;

      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(payload);
      } else {
        pendingOutboundRef.current = payload;
        if (!ws || ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
          connect();
        }
      }

      return true;
    },
    [connect]
  );

  return {
    messages,
    sentiment,
    statusText,
    suggestions,
    tickets,
    connectionState,
    sendMessage,
    resetConversation
  };
}
