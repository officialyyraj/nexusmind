"use client";

import { useMemo, useState } from "react";
import { useWorkflowStore } from "@/lib/stores/workflow";
import { cn } from "@/lib/utils";
import {
  Play,
  Pause,
  SkipBack,
  RotateCcw,
  Clock,
  CheckCircle,
  XCircle,
  ChevronDown,
  Brain,
  Search,
  Code,
  Eye,
  TestTube,
  FileText,
  User,
  Flag,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ExecutionPhase, TimelineEvent } from "@/types";

const phaseIcons: Record<ExecutionPhase, React.ElementType> = {
  start: Flag,
  planning: Brain,
  research: Search,
  coding: Code,
  review: Eye,
  testing: TestTube,
  documentation: FileText,
  complete: CheckCircle,
};

const phaseColors: Record<ExecutionPhase, string> = {
  start: "text-gray-400",
  planning: "text-blue-400",
  research: "text-purple-400",
  coding: "text-green-400",
  review: "text-yellow-400",
  testing: "text-orange-400",
  documentation: "text-cyan-400",
  complete: "text-green-500",
};

interface ExecutionTimelineProps {
  className?: string;
  onEventClick?: (event: TimelineEvent) => void;
}

export function ExecutionTimeline({ className, onEventClick }: ExecutionTimelineProps) {
  const {
    currentWorkflow,
    timeline,
    isLive,
    playbackSpeed,
    toggleLive,
    setPlaybackSpeed,
    replayWorkflow,
    selectNode,
  } = useWorkflowStore();

  const [showReplay, setShowReplay] = useState(false);

  // Generate timeline from workflow nodes
  const events = useMemo(() => {
    if (!currentWorkflow) return [];

    const workflowEvents: TimelineEvent[] = [];
    
    // Add start event
    workflowEvents.push({
      id: "start",
      phase: "start",
      status: "started",
      timestamp: currentWorkflow.startedAt,
      details: "Workflow started",
    });

    // Add node events based on their status
    currentWorkflow.nodes.forEach((node) => {
      if (node.startedAt) {
        workflowEvents.push({
          id: `${node.id}-start`,
          phase: node.type as ExecutionPhase,
          nodeId: node.id,
          nodeName: node.name,
          status: "started",
          timestamp: node.startedAt,
          details: `${node.name} started${node.currentTask ? `: ${node.currentTask}` : ""}`,
        });
      }
      if (node.completedAt) {
        workflowEvents.push({
          id: `${node.id}-complete`,
          phase: node.type as ExecutionPhase,
          nodeId: node.id,
          nodeName: node.name,
          status: node.status === "failed" ? "failed" : "completed",
          timestamp: node.completedAt,
          duration: node.duration,
          details: node.output || `${node.name} ${node.status === "failed" ? "failed" : "completed"}`,
        });
      }
    });

    // Add complete event
    if (currentWorkflow.completedAt) {
      workflowEvents.push({
        id: "complete",
        phase: "complete",
        status: currentWorkflow.status === "failed" ? "failed" : "completed",
        timestamp: currentWorkflow.completedAt,
        duration: currentWorkflow.duration,
        details: currentWorkflow.status === "failed" ? "Workflow failed" : "Workflow completed",
      });
    }

    // Sort by timestamp
    return workflowEvents.sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  }, [currentWorkflow]);

  const handleEventClick = (event: TimelineEvent) => {
    if (event.nodeId) {
      selectNode(event.nodeId);
    }
    onEventClick?.(event);
  };

  if (!currentWorkflow) {
    return (
      <div className={cn("flex items-center justify-center h-full bg-gray-900 border-t border-gray-700", className)}>
        <div className="text-center text-gray-500">
          <Clock className="h-8 w-8 mx-auto mb-2 text-gray-600" />
          <p className="text-sm">No timeline available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full bg-gray-900 border-t border-gray-700", className)}>
      {/* Timeline Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-medium text-white">Execution Timeline</h3>
          <Badge variant="outline" className="text-xs">
            {events.length} events
          </Badge>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Playback Controls */}
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={toggleLive}
          >
            {isLive ? (
              <Pause className="h-4 w-4 text-green-400" />
            ) : (
              <Play className="h-4 w-4 text-yellow-400" />
            )}
          </Button>
          
          {/* Replay Button */}
          <DropdownMenu open={showReplay} onOpenChange={setShowReplay}>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 text-xs">
                <RotateCcw className="h-3 w-3 mr-1" />
                Replay
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => { replayWorkflow(); setShowReplay(false); }}>
                <RotateCcw className="h-4 w-4 mr-2" />
                Replay from start
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Playback Speed */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 text-xs">
                {playbackSpeed}x
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {[0.5, 1, 2, 4].map((speed) => (
                <DropdownMenuItem
                  key={speed}
                  onClick={() => setPlaybackSpeed(speed)}
                  className={playbackSpeed === speed ? "bg-gray-700" : ""}
                >
                  {speed}x
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Timeline Content */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          <div className="relative">
            {/* Vertical line */}
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-700" />
            
            {/* Events */}
            <div className="space-y-4">
              {events.map((event, index) => {
                const Icon = phaseIcons[event.phase];
                const color = phaseColors[event.phase];
                const isLast = index === events.length - 1;
                
                return (
                  <div
                    key={event.id}
                    className={cn(
                      "relative flex items-start gap-4 pl-10 cursor-pointer group",
                      event.nodeId && "hover:bg-gray-800/50 rounded-lg p-2 -m-2"
                    )}
                    onClick={() => handleEventClick(event)}
                  >
                    {/* Icon */}
                    <div
                      className={cn(
                        "absolute left-2 w-5 h-5 rounded-full flex items-center justify-center z-10",
                        "bg-gray-800 border-2 border-gray-700 group-hover:border-gray-500 transition-colors",
                        event.status === "completed" && "bg-green-900 border-green-700",
                        event.status === "failed" && "bg-red-900 border-red-700",
                        event.status === "started" && "bg-blue-900 border-blue-700"
                      )}
                    >
                      <Icon className={cn("h-3 w-3", color)} />
                    </div>
                    
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-white capitalize">
                          {event.phase === "start" ? "Start" : 
                           event.phase === "complete" ? "Complete" : 
                           event.nodeName || event.phase}
                        </span>
                        <Badge
                          variant="secondary"
                          className={cn(
                            "text-xs capitalize",
                            event.status === "completed" && "bg-green-900 text-green-300",
                            event.status === "failed" && "bg-red-900 text-red-300",
                            event.status === "started" && "bg-blue-900 text-blue-300"
                          )}
                        >
                          {event.status}
                        </Badge>
                      </div>
                      
                      {event.details && (
                        <p className="text-xs text-gray-400 truncate mb-1">
                          {event.details}
                        </p>
                      )}
                      
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span>{formatTime(event.timestamp)}</span>
                        {event.duration && (
                          <span>{formatDuration(event.duration)}</span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </ScrollArea>

      {/* Summary Footer */}
      {currentWorkflow && (
        <div className="px-4 py-3 border-t border-gray-700 bg-gray-800/50">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-blue-500" />
                <span className="text-gray-400">Running: {currentWorkflow.nodes.filter(n => n.status === "running").length}</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <span className="text-gray-400">Completed: {currentWorkflow.nodes.filter(n => n.status === "completed").length}</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-gray-400">Failed: {currentWorkflow.nodes.filter(n => n.status === "failed").length}</span>
              </div>
            </div>
            <div className="text-gray-400">
              Total: {formatDuration(currentWorkflow.duration)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Helper functions
function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function formatDuration(ms?: number): string {
  if (!ms) return "-";
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) return `${hours}h ${minutes % 60}m`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
}
