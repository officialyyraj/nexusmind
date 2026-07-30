"use client";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { Agent } from "@/types";
import { Clock, Cpu, HardDrive } from "lucide-react";

interface AgentCardProps {
  agent: Agent;
  expanded?: boolean;
  onToggle?: () => void;
}

export function AgentCard({ agent, expanded, onToggle }: AgentCardProps) {
  return (
    <Card className="cursor-pointer" onClick={onToggle}>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-white text-sm font-medium">{agent.name.charAt(0)}</div>
          <div className="flex-1 min-w-0">
            <CardTitle className="text-sm truncate">{agent.name}</CardTitle>
            <Badge variant={agent.status === "running" ? "default" : "secondary"} className="mt-1 text-xs">{agent.status}</Badge>
          </div>
        </div>
      </CardHeader>
      {expanded && (
        <CardContent className="space-y-3 pt-0">
          <div className="text-xs text-muted-foreground">{agent.currentTask || "Idle"}</div>
          {agent.progress !== undefined && (
            <div className="space-y-1">
              <div className="flex justify-between text-xs"><span>Progress</span><span>{agent.progress}%</span></div>
              <Progress value={agent.progress} />
            </div>
          )}
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="flex items-center gap-1"><Clock className="h-3 w-3" />{agent.elapsedTime ? `${Math.floor(agent.elapsedTime / 60)}m` : "-"}</div>
            <div className="flex items-center gap-1"><Cpu className="h-3 w-3" />{agent.cpuUsage ? `${agent.cpuUsage}%` : "-"}</div>
            <div className="flex items-center gap-1"><HardDrive className="h-3 w-3" />{agent.memoryUsage ? `${agent.memoryUsage}MB` : "-"}</div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
