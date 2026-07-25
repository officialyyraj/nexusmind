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

// Generate mock workflow data for demonstration
function generateMockWorkflow(): WorkflowExecution {
  const nodes: WorkflowNodeState[] = [
    {
      id: 'planner',
      name: 'Planner',
      type: 'planner',
      status: 'completed',
      position: { x: 250, y: 50 },
      assignedAgent: 'planner-agent-1',
      progress: 100,
      retryCount: 0,
      maxRetries: 3,
      startedAt: new Date(Date.now() - 60000).toISOString(),
      completedAt: new Date(Date.now() - 50000).toISOString(),
      duration: 10000,
      output: 'Task decomposed into 5 subtasks',
    },
    {
      id: 'researcher',
      name: 'Researcher',
      type: 'researcher',
      status: 'running',
      position: { x: 250, y: 150 },
      assignedAgent: 'researcher-agent-1',
      currentTask: 'Researching implementation patterns',
      progress: 65,
      retryCount: 0,
      maxRetries: 3,
      startedAt: new Date(Date.now() - 40000).toISOString(),
      recentActions: [
        {
          id: '1',
          type: 'memory',
          description: 'Accessed project requirements',
          timestamp: new Date(Date.now() - 30000).toISOString(),
          success: true,
        },
        {
          id: '2',
          type: 'tool',
          description: 'Used web search tool',
          timestamp: new Date(Date.now() - 25000).toISOString(),
          duration: 5000,
          success: true,
        },
      ],
    },
    {
      id: 'backend',
      name: 'Backend',
      type: 'coder',
      status: 'waiting',
      position: { x: 250, y: 250 },
      progress: 0,
      retryCount: 0,
      maxRetries: 3,
    },
    {
      id: 'frontend',
      name: 'Frontend',
      type: 'coder',
      status: 'waiting',
      position: { x: 250, y: 350 },
      progress: 0,
      retryCount: 0,
      maxRetries: 3,
    },
    {
      id: 'reviewer',
      name: 'Reviewer',
      type: 'reviewer',
      status: 'waiting',
      position: { x: 250, y: 450 },
      progress: 0,
      retryCount: 0,
      maxRetries: 3,
    },
    {
      id: 'tester',
      name: 'Tester',
      type: 'tester',
      status: 'waiting',
      position: { x: 250, y: 550 },
      progress: 0,
      retryCount: 0,
      maxRetries: 3,
    },
    {
      id: 'documentation',
      name: 'Documentation',
      type: 'documentation',
      status: 'waiting',
      position: { x: 250, y: 650 },
      progress: 0,
      retryCount: 0,
      maxRetries: 3,
    },
  ];

  const edges: WorkflowEdgeState[] = [
    { id: 'e1', source: 'planner', target: 'researcher', status: 'completed' },
    { id: 'e2', source: 'researcher', target: 'backend', status: 'pending' },
    { id: 'e3', source: 'researcher', target: 'frontend', status: 'pending' },
    { id: 'e4', source: 'backend', target: 'reviewer', status: 'pending' },
    { id: 'e5', source: 'frontend', target: 'reviewer', status: 'pending' },
    { id: 'e6', source: 'reviewer', target: 'tester', status: 'pending' },
    { id: 'e7', source: 'tester', target: 'documentation', status: 'pending' },
  ];

  return {
    id: 'workflow-1',
    name: 'Feature Development Workflow',
    status: 'running',
    startedAt: new Date(Date.now() - 60000).toISOString(),
    progress: 25,
    currentNode: 'researcher',
    nodes,
    edges,
    projectId: 'project-1',
    sessionId: 'session-1',
  };
}

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
}

export const useWorkflowStore = create<WorkflowState>()(
  persist(
    (set, get) => ({
      currentWorkflow: generateMockWorkflow(),
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
      }),
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
