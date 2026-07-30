import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  WorkflowExecution,
  WorkflowNodeState,
  WorkflowEdgeState,
  AgentInspector,
  TimelineEvent,
  LogCorrelation,
  WorkflowFilter,
  NodeStatus,
} from '@/types';
import { api } from '@/lib/api/client';
import { useRealtimeStore, mapExecutionStateToStatus } from '@/lib/stores/realtime';

interface WorkflowState {
  // Current workflow
  currentWorkflow: WorkflowExecution | null;
  workflows: WorkflowExecution[];
  selectedNodeId: string | null;
  selectedAgent: AgentInspector | null;
  timeline: TimelineEvent[];
  logs: LogCorrelation[];
  filter: WorkflowFilter;
  isLive: boolean;
  playbackSpeed: number;
  selectedLogId: string | null;
  relatedLogs: LogCorrelation[];
  
  // Loading states
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setCurrentWorkflow: (workflow: WorkflowExecution | null) => void;
  updateNode: (nodeId: string, updates: Partial<WorkflowNodeState>) => void;
  updateEdge: (edgeId: string, updates: Partial<WorkflowEdgeState>) => void;
  selectNode: (nodeId: string | null) => void;
  selectAgent: (agent: AgentInspector | null) => void;
  setFilter: (filter: WorkflowFilter) => void;
  toggleLive: () => void;
  setPlaybackSpeed: (speed: number) => void;
  selectLog: (logId: string | null) => void;
  addTimelineEvent: (event: TimelineEvent) => void;
  addLog: (log: LogCorrelation) => void;
  replayWorkflow: () => void;
  exportWorkflow: (format: 'json' | 'png' | 'svg') => void;
  reset: () => void;
  syncFromRealtime: () => void;
  
  // Async actions
  loadWorkflow: (executionId: string) => Promise<void>;
  loadExecutions: (sessionId?: string) => Promise<void>;
}

export const useWorkflowStore = create<WorkflowState>()(
  persist(
    (set, get) => ({
      currentWorkflow: null,
      workflows: [],
      selectedNodeId: null,
      selectedAgent: null,
      timeline: [],
      logs: [],
      filter: {},
      isLive: true,
      playbackSpeed: 1,
      selectedLogId: null,
      relatedLogs: [],
      isLoading: false,
      error: null,
      
      setCurrentWorkflow: (workflow) => set({ currentWorkflow: workflow }),
      
      updateNode: (nodeId, updates) => set((state) => {
        if (!state.currentWorkflow) return {};
        return {
          currentWorkflow: {
            ...state.currentWorkflow,
            nodes: state.currentWorkflow.nodes.map((node) =>
              node.id === nodeId ? { ...node, ...updates } : node
            ),
          },
        };
      }),
      
      updateEdge: (edgeId, updates) => set((state) => {
        if (!state.currentWorkflow) return {};
        return {
          currentWorkflow: {
            ...state.currentWorkflow,
            edges: state.currentWorkflow.edges.map((edge) =>
              edge.id === edgeId ? { ...edge, ...updates } : edge
            ),
          },
        };
      }),
      
      selectNode: (nodeId) => {
        set({ selectedNodeId: nodeId });
        
        if (nodeId) {
          const workflow = get().currentWorkflow;
          const node = workflow?.nodes.find((n) => n.id === nodeId);
          
          if (node?.assignedAgent) {
            // Create agent inspector data from node
            const agent: AgentInspector = {
              id: node.assignedAgent,
              name: node.name,
              type: node.type,
              model: 'gpt-4',
              status: node.status,
              currentTask: node.currentTask,
              currentTool: node.currentTool,
              memoryLookups: node.memoryLookups || [],
              tokenUsage: node.tokenUsage,
              duration: node.duration,
              recentActions: node.recentActions || [],
              output: node.output,
              errors: node.error ? [node.error] : [],
              metrics: {
                cpuUsage: 45,
                memoryUsage: 256,
                tasksCompleted: 3,
                tasksFailed: 0,
              },
            };
            set({ selectedAgent: agent });
            
            // Get related logs
            const logs = get().logs.filter((l) => l.nodeId === nodeId);
            set({ relatedLogs: logs });
          }
        } else {
          set({ selectedAgent: null, relatedLogs: [] });
        }
      },
      
      selectAgent: (agent) => set({ selectedAgent: agent }),
      
      setFilter: (filter) => set({ filter }),
      
      toggleLive: () => set((state) => ({ isLive: !state.isLive })),
      
      setPlaybackSpeed: (speed) => set({ playbackSpeed: speed }),
      
      selectLog: (logId) => {
        set({ selectedLogId: logId });
        if (logId) {
          const log = get().logs.find((l) => l.logId === logId);
          if (log) {
            const relatedLogs = get().logs.filter(
              (l) => l.nodeId === log.nodeId
            );
            set({ relatedLogs });
          }
        }
      },
      
      addTimelineEvent: (event) => set((state) => ({
        timeline: [...state.timeline, event],
      })),
      
      addLog: (log) => set((state) => ({
        logs: [...state.logs, log],
      })),
      
      replayWorkflow: () => {
        const workflow = get().currentWorkflow;
        if (!workflow) return;
        
        // Reset all nodes to initial state
        const resetWorkflow: WorkflowExecution = {
          ...workflow,
          status: 'running',
          startedAt: new Date().toISOString(),
          progress: 0,
          nodes: workflow.nodes.map((node) => ({
            ...node,
            status: 'idle' as NodeStatus,
            progress: 0,
            startedAt: undefined,
            completedAt: undefined,
            duration: undefined,
            output: undefined,
            error: undefined,
          })),
          edges: workflow.edges.map((edge) => ({
            ...edge,
            status: 'pending' as const,
          })),
        };
        
        set({ currentWorkflow: resetWorkflow, timeline: [] });
      },
      
      exportWorkflow: (format) => {
        const workflow = get().currentWorkflow;
        if (!workflow) return;
        
        if (format === 'json') {
          const data = JSON.stringify(workflow, null, 2);
          const blob = new Blob([data], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${workflow.name}.json`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }
        // PNG and SVG would require canvas rendering
      },
      
      reset: () => set({
        currentWorkflow: null,
        workflows: [],
        selectedNodeId: null,
        selectedAgent: null,
        timeline: [],
        logs: [],
        filter: {},
        isLive: true,
        playbackSpeed: 1,
        selectedLogId: null,
        relatedLogs: [],
        isLoading: false,
        error: null,
      }),
      
      // Sync from realtime store
      syncFromRealtime: () => {
        const state = get();
        const realtime = useRealtimeStore.getState();
        
        // Sync execution updates to workflow
        if (state.currentWorkflow) {
          const executionId = state.currentWorkflow.id;
          const update = realtime.executionUpdates.get(executionId);
          
          if (update) {
            // Update workflow status using the pre-mapped status from realtime store
            set({
              currentWorkflow: {
                ...state.currentWorkflow,
                status: update.status,  // Already mapped by realtime store
                progress: update.progress,
                currentNode: update.currentAgent,
              },
            });
            
            // Update nodes based on current agent
            if (update.currentAgent) {
              state.updateNode(update.currentAgent, {
                status: 'running',
              });
            }
            
            // Update completed nodes using the step field (now consistent with backend)
            if (update.step !== undefined) {
              const nodes = state.currentWorkflow.nodes;
              for (let i = 0; i < update.step && i < nodes.length; i++) {
                if (nodes[i].status !== 'completed') {
                  state.updateNode(nodes[i].id, {
                    status: 'completed',
                  });
                }
              }
            }
          }
        }
        
        // Sync logs from realtime
        const realtimeLogs = realtime.logs;
        if (realtimeLogs.length > state.logs.length) {
          const newLogs = realtimeLogs.slice(state.logs.length);
          for (const log of newLogs) {
            if (log.executionId === state.currentWorkflow?.id) {
              state.addLog({
                logId: log.id,
                nodeId: log.agentId || '',
                nodeName: log.agentType || '',
                level: log.level as 'debug' | 'info' | 'warn' | 'error',
                message: log.message,
                timestamp: log.timestamp,
              });
            }
          }
        }
      },
      
      // Async actions
      loadWorkflow: async (executionId: string) => {
        set({ isLoading: true, error: null });
        try {
          const execution = await api.executions.get(executionId) as Record<string, unknown>;
          const steps = await api.executions.getSteps(executionId) as unknown[];
          
          // Convert execution to workflow format
          const nodeTypes = ['planner', 'researcher', 'coder', 'reviewer', 'tester', 'documentation', 'manager', 'input', 'output', 'condition', 'tool'] as const;
          type NodeType = typeof nodeTypes[number];
          const nodes = (steps as Record<string, unknown>[]).map((step, index): WorkflowNodeState => {
            const agentType = (step.agent_type as string) || 'unknown';
            const validType: NodeType = nodeTypes.includes(agentType as NodeType) 
              ? agentType as NodeType
              : 'tool';
            const durationMs = step.duration_ms as number | undefined;
            return {
              id: step.id as string || `node-${index}`,
              name: agentType.charAt(0).toUpperCase() + agentType.slice(1),
              type: validType,
              status: (step.state as string || 'pending') as NodeStatus,
              position: { x: 250, y: 50 + index * 100 },
              progress: step.completed_at ? 100 : (step.started_at ? 50 : 0),
              retryCount: step.retry_count as number || 0,
              maxRetries: 3,
              startedAt: step.started_at as string | undefined,
              completedAt: step.completed_at as string | undefined,
              duration: durationMs ? durationMs / 1000 : undefined,
              output: step.result as string | undefined,
              error: step.error as string | undefined,
            };
          });
          
          const edges: WorkflowEdgeState[] = [];
          for (let i = 0; i < nodes.length - 1; i++) {
            edges.push({
              id: `e${i + 1}`,
              source: nodes[i].id,
              target: nodes[i + 1].id,
              status: nodes[i].status === 'completed' ? 'completed' : 'pending',
            });
          }
          
          const workflow: WorkflowExecution = {
            id: executionId,
            name: execution.task as string || 'Execution Workflow',
            status: mapExecutionStateToStatus(execution.state as string),
            startedAt: execution.started_at as string,
            progress: execution.progress_percent as number || 0,
            currentNode: nodes.find(n => n.status === 'running')?.id,
            nodes,
            edges,
            projectId: execution.project_id as string | undefined,
            sessionId: execution.session_id as string,
          };
          
          set({ currentWorkflow: workflow, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
      
      loadExecutions: async (sessionId?: string) => {
        set({ isLoading: true, error: null });
        try {
          const result = await api.executions.list({ sessionId, limit: 20 });
          set({ workflows: result.executions as unknown[] as WorkflowExecution[], isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
    }),
    {
      name: 'nexusmind-workflow',
      partialize: (state) => ({
        isLive: state.isLive,
        playbackSpeed: state.playbackSpeed,
      }),
    }
  )
);

// Helper hooks
export const useCurrentWorkflow = () => {
  return useWorkflowStore((state) => state.currentWorkflow);
};

export const useSelectedNode = () => {
  const workflow = useWorkflowStore((state) => state.currentWorkflow);
  const selectedId = useWorkflowStore((state) => state.selectedNodeId);
  return workflow?.nodes.find((n) => n.id === selectedId);
};

export const useSelectedAgent = () => {
  return useWorkflowStore((state) => state.selectedAgent);
};

export const useWorkflowStats = () => {
  const workflow = useWorkflowStore((state) => state.currentWorkflow);
  if (!workflow) return { total: 0, completed: 0, running: 0, failed: 0, waiting: 0 };
  
  return {
    total: workflow.nodes.length,
    completed: workflow.nodes.filter((n) => n.status === 'completed').length,
    running: workflow.nodes.filter((n) => n.status === 'running').length,
    failed: workflow.nodes.filter((n) => n.status === 'failed').length,
    waiting: workflow.nodes.filter((n) => n.status === 'waiting' || n.status === 'idle').length,
  };
};
