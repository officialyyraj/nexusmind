"use client";

import { useMemo } from "react";
import { useWorkflowStore, useSelectedAgent, useSelectedNode } from "@/lib/stores/workflow";
import { cn } from "@/lib/utils";
import {
  X,
  User,
  Brain,
  Clock,
  Cpu,
  HardDrive,
  Zap,
  CheckCircle,
  XCircle,
  Loader2,
  Search,
  FileCode,
  MessageSquare,
  GitBranch,
  ChevronDown,
  ChevronRight,
  Copy,
  Download,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { NodeStatus, Action } from "@/types";

const statusIcons: Record<NodeStatus, React.ElementType> = {
  idle: Clock,
  running: Loader2,
  waiting: Clock,
  completed: CheckCircle,
  failed: XCircle,
  retrying: Loader2,
};

const actionIcons: Record<string, React.ElementType> = {
  tool: Zap,
  memory: Search,
  file: FileCode,
  message: MessageSquare,
  decision: GitBranch,
};

const statusColors: Record<NodeStatus, string> = {
  idle: "text-gray-400",
  running: "text-blue-400",
  waiting: "text-yellow-400",
  completed: "text-green-400",
  failed: "text-red-400",
  retrying: "text-orange-400",
};

interface AgentInspectorPanelProps {
  className?: string;
  onClose?: () => void;
}

export function AgentInspectorPanel({ className, onClose }: AgentInspectorPanelProps) {
  const { selectedAgent, selectAgent, selectNode } = useWorkflowStore();
  const selectedNode = useSelectedNode();

  const agent = selectedAgent;

  if (!agent) {
    return (
      <div className={cn("flex items-center justify-center h-full bg-gray-900 border-l border-gray-700", className)}>
        <div className="text-center text-gray-500 p-4">
          <User className="h-12 w-12 mx-auto mb-3 text-gray-600" />
          <p className="text-sm">Select a node to inspect</p>
        </div>
      </div>
    );
  }

  const StatusIcon = statusIcons[agent.status] || Clock;

  return (
    <div className={cn("flex flex-col h-full bg-gray-900 border-l border-gray-700", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-600 rounded-lg">
            <StatusIcon className={cn("h-5 w-5 text-white", agent.status === "running" && "animate-spin")} />
          </div>
          <div>
            <h3 className="text-sm font-medium text-white">{agent.name}</h3>
            <Badge
              variant="secondary"
              className={cn("text-xs capitalize mt-0.5", statusColors[agent.status])}
            >
              {agent.status}
            </Badge>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => {
            selectAgent(null);
            selectNode(null);
            onClose?.();
          }}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      <Tabs defaultValue="overview" className="flex-1 flex flex-col overflow-hidden">
        <TabsList className="w-full justify-start rounded-none border-b border-gray-700 bg-gray-900 h-10">
          <TabsTrigger value="overview" className="text-xs data-[state=active]:bg-gray-800">Overview</TabsTrigger>
          <TabsTrigger value="actions" className="text-xs data-[state=active]:bg-gray-800">Actions</TabsTrigger>
          <TabsTrigger value="output" className="text-xs data-[state=active]:bg-gray-800">Output</TabsTrigger>
          <TabsTrigger value="metrics" className="text-xs data-[state=active]:bg-gray-800">Metrics</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="space-y-3">
            <h4 className="text-xs font-medium text-gray-400 uppercase">Agent Info</h4>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-gray-500 text-xs">Type</p>
                <p className="text-white capitalize">{agent.type}</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs">Model</p>
                <p className="text-white">{agent.model}</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs">Status</p>
                <p className={cn("capitalize", statusColors[agent.status])}>{agent.status}</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs">Duration</p>
                <p className="text-white">{formatDuration(agent.duration)}</p>
              </div>
            </div>
          </div>

          {agent.currentTask && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium text-gray-400 uppercase">Current Task</h4>
              <p className="text-sm text-white bg-gray-800 rounded-lg p-3">{agent.currentTask}</p>
            </div>
          )}

          {agent.currentTool && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium text-gray-400 uppercase">Current Tool</h4>
              <div className="flex items-center gap-2 bg-gray-800 rounded-lg p-3">
                <Zap className="h-4 w-4 text-blue-400" />
                <span className="text-sm text-white">{agent.currentTool}</span>
              </div>
            </div>
          )}

          {agent.tokenUsage && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium text-gray-400 uppercase">Token Usage</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Prompt</span>
                  <span className="text-white">{agent.tokenUsage.promptTokens.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Completion</span>
                  <span className="text-white">{agent.tokenUsage.completionTokens.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Total</span>
                  <span className="text-white font-medium">{agent.tokenUsage.totalTokens.toLocaleString()}</span>
                </div>
                <Progress
                  value={(agent.tokenUsage.completionTokens / agent.tokenUsage.totalTokens) * 100}
                  className="h-2"
                />
              </div>
            </div>
          )}

          {agent.memoryLookups && agent.memoryLookups.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium text-gray-400 uppercase">
                Memory Lookups ({agent.memoryLookups.length})
              </h4>
              <div className="space-y-2">
                {agent.memoryLookups.slice(0, 5).map((lookup) => (
                  <div key={lookup.id} className="bg-gray-800 rounded-lg p-2 text-sm">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline" className="text-xs capitalize">{lookup.type}</Badge>
                      <span className="text-xs text-gray-500">{lookup.accessCount} accesses</span>
                    </div>
                    <p className="text-gray-300 text-xs truncate">{lookup.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {agent.errors.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium text-red-400 uppercase">Errors</h4>
              <div className="space-y-2">
                {agent.errors.map((error, i) => (
                  <div key={i} className="bg-red-900/30 border border-red-800 rounded-lg p-2 text-sm text-red-300">
                    {error}
                  </div>
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        {/* Actions Tab */}
        <TabsContent value="actions" className="flex-1 overflow-y-auto p-4">
          {agent.recentActions.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <p className="text-sm">No actions yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {agent.recentActions.map((action) => (
                <ActionItem key={action.id} action={action} />
              ))}
            </div>
          )}
        </TabsContent>

        {/* Output Tab */}
        <TabsContent value="output" className="flex-1 overflow-hidden flex flex-col">
          {agent.output ? (
            <>
              <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700">
                <span className="text-xs text-gray-400">Output</span>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => navigator.clipboard.writeText(agent.output || "")}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => {
                      const blob = new Blob([agent.output || ""], { type: "text/plain" });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = `${agent.name}-output.txt`;
                      a.click();
                    }}
                  >
                    <Download className="h-3 w-3" />
                  </Button>
                </div>
              </div>
              <ScrollArea className="flex-1">
                <pre className="p-4 text-xs text-gray-300 whitespace-pre-wrap font-mono">
                  {agent.output}
                </pre>
              </ScrollArea>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              <p className="text-sm">No output available</p>
            </div>
          )}
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics" className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-800 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <Cpu className="h-4 w-4 text-blue-400" />
                <span className="text-xs text-gray-400">CPU Usage</span>
              </div>
              <p className="text-xl font-bold text-white">{agent.metrics.cpuUsage}%</p>
              <Progress value={agent.metrics.cpuUsage} className="h-1 mt-2" />
            </div>
            <div className="bg-gray-800 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <HardDrive className="h-4 w-4 text-green-400" />
                <span className="text-xs text-gray-400">Memory</span>
              </div>
              <p className="text-xl font-bold text-white">{agent.metrics.memoryUsage}MB</p>
              <Progress value={(agent.metrics.memoryUsage / 512) * 100} className="h-1 mt-2" />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-800 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="h-4 w-4 text-green-400" />
                <span className="text-xs text-gray-400">Tasks Completed</span>
              </div>
              <p className="text-xl font-bold text-green-400">{agent.metrics.tasksCompleted}</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <XCircle className="h-4 w-4 text-red-400" />
                <span className="text-xs text-gray-400">Tasks Failed</span>
              </div>
              <p className="text-xl font-bold text-red-400">{agent.metrics.tasksFailed}</p>
            </div>
          </div>

          {agent.metrics.tokensPerSecond && (
            <div className="bg-gray-800 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="h-4 w-4 text-yellow-400" />
                <span className="text-xs text-gray-400">Tokens/Second</span>
              </div>
              <p className="text-xl font-bold text-white">{agent.metrics.tokensPerSecond.toFixed(1)}</p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ActionItem({ action }: { action: Action }) {
  const [expanded, setExpanded] = useState(false);
  const Icon = actionIcons[action.type] || Zap;

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div
        className="flex items-center gap-3 p-3 cursor-pointer hover:bg-gray-750"
        onClick={() => setExpanded(!expanded)}
      >
        <div className={cn("p-1.5 rounded", action.success ? "bg-green-600/20" : "bg-red-600/20")}>
          <Icon className={cn("h-3 w-3", action.success ? "text-green-400" : "text-red-400")} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-white truncate">{action.description}</p>
          <p className="text-xs text-gray-500">
            {formatTime(action.timestamp)}
            {action.duration && ` • ${action.duration}ms`}
          </p>
        </div>
        {expanded ? (
          <ChevronDown className="h-4 w-4 text-gray-500" />
        ) : (
          <ChevronRight className="h-4 w-4 text-gray-500" />
        )}
      </div>
      {expanded && action.details && (
        <div className="px-3 pb-3">
          <pre className="text-xs text-gray-400 bg-gray-900 rounded p-2 overflow-x-auto">
            {JSON.stringify(action.details, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

// Helper functions
function formatDuration(ms?: number): string {
  if (!ms) return "-";
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) return `${hours}h ${minutes % 60}m`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

// Import useState for ActionItem
import { useState } from "react";
