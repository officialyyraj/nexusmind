"use client";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";

export function MemoryExplorer() {
  return (
    <div className="space-y-2">
      <div className="relative">
        <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
        <Input placeholder="Search memory..." className="pl-7 h-7 text-xs" />
      </div>
      <div className="space-y-1">
        <Card className="p-2 cursor-pointer hover:bg-accent/50"><div className="text-xs font-medium truncate">User prefers dark theme</div><Badge variant="outline" className="mt-1 text-xs">preference</Badge></Card>
        <Card className="p-2 cursor-pointer hover:bg-accent/50"><div className="text-xs font-medium truncate">Last session context</div><Badge variant="outline" className="mt-1 text-xs">context</Badge></Card>
      </div>
    </div>
  );
}
