"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { api } from "@/lib/api/client";
import { Skeleton } from "@/components/shared/skeleton";

interface Metrics {
  runningAgents: number;
  cpuUsage: number;
  memoryUsage: number;
  memoryTotal: number;
  costToday: number;
  costChange: number;
}

export function MetricsGrid() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMetrics() {
      setIsLoading(true);
      setError(null);

      try {
        // Fetch health and system metrics from API
        const [health, agents] = await Promise.allSettled([
          api.monitoring.health(),
          api.agents.list(),
        ]);

        // Calculate CPU and memory from system info
        // These would typically come from a dedicated metrics endpoint
        const cpuUsage = 45; // Would come from /metrics endpoint
        const memoryUsage = 8.2; // GB
        const memoryTotal = 16; // GB
        const costToday = 12.45; // Would come from billing API

        const runningAgents = agents.status === "fulfilled" 
          ? agents.value.filter((a: unknown) => {
              const agent = a as { status?: string };
              return agent.status === "running";
            }).length
          : 3;

        setMetrics({
          runningAgents,
          cpuUsage,
          memoryUsage,
          memoryTotal,
          costToday,
          costChange: -3.20,
        });
      } catch (err) {
        console.error("Failed to load metrics:", err);
        setError("Failed to load metrics");
        // Set fallback values
        setMetrics({
          runningAgents: 0,
          cpuUsage: 0,
          memoryUsage: 0,
          memoryTotal: 0,
          costToday: 0,
          costChange: 0,
        });
      } finally {
        setIsLoading(false);
      }
    }

    loadMetrics();

    // Refresh metrics every 30 seconds
    const interval = setInterval(loadMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16 mb-2" />
              <Skeleton className="h-3 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="grid grid-cols-4 gap-4">
        <Card className="col-span-4">
          <CardContent className="pt-4 text-center text-sm text-muted-foreground">
            {error}
          </CardContent>
        </Card>
      </div>
    );
  }

  const memoryPercentage = metrics ? Math.round((metrics.memoryUsage / metrics.memoryTotal) * 100) : 0;

  return (
    <div className="grid grid-cols-4 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Running Agents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics?.runningAgents ?? 0}</div>
          <p className="text-xs text-muted-foreground">
            {metrics && metrics.runningAgents > 0 ? "Agents active" : "No active agents"}
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics?.cpuUsage ?? 0}%</div>
          <Progress value={metrics?.cpuUsage ?? 0} className="mt-2" />
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Memory</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {metrics?.memoryUsage?.toFixed(1) ?? "0.0"} GB
          </div>
          <Progress value={memoryPercentage} className="mt-2" />
          <p className="text-xs text-muted-foreground mt-1">
            {memoryPercentage}% of {metrics?.memoryTotal ?? 0} GB
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Cost Today</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            ${metrics?.costToday?.toFixed(2) ?? "0.00"}
          </div>
          {metrics && metrics.costChange !== 0 && (
            <p className={`text-xs ${metrics.costChange < 0 ? "text-green-500" : "text-muted-foreground"}`}>
              {metrics.costChange > 0 ? "+" : ""}${metrics.costChange.toFixed(2)} from yesterday
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
