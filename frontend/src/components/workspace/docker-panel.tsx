"use client";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function DockerPanel() {
  return (
    <div className="p-4 space-y-4">
      <h3 className="text-sm font-medium">Docker Containers</h3>
      <div className="space-y-2">
        <Card className="p-3"><div className="flex items-center justify-between"><span className="text-sm">nexusmind-app</span><Badge variant="default">running</Badge></div><div className="text-xs text-muted-foreground mt-1">Image: nexusmind/app:latest</div></Card>
        <Card className="p-3"><div className="flex items-center justify-between"><span className="text-sm">postgres-db</span><Badge variant="default">running</Badge></div><div className="text-xs text-muted-foreground mt-1">Image: postgres:15</div></Card>
      </div>
    </div>
  );
}
