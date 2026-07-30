"use client";

import { useEffect, useRef, useCallback, useState } from "react";

export type WebSocketStatus = "connecting" | "connected" | "disconnected" | "reconnecting" | "error";

export interface WebSocketMessage {
  type: string;
  data?: unknown;
  [key: string]: unknown;
}

export interface UseWebSocketOptions {
  url: string;
  sessionId?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  enabled?: boolean;
}

export interface UseWebSocketReturn {
  status: WebSocketStatus;
  send: (message: WebSocketMessage) => void;
  subscribe: (events: string[]) => void;
  lastMessage: WebSocketMessage | null;
  reconnectAttempt: number;
  disconnect: () => void;
  connect: () => void;
}

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    url,
    sessionId,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectAttempts = 10,
    reconnectInterval = 3000,
    heartbeatInterval = 30000,
    enabled = true,
  } = options;

  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const subscribedEventsRef = useRef<string[]>([]);
  const shouldReconnectRef = useRef(true);

  const clearTimers = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!enabled) return;
    
    // Close existing connection if any
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return;
    }

    setStatus("connecting");

    // Build WebSocket URL with session ID
    const wsUrl = sessionId ? `${url}/${sessionId}` : url;
    
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("connected");
        setReconnectAttempt(0);
        onConnect?.();

        // Send ping to establish connection
        ws.send(JSON.stringify({ type: "ping" }));

        // Start heartbeat
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }));
          }
        }, heartbeatInterval);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch {
          console.error("Failed to parse WebSocket message:", event.data);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setStatus("error");
        onError?.(error);
      };

      ws.onclose = () => {
        clearTimers();
        
        if (shouldReconnectRef.current && reconnectAttempt < reconnectAttempts) {
          setStatus("reconnecting");
          setReconnectAttempt((prev) => prev + 1);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else {
          setStatus("disconnected");
          onDisconnect?.();
        }
      };
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      setStatus("error");
    }
  }, [url, sessionId, enabled, reconnectAttempts, reconnectInterval, heartbeatInterval, onConnect, onDisconnect, onError, onMessage, clearTimers, reconnectAttempt]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    clearTimers();
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setStatus("disconnected");
  }, [clearTimers]);

  const send = useCallback((message: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn("WebSocket is not connected, cannot send message");
    }
  }, []);

  const subscribe = useCallback((events: string[]) => {
    subscribedEventsRef.current = events;
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "subscribe", events }));
    }
  }, []);

  // Connect on mount
  useEffect(() => {
    if (enabled) {
      shouldReconnectRef.current = true;
      connect();
    }

    return () => {
      shouldReconnectRef.current = false;
      clearTimers();
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [enabled, connect, clearTimers]);

  return {
    status,
    send,
    subscribe,
    lastMessage,
    reconnectAttempt,
    disconnect,
    connect,
  };
}

// Polling fallback hook
export interface UsePollingOptions {
  pollFn: () => Promise<void>;
  interval: number;
  enabled?: boolean;
  onError?: (error: Error) => void;
}

export function usePolling(options: UsePollingOptions) {
  const { pollFn, interval, enabled = true, onError } = options;
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const poll = async () => {
      try {
        await pollFn();
      } catch (error) {
        onError?.(error as Error);
      }
    };

    // Initial poll
    poll();

    // Set up interval
    intervalRef.current = setInterval(poll, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [pollFn, interval, enabled, onError]);

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const start = useCallback(() => {
    if (!intervalRef.current) {
      intervalRef.current = setInterval(pollFn, interval);
    }
  }, [pollFn, interval]);

  return { stop, start };
}
