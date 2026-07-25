"use client";
import { useAgents } from "@/lib/api/hooks";
import { AgentCard } from "./agent-card";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

export function AgentActivity() {
  const { data: agents } = useAgents();
  const list = agents || [];
  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Active Agents</h3>
        <Button variant="ghost" size="icon" className="h-6 w-6"><Plus className="h-3 w-3" /></Button>
      </div>
      <div className="space-y-2">
        {list.map((agent) => <AgentCard key={agent.id} agent={agent} />)}
        {list.length === 0 && <div className="text-xs text-muted-foreground">No active agents</div>}
      </div>
    </div>
  );
}
