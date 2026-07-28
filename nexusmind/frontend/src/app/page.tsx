"use client";
import { AppShell } from "@/components/layout/app-shell";
import { MetricsGrid } from "@/components/dashboard/metrics-grid";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AgentCard } from "@/components/agents/agent-card";
import { useAgents, useSessions, useCreateSession } from "@/lib/api/hooks";
import { Plus, ArrowRight } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function DashboardPage() {
  const router = useRouter();
  const { data: agents } = useAgents();
  const { data: sessions, isLoading: sessionsLoading } = useSessions();
  const createSession = useCreateSession();
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateSession = async () => {
    setIsCreating(true);
    try {
      const result = await createSession.mutateAsync({ 
        title: `New Session ${new Date().toLocaleString()}`
      });
      router.push(`/sessions/${result.id}`);
    } catch (error) {
      console.error('Failed to create session:', error);
      setIsCreating(false);
    }
  };

  const recentSessions = sessions?.slice(0, 5) || [];

  const formatRelativeTime = (dateStr: string | null) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'active':
      case 'running':
        return 'default';
      case 'completed':
        return 'secondary';
      case 'error':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  return (
    <AppShell>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <Button onClick={handleCreateSession} disabled={isCreating}>
            <Plus className="h-4 w-4 mr-2" />
            {isCreating ? 'Creating...' : 'New Session'}
          </Button>
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
              {sessionsLoading ? (
                <div className="text-center py-8 text-sm text-muted-foreground">
                  Loading...
                </div>
              ) : recentSessions.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sm text-muted-foreground mb-4">No sessions yet</p>
                  <Button variant="outline" size="sm" onClick={handleCreateSession} disabled={isCreating}>
                    Create your first session
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  {recentSessions.map((session) => (
                    <Link key={session.id} href={`/sessions/${session.id}`}>
                      <div className="flex items-center justify-between p-2 rounded-lg hover:bg-accent/50 cursor-pointer">
                        <div>
                          <div className="text-sm font-medium">
                            {session.title || 'Untitled Session'}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {formatRelativeTime(session.updated_at)}
                          </div>
                        </div>
                        <Badge variant={getStatusVariant(session.status)}>
                          {session.status}
                        </Badge>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
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
