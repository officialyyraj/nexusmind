import { describe, it, expect, beforeEach } from "vitest";
import { useWorkflowStore } from "../workflow";
import type { WorkflowNodeState, WorkflowExecution } from "@/types";

// Reset store before each test
beforeEach(() => {
  // Reset the store state
  useWorkflowStore.setState({
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
  });
});

describe("WorkflowStore", () => {
  describe("Workflow State", () => {
    it("should set current workflow", () => {
      const newWorkflow: WorkflowExecution = {
        id: "workflow-2",
        name: "New Workflow",
        status: "pending",
        startedAt: new Date().toISOString(),
        progress: 0,
        nodes: [],
        edges: [],
      };

      useWorkflowStore.getState().setCurrentWorkflow(newWorkflow);
      
      const state = useWorkflowStore.getState();
      expect(state.currentWorkflow?.id).toBe("workflow-2");
      expect(state.currentWorkflow?.name).toBe("New Workflow");
    });
  });

  describe("Node Management", () => {
    it("should update a node", () => {
      const testWorkflow: WorkflowExecution = {
        id: "test-workflow",
        name: "Test Workflow",
        status: "running",
        startedAt: new Date().toISOString(),
        progress: 0,
        nodes: [
          {
            id: "node-1",
            name: "Test Node",
            type: "planner",
            status: "idle",
            position: { x: 0, y: 0 },
            progress: 0,
            retryCount: 0,
            maxRetries: 3,
          },
        ],
        edges: [],
      };

      useWorkflowStore.getState().setCurrentWorkflow(testWorkflow);
      
      useWorkflowStore.getState().updateNode("node-1", {
        status: "running",
        progress: 50,
      });
      
      const updatedState = useWorkflowStore.getState();
      const updatedNode = updatedState.currentWorkflow?.nodes.find(n => n.id === "node-1");
      
      expect(updatedNode?.status).toBe("running");
      expect(updatedNode?.progress).toBe(50);
    });

    it("should select a node", () => {
      const testWorkflow: WorkflowExecution = {
        id: "test-workflow",
        name: "Test Workflow",
        status: "running",
        startedAt: new Date().toISOString(),
        progress: 0,
        nodes: [
          {
            id: "node-1",
            name: "Test Node",
            type: "planner",
            status: "idle",
            position: { x: 0, y: 0 },
            progress: 0,
            retryCount: 0,
            maxRetries: 3,
          },
        ],
        edges: [],
      };

      useWorkflowStore.getState().setCurrentWorkflow(testWorkflow);
      useWorkflowStore.getState().selectNode("node-1");
      
      const newState = useWorkflowStore.getState();
      expect(newState.selectedNodeId).toBe("node-1");
    });

    it("should clear node selection", () => {
      const testWorkflow: WorkflowExecution = {
        id: "test-workflow",
        name: "Test Workflow",
        status: "running",
        startedAt: new Date().toISOString(),
        progress: 0,
        nodes: [
          {
            id: "node-1",
            name: "Test Node",
            type: "planner",
            status: "idle",
            position: { x: 0, y: 0 },
            progress: 0,
            retryCount: 0,
            maxRetries: 3,
          },
        ],
        edges: [],
      };

      useWorkflowStore.getState().setCurrentWorkflow(testWorkflow);
      useWorkflowStore.getState().selectNode("node-1");
      useWorkflowStore.getState().selectNode(null);
      
      const newState = useWorkflowStore.getState();
      expect(newState.selectedNodeId).toBeNull();
    });
  });

  describe("Edge Management", () => {
    it("should update an edge", () => {
      const testWorkflow: WorkflowExecution = {
        id: "test-workflow",
        name: "Test Workflow",
        status: "running",
        startedAt: new Date().toISOString(),
        progress: 0,
        nodes: [
          {
            id: "node-1",
            name: "Test Node",
            type: "planner",
            status: "idle",
            position: { x: 0, y: 0 },
            progress: 0,
            retryCount: 0,
            maxRetries: 3,
          },
        ],
        edges: [
          {
            id: "edge-1",
            source: "node-1",
            target: "node-2",
            status: "pending",
          },
        ],
      };

      useWorkflowStore.getState().setCurrentWorkflow(testWorkflow);
      useWorkflowStore.getState().updateEdge("edge-1", {
        status: "completed",
      });
      
      const updatedState = useWorkflowStore.getState();
      const updatedEdge = updatedState.currentWorkflow?.edges.find(e => e.id === "edge-1");
      
      expect(updatedEdge?.status).toBe("completed");
    });
  });

  describe("Filter Management", () => {
    it("should set filter", () => {
      useWorkflowStore.getState().setFilter({
        statuses: ["running", "completed"],
        agentIds: ["agent-1"],
      });
      
      const state = useWorkflowStore.getState();
      expect(state.filter.statuses).toContain("running");
      expect(state.filter.statuses).toContain("completed");
      expect(state.filter.agentIds).toContain("agent-1");
    });
  });

  describe("Live Mode", () => {
    it("should toggle live mode", () => {
      const initialState = useWorkflowStore.getState().isLive;
      
      useWorkflowStore.getState().toggleLive();
      expect(useWorkflowStore.getState().isLive).toBe(!initialState);
      
      useWorkflowStore.getState().toggleLive();
      expect(useWorkflowStore.getState().isLive).toBe(initialState);
    });

    it("should set playback speed", () => {
      useWorkflowStore.getState().setPlaybackSpeed(2);
      expect(useWorkflowStore.getState().playbackSpeed).toBe(2);
      
      useWorkflowStore.getState().setPlaybackSpeed(0.5);
      expect(useWorkflowStore.getState().playbackSpeed).toBe(0.5);
    });
  });

  describe("Log Management", () => {
    it("should add a log", () => {
      useWorkflowStore.getState().addLog({
        logId: "log-1",
        nodeId: "node-1",
        nodeName: "Test Node",
        level: "info",
        message: "Test log message",
        timestamp: new Date().toISOString(),
      });
      
      const state = useWorkflowStore.getState();
      expect(state.logs).toHaveLength(1);
      expect(state.logs[0].message).toBe("Test log message");
    });

    it("should select a log", () => {
      useWorkflowStore.getState().addLog({
        logId: "log-1",
        nodeId: "node-1",
        nodeName: "Test Node",
        level: "info",
        message: "Test log message",
        timestamp: new Date().toISOString(),
      });
      
      useWorkflowStore.getState().selectLog("log-1");
      
      const state = useWorkflowStore.getState();
      expect(state.selectedLogId).toBe("log-1");
      expect(state.relatedLogs).toHaveLength(1);
    });
  });

  describe("Timeline", () => {
    it("should add a timeline event", () => {
      useWorkflowStore.getState().addTimelineEvent({
        id: "event-1",
        phase: "planning",
        nodeId: "planner",
        nodeName: "Planner",
        status: "completed",
        timestamp: new Date().toISOString(),
        duration: 5000,
      });
      
      const state = useWorkflowStore.getState();
      expect(state.timeline).toHaveLength(1);
      expect(state.timeline[0].phase).toBe("planning");
    });
  });

  describe("Reset", () => {
    it("should reset all state", () => {
      // Add some data
      useWorkflowStore.getState().setCurrentWorkflow({
        id: "workflow-2",
        name: "Test",
        status: "running",
        startedAt: new Date().toISOString(),
        progress: 50,
        nodes: [],
        edges: [],
      });
      useWorkflowStore.getState().addLog({
        logId: "log-1",
        nodeId: "node-1",
        nodeName: "Test",
        level: "info",
        message: "Test",
        timestamp: new Date().toISOString(),
      });
      useWorkflowStore.getState().toggleLive();
      
      // Reset
      useWorkflowStore.getState().reset();
      
      const state = useWorkflowStore.getState();
      expect(state.currentWorkflow).toBeNull();
      expect(state.logs).toHaveLength(0);
      expect(state.isLive).toBe(true); // Default value
    });
  });
});

describe("WorkflowNodeState", () => {
  it("should create a valid node state", () => {
    const node: WorkflowNodeState = {
      id: "node-1",
      name: "Test Node",
      type: "planner",
      status: "running",
      position: { x: 100, y: 200 },
      progress: 50,
      retryCount: 0,
      maxRetries: 3,
    };
    
    expect(node.id).toBe("node-1");
    expect(node.status).toBe("running");
    expect(node.progress).toBe(50);
  });
});
