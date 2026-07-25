"use client";
import { useLogs } from "@/lib/api/hooks";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const levelColors = { info: "text-blue-500", warn: "text-yellow-500", error: "text-red-500", debug: "text-gray-500" };

export function LogViewer() {
  const { data: logs } = useLogs();
  const logList = logs || [];
  return (
    <ScrollArea className="h-full">
      <div className="p-2 font-mono text-xs space-y-1">
        {logList.map((log) => (
          <div key={log.id} className="flex items-start gap-2">
            <span className="text-muted-foreground shrink-0">{new Date(log.timestamp).toLocaleTimeString()}</span>
            <Badge variant="outline" className={cn("text-xs shrink-0", levelColors[log.level])}>{log.level}</Badge>
            <span className="text-muted-foreground shrink-0">[{log.source}]</span>
            <span className="flex-1 break-all">{log.message}</span>
          </div>
        ))}
        {logList.length === 0 && <div className="text-center text-muted-foreground py-8">No logs available</div>}
      </div>
    </ScrollArea>
  );
}
