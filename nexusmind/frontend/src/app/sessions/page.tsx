"use client";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useSessions } from "@/lib/api/hooks";
import { Plus, Search } from "lucide-react";
import Link from "next/link";
import type { Session } from "@/types";

export default function SessionsPage() {
  const { data: sessions, isLoading } = useSessions();
  const sessionsList: Session[] = sessions || [];

  return (
    <AppShell>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Sessions</h1>
          <Button><Plus className="h-4 w-4 mr-2" />New Session</Button>
        </div>
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search sessions..." className="pl-10" />
        </div>
        {isLoading ? (
          <div className="text-center py-12 text-muted-foreground">Loading...</div>
        ) : (
          <div className="grid gap-4">
            {sessionsList.map((session) => (
              <Link key={session.id} href={`/sessions/${session.id}`}>
                <Card className="hover:bg-accent/50 cursor-pointer">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle>{session.name}</CardTitle>
                      <Badge variant={session.status === "active" ? "default" : "secondary"}>
                        {session.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>{session.messageCount} messages</span>
                      <span>Updated {new Date(session.updatedAt).toLocaleDateString()}</span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
            {sessionsList.length === 0 && (
              <div className="text-center py-12">
                <p className="text-muted-foreground mb-4">No sessions yet</p>
                <Button>Create your first session</Button>
              </div>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
