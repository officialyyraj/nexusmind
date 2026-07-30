"use client";

import { create } from "zustand";
import type { WebSocketStatus, WebSocketMessage } from "@/lib/api/websocket";

// Backend execution states from ExecutionState enum
type BackendExecutionState = 
  | "queued" 
  | "starting" 
  | "planning" 
  | "researching" 
  | "coding" 
  | "reviewing" 
  | "testing" 
  | "documenting" 
  | "completed" 
  | "failed" 
  | "cancelled" 
  | "paused" 
  | "resuming";

// Frontend execution status (matches WorkflowExecution.status)
type FrontendExecutionStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

// Mapping from backend execution states to frontend execution status
const EXECUTION_STATE_MAP: Record<BackendExecutionState, FrontendExecutionStatus> = {
  // Terminal states - direct mapping
  "completed": "completed",
  "failed": "failed",
  "cancelled": "cancelled",
  
  // Active/in-progress states - map to running
  "queued": "pending",
  "starting": "running",
  "planning": "running",
  "researching": "running",
  "coding": "running",
  "reviewing": "running",
  "testing": "running",
  "documenting": "running",
  "paused": "running",
  "resuming": "running",
};

/**
 * Maps backend execution state to frontend execution status.
 * Centralized mapping ensures consistent state representation across the app.
 */
export function mapExecutionStateToStatus(state: string): FrontendExecutionStatus {
  const normalizedState = state.toLowerCase() as BackendExecutionState;
  return EXECUTION_STATE_MAP[normalizedState] ?? "pending";
}

export interface RealtimeEvent {
  id: string;
  type: string;
  data: unknown;
  timestamp: string;
}

export interface ExecutionUpdate {
  executionId: string;
  state: string;
  status: FrontendExecutionStatus;
  progress: number;
  currentAgent?: string;
  step?: number;
  totalSteps?: number;
}

export interface LogEntry {
  id: string;
  level: string;
  message: string;
  agentId?: string;
  agentType?: string;
  executionId?: string;
  timestamp: string;
  details?: Record<string, unknown>;
}

export interface AgentStatus {
  agentId: string;
  agentType: string;
  status: string;
  message?: string;
  timestamp: string;
}

export interface Artifact {
  id: string;
  type: string;
  name: string;
  content?: string;
  metadata?: Record<string, unknown>;
}

interface RealtimeState {
  // Connection status
  status: WebSocketStatus;
  sessionId: string | null;
  reconnectAttempt: number;
  lastConnected: string | null;
  
  // Real-time data
  logs: LogEntry[];
  executionUpdates: Map<string, ExecutionUpdate>;
  agentStatuses: Map<string, AgentStatus>;
  artifacts: Artifact[];
  
  // Subscribed events
  subscribedEvents: string[];
  
  // Actions
  setStatus: (status: WebSocketStatus) => void;
  setSessionId: (sessionId: string | null) => void;
  setReconnectAttempt: (attempt: number) => void;
  setLastConnected: (timestamp: string | null) => void;
  
  addLog: (log: LogEntry) => void;
  clearLogs: () => void;
  
  updateExecution: (update: ExecutionUpdate) => void;
  clearExecution: (executionId: string) => void;
  
  updateAgentStatus: (status: AgentStatus) => void;
  clearAgentStatus: (agentId: string) => void;
  
  addArtifact: (artifact: Artifact) => void;
  updateArtifact: (id: string, updates: Partial<Artifact>) => void;
  clearArtifact: (id: string) => void;
  
  setSubscribedEvents: (events: string[]) => void;
  
  handleMessage: (message: WebSocketMessage) => void;
  reset: () => void;
}

const initialState = {
  status: "disconnected" as WebSocketStatus,
  sessionId: null,
  reconnectAttempt: 0,
  lastConnected: null,
  logs: [],
  executionUpdates: new Map(),
  agentStatuses: new Map(),
  artifacts: [],
  subscribedEvents: [],
};

export const useRealtimeStore = create<RealtimeState>((set, get) => ({
  ...initialState,

  setStatus: (status) => set({ status }),
  setSessionId: (sessionId) => set({ sessionId }),
  setReconnectAttempt: (reconnectAttempt) => set({ reconnectAttempt }),
  setLastConnected: (lastConnected) => set({ lastConnected: lastConnected ?? null }),

  addLog: (log) => set((state) => ({
    logs: [...state.logs.slice(-999), log], // Keep last 1000 logs
  })),

  clearLogs: () => set({ logs: [] }),

  updateExecution: (update) => set((state) => {
    const newMap = new Map(state.executionUpdates);
    newMap.set(update.executionId, update);
    return { executionUpdates: newMap };
  }),

  clearExecution: (executionId) => set((state) => {
    const newMap = new Map(state.executionUpdates);
    newMap.delete(executionId);
    return { executionUpdates: newMap };
  }),

  updateAgentStatus: (status) => set((state) => {
    const newMap = new Map(state.agentStatuses);
    newMap.set(status.agentId, status);
    return { agentStatuses: newMap };
  }),

  clearAgentStatus: (agentId) => set((state) => {
    const newMap = new Map(state.agentStatuses);
    newMap.delete(agentId);
    return { agentStatuses: newMap };
  }),

  addArtifact: (artifact) => set((state) => ({
    artifacts: [...state.artifacts, artifact],
  })),

  updateArtifact: (id, updates) => set((state) => ({
    artifacts: state.artifacts.map((a) =>
      a.id === id ? { ...a, ...updates } : a
    ),
  })),

  clearArtifact: (id) => set((state) => ({
    artifacts: state.artifacts.filter((a) => a.id !== id),
  })),

  setSubscribedEvents: (events) => set({ subscribedEvents: events }),

  handleMessage: (message) => {
    const state = get();
    
    switch (message.type) {
      case "log_entry":
      case "LOG_ENTRY":
        if (message.data && typeof message.data === "object") {
          const data = message.data as Record<string, unknown>;
          state.addLog({
            id: crypto.randomUUID(),
            level: (data.level as string) || "INFO",
            message: (data.message as string) || "",
            agentId: data.agent_id as string | undefined,
            agentType: data.agent_type as string | undefined,
            executionId: data.execution_id as string | undefined,
            timestamp: (message.timestamp as string) || new Date().toISOString(),
            details: data.details as Record<string, unknown> | undefined,
          });
        }
        break;

      case "execution_update":
      case "EXECUTION_PROGRESS":
      case "EXECUTION_STARTED":
      case "EXECUTION_COMPLETED":
      case "EXECUTION_ERROR":
        if (message.data && typeof message.data === "object") {
          const data = message.data as Record<string, unknown>;
          const executionId = (data.execution_id || data.executionId) as string;
          if (executionId) {
            const rawState = (data.state as string) || "";
            state.updateExecution({
              executionId,
              state: rawState,
              status: mapExecutionStateToStatus(rawState),
              progress: (data.progress as number) || 0,
              currentAgent: data.current_agent as string | undefined,
              step: data.step as number | undefined,
              totalSteps: data.total_steps as number | undefined,
            });
          }
        }
        break;

      case "agent_status_changed":
      case "AGENT_STATUS_CHANGED":
      case "AGENT_ACTIVATED":
      case "AGENT_DEACTIVATED":
      case "AGENT_COMPLETED":
      case "AGENT_ERROR":
        if (message.agent_id || message.agentType) {
          const data = message.data as Record<string, unknown> | undefined;
          const agentId = (message.agent_id || (data?.agent_id as string | undefined)) as string;
          const agentType = (message.agentType || (data?.agent_type as string | undefined)) as string;
          const statusValue = (data?.status as string) || (message.event as string) || message.type;
          state.updateAgentStatus({
            agentId: agentId || "unknown",
            agentType: agentType || "unknown",
            status: statusValue,
            message: data?.message as string | undefined,
            timestamp: (message.timestamp as string) || new Date().toISOString(),
          });
        }
        break;

      case "artifact":
      case "artifact_created":
      case "ARTIFACT_CREATED":
      case "artifact_updated":
      case "ARTIFACT_UPDATED":
        {
          const data = message.data as Record<string, unknown> | undefined;
          if (message.artifact_id || data?.id) {
            const artifactId = (message.artifact_id || (data?.id as string | undefined)) as string;
            state.updateArtifact(artifactId, {
              id: artifactId,
              ...data,
            } as Partial<Artifact>);
          }
        }
        break;

      case "file_created":
      case "file_modified":
      case "file_deleted":
      case "FILE_CREATED":
      case "FILE_MODIFIED":
      case "FILE_DELETED":
        // File change events - handled by workspace store
        break;

      case "connected":
      case "CONNECTED":
        state.setStatus("connected");
        state.setLastConnected(new Date().toISOString());
        break;

      case "disconnected":
      case "DISCONNECTED":
        state.setStatus("disconnected");
        break;

      case "pong":
        // Heartbeat response
        break;

      default:
        // Handle unknown message types
        break;
    }
  },

  reset: () => set({
    ...initialState,
    executionUpdates: new Map(),
    agentStatuses: new Map(),
  }),
}));

// Helper hooks
export const useWebSocketStatus = () => {
  return useRealtimeStore((state) => ({
    status: state.status,
    sessionId: state.sessionId,
    reconnectAttempt: state.reconnectAttempt,
    lastConnected: state.lastConnected,
  }));
};

export const useRealtimeLogs = () => {
  return useRealtimeStore((state) => state.logs);
};

export const useExecutionUpdate = (executionId: string) => {
  return useRealtimeStore((state) => state.executionUpdates.get(executionId));
};

export const useAgentStatus = (agentId: string) => {
  return useRealtimeStore((state) => state.agentStatuses.get(agentId));
};

export const useRealtimeArtifacts = () => {
  return useRealtimeStore((state) => state.artifacts);
};
