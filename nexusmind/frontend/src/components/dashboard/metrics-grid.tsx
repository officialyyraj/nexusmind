"use client";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

export function MetricsGrid() {
  return (
    <div className="grid grid-cols-4 gap-4">
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Running Agents</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">3</div><p className="text-xs text-muted-foreground">+2 from yesterday</p></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">CPU Usage</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">45%</div><Progress value={45} className="mt-2" /></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Memory</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">8.2 GB</div><Progress value={68} className="mt-2" /></CardContent></Card>
      <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Cost Today</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">$12.45</div><p className="text-xs text-muted-foreground">-$3.20 from yesterday</p></CardContent></Card>
    </div>
  );
}
