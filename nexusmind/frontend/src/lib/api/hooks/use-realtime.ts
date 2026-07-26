"use client";

import { useEffect, useCallback } from "react";
import { useWebSocket, usePolling } from "@/lib/api/websocket";
import { useRealtimeStore } from "@/lib/stores/realtime";
import { getWebSocketUrl, api } from "@/lib/api/client";

export interface UseRealtimeOptions {
  sessionId?: string;
  enabled?: boolean;
  usePollingFallback?: boolean;
  pollingInterval?: number;
}

export function useRealtime(options: UseRealtimeOptions = {}) {
  const { sessionId, enabled = true, usePollingFallback = false, pollingInterval = 5000 } = options;

  const store = useRealtimeStore();
  const wsUrl = getWebSocketUrl();

  // WebSocket hook
  const {
    status,
    send,
    subscribe,
    reconnectAttempt,
    disconnect,
    connect,
    lastMessage,
  } = useWebSocket({
    url: wsUrl,
    sessionId,
    enabled: enabled && !usePollingFallback,
    reconnectAttempts: 10,
    reconnectInterval: 3000,
    heartbeatInterval: 30000,
    onMessage: (message) => {
      store.handleMessage(message);
    },
    onConnect: () => {
      store.setStatus("connected");
      store.setSessionId(sessionId || null);
      store.setLastConnected(new Date().toISOString());
      // Subscribe to events
      subscribe([
        "execution_update",
        "execution_progress",
        "execution_completed",
        "execution_error",
        "agent_status_changed",
        "agent_activated",
        "agent_deactivated",
        "log_entry",
        "artifact",
        "file_created",
        "file_modified",
        "file_deleted",
      ]);
    },
    onDisconnect: () => {
      store.setStatus("disconnected");
    },
    onError: (error) => {
      console.error("WebSocket error:", error);
    },
  });

  // Polling fallback
  const pollFn = useCallback(async () => {
    if (!sessionId) return;

    try {
      // Poll for executions
      const executions = await api.executions.list({ sessionId, limit: 10 });
      for (const exec of executions.executions as unknown[]) {
        const execution = exec as Record<string, unknown>;
        store.updateExecution({
          executionId: execution.id as string,
          state: execution.state as string,
          progress: (execution.progress_percent as number) || 0,
          currentAgent: execution.current_agent as string | undefined,
          step: execution.current_step_index as number | undefined,
          totalSteps: execution.total_steps as number | undefined,
        });

        // Poll for logs
        const logs = await api.executions.getLogs(execution.id as string, 50, 0);
        for (const log of logs as unknown[]) {
          const logEntry = log as Record<string, unknown>;
          store.addLog({
            id: logEntry.id as string,
            level: logEntry.level as string,
            message: logEntry.message as string,
            agentId: logEntry.agent_type as string | undefined,
            agentType: logEntry.agent_type as string | undefined,
            executionId: execution.id as string,
            timestamp: (logEntry.timestamp as string) || new Date().toISOString(),
          });
        }
      }
    } catch (error) {
      console.error("Polling error:", error);
    }
  }, [sessionId, store]);

  usePolling({
    pollFn,
    interval: pollingInterval,
    enabled: enabled && usePollingFallback,
  });

  // Update store with WebSocket status
  useEffect(() => {
    store.setStatus(status);
    store.setReconnectAttempt(reconnectAttempt);
  }, [status, reconnectAttempt, store]);

  return {
    status,
    send,
    subscribe,
    reconnectAttempt,
    disconnect,
    connect,
    lastMessage,
    logs: store.logs,
    executionUpdates: Array.from(store.executionUpdates.values()),
    agentStatuses: Array.from(store.agentStatuses.values()),
    artifacts: store.artifacts,
  };
}

// Hook for specific execution updates
export function useExecutionRealtime(executionId: string) {
  const store = useRealtimeStore();
  
  useEffect(() => {
    return () => {
      store.clearExecution(executionId);
    };
  }, [executionId, store]);

  return {
    update: store.executionUpdates.get(executionId),
    logs: store.logs.filter((l) => l.executionId === executionId),
  };
}

// Hook for specific agent status
export function useAgentRealtime(agentId: string) {
  const store = useRealtimeStore();
  
  useEffect(() => {
    return () => {
      store.clearAgentStatus(agentId);
    };
  }, [agentId, store]);

  return store.agentStatuses.get(agentId);
}
