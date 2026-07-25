"use client";

import { useCallback, useMemo, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  Connection,
  useNodesState,
  useEdgesState,
  addEdge,
  NodeProps,
  Handle,
  Position,
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useWorkflowStore } from "@/lib/stores/workflow";
import type { WorkflowNodeState, WorkflowEdgeState, NodeStatus } from "@/types";
import { cn } from "@/lib/utils";
import {
  Brain,
  Search,
  Code,
  Eye,
  TestTube,
  FileText,
  CheckCircle,
  XCircle,
  Loader2,
  Clock,
  RefreshCw,
  Play,
  Pause,
  User,
} from "lucide-react";

const nodeIcons: Record<string, React.ElementType> = {
  planner: Brain,
  researcher: Search,
  coder: Code,
  backend: Code,
  frontend: Code,
  reviewer: Eye,
  tester: TestTube,
  documentation: FileText,
  manager: User,
};

const statusColors: Record<NodeStatus, string> = {
  idle: "bg-gray-500",
  running: "bg-blue-500 animate-pulse",
  waiting: "bg-yellow-500",
  completed: "bg-green-500",
  failed: "bg-red-500",
  retrying: "bg-orange-500 animate-pulse",
};

const statusTextColors: Record<NodeStatus, string> = {
  idle: "text-gray-400",
  running: "text-blue-400",
  waiting: "text-yellow-400",
  completed: "text-green-400",
  failed: "text-red-400",
  retrying: "text-orange-400",
};

interface WorkflowNodeData {
  node: WorkflowNodeState;
  onSelect: (nodeId: string) => void;
  selected: boolean;
}

function WorkflowNodeComponent({ data, selected }: NodeProps<WorkflowNodeData>) {
  const { node, onSelect, selected: isSelected } = data;
  const Icon = nodeIcons[node.type] || Code;
  
  return (
    <div
      className={cn(
        "relative px-4 py-3 rounded-lg border-2 transition-all cursor-pointer min-w-[140px]",
        isSelected
          ? "border-blue-500 bg-blue-950 shadow-lg shadow-blue-500/20"
          : "border-gray-600 bg-gray-800 hover:border-gray-500",
        node.status === "running" && "ring-2 ring-blue-500 ring-offset-2 ring-offset-gray-900"
      )}
      onClick={() => onSelect(node.id)}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-500" />
      
      <div className="flex items-center gap-3">
        <div className={cn("p-2 rounded-lg", statusColors[node.status])}>
          <Icon className="h-4 w-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">{node.name}</p>
          <p className={cn("text-xs capitalize", statusTextColors[node.status])}>
            {node.status}
          </p>
        </div>
      </div>
      
      {node.status === "running" && (
        <div className="mt-2">
          <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${node.progress}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-1">{node.progress}%</p>
        </div>
      )}
      
      {node.currentTask && (
        <p className="text-xs text-gray-400 mt-2 truncate">{node.currentTask}</p>
      )}
      
      {node.retryCount > 0 && (
        <div className="absolute -top-1 -right-1 flex items-center gap-1 px-1.5 py-0.5 bg-orange-600 rounded text-xs text-white">
          <RefreshCw className="h-3 w-3" />
          {node.retryCount}
        </div>
      )}
      
      <Handle type="source" position={Position.Bottom} className="!bg-gray-500" />
    </div>
  );
}

function WorkflowEdgeComponent({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
}: {
  id: string;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  sourcePosition: Position;
  targetPosition: Position;
  data?: { status: string };
  selected?: boolean;
}) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const status = data?.status || "pending";
  
  const strokeColor =
    status === "completed" ? "#22c55e" :
    status === "active" ? "#3b82f6" :
    status === "skipped" ? "#6b7280" :
    "#374151";

  const strokeWidth = selected ? 3 : 2;

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: strokeColor,
          strokeWidth,
          transition: "stroke 0.3s, strokeWidth 0.3s",
        }}
      />
      {status === "active" && (
        <EdgeLabelRenderer>
          <div
            className="absolute pointer-events-all"
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            }}
          >
            <div className="px-2 py-1 bg-blue-600 text-white text-xs rounded-full animate-pulse">
              Active
            </div>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

const nodeTypes = {
  workflowNode: WorkflowNodeComponent,
};

const edgeTypes = {
  workflowEdge: WorkflowEdgeComponent,
};

interface WorkflowGraphProps {
  className?: string;
  onNodeSelect?: (nodeId: string) => void;
}

export function WorkflowGraph({ className, onNodeSelect }: WorkflowGraphProps) {
  const {
    currentWorkflow,
    selectedNodeId,
    selectNode,
    isLive,
  } = useWorkflowStore();

  const [nodes, setNodes, onNodesChange] = useNodesState<NodeProps<WorkflowNodeData>[]>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Transform workflow data to React Flow format
  useMemo(() => {
    if (!currentWorkflow) {
      setNodes([]);
      setEdges([]);
      return;
    }

    const flowNodes: Node<WorkflowNodeData>[] = currentWorkflow.nodes.map((node) => ({
      id: node.id,
      type: "workflowNode",
      position: node.position,
      data: {
        node,
        onSelect: (nodeId: string) => {
          selectNode(nodeId);
          onNodeSelect?.(nodeId);
        },
        selected: node.id === selectedNodeId,
      },
    }));

    const flowEdges: Edge[] = currentWorkflow.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: "workflowEdge",
      data: { status: edge.status },
      animated: edge.status === "active",
    }));

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [currentWorkflow, selectedNodeId, setNodes, setEdges, selectNode, onNodeSelect]);

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => addEdge(connection, eds));
    },
    [setEdges]
  );

  if (!currentWorkflow) {
    return (
      <div className={cn("flex items-center justify-center h-full bg-gray-900", className)}>
        <div className="text-center text-gray-400">
          <Play className="h-12 w-12 mx-auto mb-4 text-gray-600" />
          <p className="text-lg mb-2">No Workflow Running</p>
          <p className="text-sm">Start a workflow to see it visualized here</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("h-full bg-gray-900", className)}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        attributionPosition="bottom-left"
        className="bg-gray-900"
      >
        <Background color="#374151" gap={20} />
        <Controls className="bg-gray-800 border border-gray-700" />
        <MiniMap
          className="bg-gray-800 border border-gray-700"
          nodeColor={(node) => {
            const status = (node.data as WorkflowNodeData)?.node?.status;
            return statusColors[status as NodeStatus] || "#6b7280";
          }}
        />
        
        {/* Live indicator */}
        <div className="absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-full">
          {isLive ? (
            <>
              <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-xs text-green-400">Live</span>
            </>
          ) : (
            <>
              <div className="h-2 w-2 rounded-full bg-yellow-500" />
              <span className="text-xs text-yellow-400">Paused</span>
            </>
          )}
        </div>
        
        {/* Workflow info */}
        <div className="absolute top-4 left-4 px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg">
          <p className="text-sm font-medium text-white">{currentWorkflow.name}</p>
          <p className="text-xs text-gray-400">
            {currentWorkflow.progress}% complete
          </p>
        </div>
      </ReactFlow>
    </div>
  );
}
