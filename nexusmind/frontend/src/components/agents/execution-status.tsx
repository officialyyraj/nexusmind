"use client";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export function ExecutionStatus() {
  return (
    <div className="p-4">
      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-sm">Current Task</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No task running</p>
          <div className="mt-4 space-y-2">
            <div className="text-xs text-muted-foreground">Memory Access</div>
            <p className="text-xs text-muted-foreground">-</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
