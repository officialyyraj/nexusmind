"use client";
import { useProjects } from "@/lib/api/hooks";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

export function ProjectsList() {
  const { data: projects } = useProjects();
  const list = projects || [];
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-muted-foreground">Projects</span>
        <Button variant="ghost" size="icon" className="h-6 w-6"><Plus className="h-3 w-3" /></Button>
      </div>
      {list.length === 0 && <div className="text-xs text-muted-foreground p-2">No projects</div>}
      {list.map((p) => (
        <Card key={p.id} className="p-2 cursor-pointer hover:bg-accent/50">
          <div className="text-sm font-medium truncate">{p.name}</div>
          <div className="text-xs text-muted-foreground mt-1">{p.sessionCount} sessions</div>
        </Card>
      ))}
    </div>
  );
}
