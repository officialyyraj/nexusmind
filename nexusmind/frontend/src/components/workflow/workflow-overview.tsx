"use client";

import { useMemo } from "react";
import { useWorkflowStore, useWorkflowStats } from "@/lib/stores/workflow";
import { cn } from "@/lib/utils";
import {
  Play,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  AlertCircle,
  BarChart3,
  Users,
  Zap,
  Timer,
  TrendingUp,
  Activity,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { NodeStatus } from "@/types";

const statusIcons: Record<NodeStatus, React.ElementType> = {
  idle: Clock,
  running: Loader2,
  waiting: Clock,
  completed: CheckCircle,
  failed: XCircle,
  retrying: AlertCircle,
};

const statusColors: Record<NodeStatus, string> = {
  idle: "bg-gray-500",
  running: "bg-blue-500",
  waiting: "bg-yellow-500",
  completed: "bg-green-500",
  failed: "bg-red-500",
  retrying: "bg-orange-500",
};

interface WorkflowOverviewProps {
  className?: string;
}

export function WorkflowOverview({ className }: WorkflowOverviewProps) {
  const { currentWorkflow, isLive, toggleLive, exportWorkflow } = useWorkflowStore();
  const stats = useWorkflowStats();

  const duration = useMemo(() => {
    if (!currentWorkflow?.startedAt) return 0;
    const start = new Date(currentWorkflow.startedAt).getTime();
    const end = currentWorkflow.completedAt
      ? new Date(currentWorkflow.completedAt).getTime()
      : Date.now();
    return end - start;
  }, [currentWorkflow]);

  if (!currentWorkflow) {
    return (
      <div className={cn("flex items-center justify-center h-full bg-gray-900", className)}>
        <div className="text-center text-gray-500">
          <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-600" />
          <p className="text-lg mb-2">No Active Workflow</p>
          <p className="text-sm">Start a workflow to see the overview</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("p-4 space-y-4 overflow-y-auto", className)}>
      {/* Status Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "w-3 h-3 rounded-full",
              currentWorkflow.status === "running" && "bg-green-500 animate-pulse",
              currentWorkflow.status === "completed" && "bg-green-500",
              currentWorkflow.status === "failed" && "bg-red-500",
              currentWorkflow.status === "pending" && "bg-yellow-500"
            )}
          />
          <div>
            <h2 className="text-lg font-medium text-white">{currentWorkflow.name}</h2>
            <p className="text-xs text-gray-400 capitalize">{currentWorkflow.status}</p>
          </div>
        </div>
        <Badge variant={isLive ? "default" : "secondary"} className="capitalize">
          {isLive ? "Live" : "Paused"}
        </Badge>
      </div>

      {/* Progress */}
      <Card className="bg-gray-800 border-gray-700">
        <CardContent className="pt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Overall Progress</span>
            <span className="text-lg font-bold text-white">{currentWorkflow.progress}%</span>
          </div>
          <Progress value={currentWorkflow.progress} className="h-2" />
          <div className="flex justify-between mt-2 text-xs text-gray-500">
            <span>Started {formatDuration(duration, true)} ago</span>
            {currentWorkflow.completedAt && (
              <span>Completed in {formatDuration(currentWorkflow.duration || 0)}</span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          icon={Activity}
          label="Running"
          value={stats.running}
          color="text-blue-400"
          bgColor="bg-blue-500/20"
        />
        <StatCard
          icon={CheckCircle}
          label="Completed"
          value={stats.completed}
          color="text-green-400"
          bgColor="bg-green-500/20"
        />
        <StatCard
          icon={XCircle}
          label="Failed"
          value={stats.failed}
          color="text-red-400"
          bgColor="bg-red-500/20"
        />
        <StatCard
          icon={Clock}
          label="Waiting"
          value={stats.waiting}
          color="text-yellow-400"
          bgColor="bg-yellow-500/20"
        />
      </div>

      {/* Nodes Status */}
      <Card className="bg-gray-800 border-gray-700">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Node Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {currentWorkflow.nodes.map((node) => {
              const Icon = statusIcons[node.status];
              return (
                <div
                  key={node.id}
                  className="flex items-center justify-between p-2 rounded-lg bg-gray-700/50 hover:bg-gray-700"
                >
                  <div className="flex items-center gap-3">
                    <div className={cn("p-1.5 rounded", statusColors[node.status])}>
                      <Icon className="h-3 w-3 text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">{node.name}</p>
                      {node.currentTask && (
                        <p className="text-xs text-gray-400 truncate max-w-[200px]">
                          {node.currentTask}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {node.status === "running" && (
                      <span className="text-xs text-blue-400">{node.progress}%</span>
                    )}
                    {node.retryCount > 0 && (
                      <Badge variant="outline" className="text-xs text-orange-400">
                        Retry {node.retryCount}/{node.maxRetries}
                      </Badge>
                    )}
                    <Badge variant="secondary" className="text-xs capitalize">
                      {node.status}
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Quick Info */}
      <div className="grid grid-cols-2 gap-3">
        <Card className="bg-gray-800 border-gray-700">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Users className="h-8 w-8 text-purple-400" />
              <div>
                <p className="text-xs text-gray-400">Active Agents</p>
                <p className="text-xl font-bold text-white">
                  {currentWorkflow.nodes.filter((n) => n.assignedAgent).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gray-800 border-gray-700">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Timer className="h-8 w-8 text-blue-400" />
              <div>
                <p className="text-xs text-gray-400">Duration</p>
                <p className="text-xl font-bold text-white">{formatDuration(duration)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Export */}
      <Card className="bg-gray-800 border-gray-700">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Export</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2">
          <button
            onClick={() => exportWorkflow("json")}
            className="flex-1 px-3 py-2 text-xs bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
          >
            Export JSON
          </button>
          <button
            onClick={() => exportWorkflow("png")}
            className="flex-1 px-3 py-2 text-xs bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
          >
            Export PNG
          </button>
          <button
            onClick={() => exportWorkflow("svg")}
            className="flex-1 px-3 py-2 text-xs bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
          >
            Export SVG
          </button>
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
  bgColor,
}: {
  icon: React.ElementType;
  label: string;
  value: number;
  color: string;
  bgColor: string;
}) {
  return (
    <Card className="bg-gray-800 border-gray-700">
      <CardContent className="pt-4">
        <div className="flex items-center gap-3">
          <div className={cn("p-2 rounded-lg", bgColor)}>
            <Icon className={cn("h-4 w-4", color)} />
          </div>
          <div>
            <p className="text-xs text-gray-400">{label}</p>
            <p className="text-xl font-bold text-white">{value}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Helper functions
function formatDuration(ms: number, short = false): string {
  if (ms <= 0) return "0s";
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (short) {
    if (days > 0) return `${days}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m`;
    return `${seconds}s`;
  }

  if (days > 0) return `${days}d ${hours % 24}h ${minutes % 60}m`;
  if (hours > 0) return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
}
