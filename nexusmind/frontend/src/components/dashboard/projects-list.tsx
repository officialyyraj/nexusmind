"use client";
import { Card } from "@/components/ui/card";

export function ProjectsList() {
  // DEFERRED: Projects feature not implemented in Phase 3
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-muted-foreground">Projects</span>
      </div>
      <Card className="p-3">
        <p className="text-xs text-muted-foreground text-center">Projects coming soon</p>
      </Card>
    </div>
  );
}
