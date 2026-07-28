"use client";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Bot, User, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { useSession } from "@/lib/api/hooks";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function SessionWorkspacePage() {
  const params = useParams();
  const sessionId = params.id as string;
  const { data: session, isLoading, error } = useSession(sessionId);
  const [messages, setMessages] = useState<Array<{ role: string; content: string; agentType?: string }>>([]);
  const [input, setInput] = useState("");

  return (
    <AppShell>
      <div className="h-full flex flex-col">
        <div className="border-b p-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/sessions">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div>
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm text-muted-foreground">Loading...</span>
                </div>
              ) : error ? (
                <h1 className="font-semibold text-destructive">Session not found</h1>
              ) : (
                <h1 className="font-semibold">{session?.title || 'Untitled Session'}</h1>
              )}
            </div>
          </div>
          {session && (
            <span className="text-sm text-muted-foreground">
              Status: {session.status}
            </span>
          )}
        </div>
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === "user" ? "bg-primary" : "bg-muted"}`}>
                  {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </div>
                <Card className="max-w-[70%]">
                  <CardContent className="p-3 text-sm">{msg.content}</CardContent>
                </Card>
              </div>
            ))}
            {messages.length === 0 && !isLoading && (
              <div className="text-center py-12 text-muted-foreground">
                Start a conversation with your AI agents
              </div>
            )}
          </div>
        </ScrollArea>
        <div className="border-t p-4">
          <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); if (input) { setMessages([...messages, { role: "user", content: input }]); setInput(""); } }}>
            <Input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Type your message..." className="flex-1" disabled={isLoading || !!error} />
            <Button type="submit" size="icon" disabled={isLoading || !!error || !input.trim()}><Send className="h-4 w-4" /></Button>
          </form>
        </div>
      </div>
    </AppShell>
  );
}
