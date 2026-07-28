"use client";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useSessions, useCreateSession, useDeleteSession } from "@/lib/api/hooks";
import { Plus, Search, Trash2, Loader2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export default function SessionsPage() {
  const router = useRouter();
  const { data: sessions, isLoading } = useSessions();
  const createSession = useCreateSession();
  const deleteSession = useDeleteSession();
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [newSessionTitle, setNewSessionTitle] = useState("");
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);

  const sessionsList = sessions || [];

  const filteredSessions = sessionsList.filter((session) => {
    const title = session.title || 'Untitled Session';
    return title.toLowerCase().includes(searchQuery.toLowerCase());
  });

  const handleCreateSession = async () => {
    setIsCreating(true);
    try {
      const result = await createSession.mutateAsync({
        title: newSessionTitle.trim() || `New Session ${new Date().toLocaleString()}`
      });
      setNewSessionTitle("");
      router.push(`/sessions/${result.id}`);
    } catch (error) {
      console.error('Failed to create session:', error);
      setIsCreating(false);
    }
  };

  const handleDeleteSession = async () => {
    if (!sessionToDelete) return;
    try {
      await deleteSession.mutateAsync(sessionToDelete);
      setSessionToDelete(null);
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Unknown';
    return new Date(dateStr).toLocaleDateString();
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
    <AppShell>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Sessions</h1>
          <Dialog open={isCreating} onOpenChange={setIsCreating}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />New Session</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Session</DialogTitle>
                <DialogDescription>
                  Give your session a name or leave it blank to use the default.
                </DialogDescription>
              </DialogHeader>
              <Input
                placeholder="Session title (optional)"
                value={newSessionTitle}
                onChange={(e) => setNewSessionTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleCreateSession();
                  }
                }}
              />
              <DialogFooter>
                <Button
                  onClick={handleCreateSession}
                  disabled={createSession.isPending}
                >
                  {createSession.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Session'
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search sessions..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        {isLoading ? (
          <div className="text-center py-12 text-muted-foreground">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            Loading sessions...
          </div>
        ) : filteredSessions.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">
              {searchQuery ? 'No sessions match your search' : 'No sessions yet'}
            </p>
            {!searchQuery && (
              <Button onClick={() => setIsCreating(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create your first session
              </Button>
            )}
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredSessions.map((session) => (
              <div key={session.id} className="flex gap-2">
                <Link href={`/sessions/${session.id}`} className="flex-1">
                  <Card className="hover:bg-accent/50 cursor-pointer h-full">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle>{session.title || 'Untitled Session'}</CardTitle>
                        <Badge variant={getStatusVariant(session.status)}>
                          {session.status}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>Created {formatDate(session.created_at)}</span>
                        <span>Updated {formatDate(session.updated_at)}</span>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      className="shrink-0"
                      onClick={() => setSessionToDelete(session.id)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Delete Session</AlertDialogTitle>
                      <AlertDialogDescription>
                        Are you sure you want to delete "{session.title || 'Untitled Session'}"?
                        This action cannot be undone.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel onClick={() => setSessionToDelete(null)}>
                        Cancel
                      </AlertDialogCancel>
                      <AlertDialogAction
                        onClick={handleDeleteSession}
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        disabled={deleteSession.isPending}
                      >
                        {deleteSession.isPending ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Deleting...
                          </>
                        ) : (
                          'Delete'
                        )}
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
