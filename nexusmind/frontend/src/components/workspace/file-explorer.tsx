"use client";
import { Button } from "@/components/ui/button";
import { FolderOpen, File, ChevronRight, ChevronDown, Plus } from "lucide-react";
import { useState } from "react";

export function FileExplorer() {
  const [expanded, setExpanded] = useState(true);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-muted-foreground">Files</span>
        <Button variant="ghost" size="icon" className="h-6 w-6"><Plus className="h-3 w-3" /></Button>
      </div>
      <div className="space-y-0.5">
        <div className="flex items-center gap-1 p-1 text-xs cursor-pointer hover:bg-accent/50 rounded" onClick={() => setExpanded(!expanded)}>
          {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          <FolderOpen className="h-3 w-3 text-yellow-500" />src
        </div>
        {expanded && (
          <div className="ml-4 space-y-0.5">
            <div className="flex items-center gap-1 p-1 text-xs cursor-pointer hover:bg-accent/50 rounded"><File className="h-3 w-3 text-blue-500" />app.tsx</div>
            <div className="flex items-center gap-1 p-1 text-xs cursor-pointer hover:bg-accent/50 rounded"><File className="h-3 w-3 text-green-500" />utils.ts</div>
          </div>
        )}
      </div>
    </div>
  );
}
