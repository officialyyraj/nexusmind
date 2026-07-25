"use client";
import { AppShell } from "@/components/layout/app-shell";
import { MetricsGrid } from "@/components/dashboard/metrics-grid";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AgentCard } from "@/components/agents/agent-card";
import { useAgents } from "@/lib/api/hooks";
import { Plus, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const { data: agents } = useAgents();

  return (
    <AppShell>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <Button><Plus className="h-4 w-4 mr-2" />New Session</Button>
        </div>
        <MetricsGrid />
        <div className="grid grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Recent Sessions
                <Link href="/sessions"><Button variant="ghost" size="sm">View all <ArrowRight className="h-3 w-3 ml-1" /></Button></Link>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-2 rounded-lg bg-accent/50">
                  <div>
                    <div className="text-sm font-medium">Build user authentication</div>
                    <div className="text-xs text-muted-foreground">2 hours ago</div>
                  </div>
                  <Badge variant="default">Active</Badge>
                </div>
                <div className="flex items-center justify-between p-2 rounded-lg hover:bg-accent/50">
                  <div>
                    <div className="text-sm font-medium">Fix API pagination bug</div>
                    <div className="text-xs text-muted-foreground">Yesterday</div>
                  </div>
                  <Badge variant="secondary">Completed</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Active Agents
                <Link href="/agents"><Button variant="ghost" size="sm">Manage <ArrowRight className="h-3 w-3 ml-1" /></Button></Link>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2">
                {agents?.slice(0, 4).map((agent) => (
                  <AgentCard key={agent.id} agent={agent} />
                ))}
                {(!agents || agents.length === 0) && (
                  <div className="col-span-2 text-center py-8 text-sm text-muted-foreground">
                    No active agents
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
