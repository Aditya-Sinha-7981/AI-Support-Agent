import { useCallback, useEffect, useRef, useState } from "react";
import { buildChatWsUrl } from "../services/api";

function makeId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function useWebSocket({ domain, sessionId }) {
  const wsRef = useRef(null);
  const pendingAssistantIdRef = useRef(null);
  const conversationCacheRef = useRef(new Map());
  const activeConversationKey = `${domain}:${sessionId}`;

  const [messages, setMessages] = useState([]);
  const [connectionState, setConnectionState] = useState("connecting");
  const [sentiment, setSentiment] = useState("neutral");

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
    const ws = new WebSocket(buildChatWsUrl(sessionId, domain));
    wsRef.current = ws;
    setConnectionState("connecting");

    ws.onopen = () => {
      setConnectionState("open");
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

      if (payload.type === "done") {
        finalizePendingAssistantTurn();
      }
    };
  }, [domain, sessionId, finalizePendingAssistantTurn]);

  const resetConversation = useCallback(() => {
    conversationCacheRef.current.delete(activeConversationKey);
    setMessages([]);
    setSentiment("neutral");
    pendingAssistantIdRef.current = null;
  }, [activeConversationKey]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  useEffect(() => {
    disconnect();
    const cachedConversation = conversationCacheRef.current.get(activeConversationKey);
    if (cachedConversation) {
      setMessages(cachedConversation.messages);
      setSentiment(cachedConversation.sentiment);
    } else {
      setMessages([]);
      setSentiment("neutral");
    }
    pendingAssistantIdRef.current = null;
    connect();

    return () => {
      disconnect();
    };
  }, [activeConversationKey, connect, disconnect]);

  useEffect(() => {
    conversationCacheRef.current.set(activeConversationKey, { messages, sentiment });
  }, [activeConversationKey, messages, sentiment]);

  const sendMessage = useCallback((text) => {
    const trimmed = text.trim();
    if (
      !trimmed ||
      !wsRef.current ||
      wsRef.current.readyState !== WebSocket.OPEN ||
      pendingAssistantIdRef.current
    ) {
      return false;
    }

    const userMessage = {
      id: makeId(),
      role: "user",
      content: trimmed,
      isComplete: true,
      isStreaming: false,
      sources: [],
      sentiment: null
    };

    const assistantMessageId = makeId();
    const assistantMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      isComplete: false,
      isStreaming: true,
      sources: [],
      sentiment: null
    };

    pendingAssistantIdRef.current = assistantMessageId;
    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    wsRef.current.send(JSON.stringify({ message: trimmed }));
    return true;
  }, []);

  return {
    messages,
    sentiment,
    connectionState,
    sendMessage,
    resetConversation
  };
}
