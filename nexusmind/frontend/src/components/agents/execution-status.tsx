"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useWorkflowStore } from "@/lib/stores/workflow";
import { useRealtimeStore } from "@/lib/stores/realtime";
import { useEffect } from "react";
import { Play, CheckCircle, XCircle, Loader2, Brain, Code, Search, Eye, FileText, User } from "lucide-react";

const agentIcons: Record<string, React.ElementType> = {
  planner: Brain,
  researcher: Search,
  coder: Code,
  reviewer: Eye,
  tester: User,
  documentation: FileText,
  manager: User,
};

const statusColors: Record<string, string> = {
  idle: "bg-gray-500",
  running: "bg-blue-500",
  completed: "bg-green-500",
  failed: "bg-red-500",
  waiting: "bg-yellow-500",
};

export function ExecutionStatus() {
  const { currentWorkflow, syncFromRealtime } = useWorkflowStore();
  const realtime = useRealtimeStore();
  
  // Sync from realtime on changes
  useEffect(() => {
    if (currentWorkflow) {
      syncFromRealtime();
    }
  }, [realtime.executionUpdates, realtime.logs, currentWorkflow, syncFromRealtime]);
  
  const currentNode = currentWorkflow?.nodes.find(n => n.status === "running");
  const completedNodes = currentWorkflow?.nodes.filter(n => n.status === "completed").length || 0;
  const totalNodes = currentWorkflow?.nodes.length || 0;
  
  const update = currentWorkflow ? realtime.executionUpdates.get(currentWorkflow.id) : null;
  
  return (
    <div className="p-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center justify-between">
            <span>Current Task</span>
            {currentWorkflow && (
              <Badge variant={currentWorkflow.status === "running" ? "default" : "secondary"}>
                {currentWorkflow.status}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!currentWorkflow ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="w-2 h-2 rounded-full bg-gray-400" />
                <span>No task running</span>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Task info */}
              <div>
                <p className="text-sm font-medium truncate" title={currentWorkflow.name}>
                  {currentWorkflow.name}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-500 transition-all"
                      style={{ width: `${currentWorkflow.progress}%` }}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {currentWorkflow.progress}%
                  </span>
                </div>
              </div>
              
              {/* Current agent */}
              {currentNode && (
                <div className="flex items-center gap-2 p-2 bg-blue-50 rounded-lg">
                  {(() => {
                    const Icon = agentIcons[currentNode.type] || User;
                    return <Icon className="w-4 h-4 text-blue-600" />;
                  })()}
                  <div className="flex-1">
                    <p className="text-sm font-medium capitalize">{currentNode.name}</p>
                    <p className="text-xs text-muted-foreground truncate">
                      {currentNode.currentTask || "Running..."}
                    </p>
                  </div>
                  <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                </div>
              )}
              
              {/* Progress summary */}
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">
                  {completedNodes} / {totalNodes} steps
                </span>
                {update?.currentAgent && (
                  <span className="capitalize">{update.currentAgent}</span>
                )}
              </div>
              
              {/* Status indicator */}
              <div className="flex items-center gap-2">
                {currentWorkflow.status === "completed" && (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                )}
                {currentWorkflow.status === "failed" && (
                  <XCircle className="w-4 h-4 text-red-500" />
                )}
                {currentWorkflow.status === "running" && (
                  <Play className="w-4 h-4 text-blue-500" />
                )}
                <span className="text-xs capitalize">{currentWorkflow.status}</span>
              </div>
              
              {/* Error display */}
              {currentWorkflow.status === "failed" && (
                <div className="p-2 bg-red-50 rounded text-xs text-red-600">
                  Execution failed. Check logs for details.
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
