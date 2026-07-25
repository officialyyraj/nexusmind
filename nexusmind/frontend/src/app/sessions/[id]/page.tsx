"use client";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Bot, User } from "lucide-react";
import { useState } from "react";

export default function SessionWorkspacePage({ params }: { params: Promise<{ id: string }> }) {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [input, setInput] = useState("");
  const sessionId = "pending"; // Will be resolved from params in real implementation

  return (
    <AppShell>
      <div className="h-full flex flex-col">
        <div className="border-b p-4 flex items-center justify-between">
          <h1 className="font-semibold">Session Workspace</h1>
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
            {messages.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                Start a conversation with your AI agents
              </div>
            )}
          </div>
        </ScrollArea>
        <div className="border-t p-4">
          <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); if (input) { setMessages([...messages, { role: "user", content: input }]); setInput(""); } }}>
            <Input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Type your message..." className="flex-1" />
            <Button type="submit" size="icon"><Send className="h-4 w-4" /></Button>
          </form>
        </div>
      </div>
    </AppShell>
  );
}
