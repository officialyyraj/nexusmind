"use client";
import { usePanelsStore } from "@/lib/stores";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { AgentActivity } from "@/components/agents/agent-activity";
import { ExecutionStatus } from "@/components/agents/execution-status";

export function RightSidebar() {
  const { toggleRightPanel } = usePanelsStore();

  return (
    <div className="h-full border-l bg-card flex flex-col">
      <div className="flex items-center justify-between px-4 py-2 border-b">
        <span className="text-sm font-medium">Activity</span>
        <Button variant="ghost" size="icon" onClick={toggleRightPanel}>×</Button>
      </div>
      <ScrollArea className="flex-1">
        <AgentActivity />
        <ExecutionStatus />
      </ScrollArea>
    </div>
  );
}
