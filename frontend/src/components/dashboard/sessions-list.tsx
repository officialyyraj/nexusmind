"use client";
import { useSessions } from "@/lib/api/hooks";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plus, Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCreateSession } from "@/lib/api/hooks";

export function SessionsList() {
  const router = useRouter();
  const { data: sessions, isLoading } = useSessions();
  const createSession = useCreateSession();
  const list = sessions || [];

  const handleCreateSession = async () => {
    try {
      const result = await createSession.mutateAsync({
        title: `New Session ${new Date().toLocaleString()}`
      });
      router.push(`/sessions/${result.id}`);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'active':
      case 'running':
      case 'created':
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
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-muted-foreground">Sessions</span>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={handleCreateSession}
          disabled={createSession.isPending}
        >
          {createSession.isPending ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Plus className="h-3 w-3" />
          )}
        </Button>
      </div>
      {isLoading ? (
        <div className="text-xs text-muted-foreground p-2 flex items-center gap-2">
          <Loader2 className="h-3 w-3 animate-spin" />
          Loading...
        </div>
      ) : list.length === 0 ? (
        <div className="text-xs text-muted-foreground p-2">No sessions</div>
      ) : (
        list.slice(0, 5).map((s) => (
          <Link key={s.id} href={`/sessions/${s.id}`}>
            <Card className="p-2 cursor-pointer hover:bg-accent/50">
              <div className="text-sm font-medium truncate">{s.title || 'Untitled Session'}</div>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant={getStatusVariant(s.status)} className="text-xs">{s.status}</Badge>
              </div>
            </Card>
          </Link>
        ))
      )}
    </div>
  );
}
