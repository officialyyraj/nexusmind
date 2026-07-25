"use client";
import { useSessions } from "@/lib/api/hooks";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import Link from "next/link";

export function SessionsList() {
  const { data: sessions } = useSessions();
  const list = sessions || [];
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-muted-foreground">Sessions</span>
        <Button variant="ghost" size="icon" className="h-6 w-6"><Plus className="h-3 w-3" /></Button>
      </div>
      {list.length === 0 && <div className="text-xs text-muted-foreground p-2">No sessions</div>}
      {list.map((s) => (
        <Link key={s.id} href={`/sessions/${s.id}`}>
          <Card className="p-2 cursor-pointer hover:bg-accent/50">
            <div className="text-sm font-medium truncate">{s.name}</div>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={s.status === "active" ? "default" : "secondary"} className="text-xs">{s.status}</Badge>
              <span className="text-xs text-muted-foreground">{s.messageCount} msgs</span>
            </div>
          </Card>
        </Link>
      ))}
    </div>
  );
}
