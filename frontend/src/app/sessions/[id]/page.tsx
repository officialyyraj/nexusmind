"use client";

import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Loader2, ArrowLeft, RefreshCw } from "lucide-react";
import { useCallback, useMemo } from "react";
import { useSession } from "@/lib/api/hooks";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ChatContainer } from "@/components/chat";
import { useMessages } from "@/lib/api/hooks/chat/useMessages";
import { useSendMessage } from "@/lib/api/hooks/chat/useSendMessage";
import type { ChatMessage } from "@/types";

export default function SessionWorkspacePage() {
  const params = useParams();
  const sessionId = params.id as string;
  
  // Session query
  const { 
    data: session, 
    isLoading: isSessionLoading, 
    error: sessionError,
    refetch: refetchSession 
  } = useSession(sessionId);
  
  // Messages query
  const {
    messages,
    isLoading: isMessagesLoading,
    isFetching: isMessagesFetching,
    error: messagesError,
    isEmpty: isMessagesEmpty,
    refetch: refetchMessages
  } = useMessages({ sessionId });
  
  // Send message mutation
  const {
    sendMessage,
    isPending: isSending,
    isError: isSendError,
    error: sendError
  } = useSendMessage({ 
    sessionId,
    onError: (error) => {
      console.error('Failed to send message:', error);
    }
  });
  
  // Combined loading state
  const isLoading = isSessionLoading || isMessagesLoading;
  
  // Combined error state
  const error = sessionError || messagesError || (isSendError ? sendError : null);
  
  // Handle send message
  const handleSendMessage = useCallback((content: string) => {
    sendMessage(content);
  }, [sendMessage]);
  
  // Handle refresh
  const handleRefresh = useCallback(() => {
    refetchMessages();
    refetchSession();
  }, [refetchMessages, refetchSession]);
  
  // Format messages for the container
  const formattedMessages = useMemo<ChatMessage[]>(() => {
    return messages as ChatMessage[];
  }, [messages]);

  return (
    <AppShell>
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="border-b p-4 flex items-center justify-between bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="flex items-center gap-4">
            <Link href="/sessions">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div>
              {isSessionLoading ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm text-muted-foreground">Loading...</span>
                </div>
              ) : sessionError ? (
                <h1 className="font-semibold text-destructive">Session not found</h1>
              ) : (
                <h1 className="font-semibold">{session?.title || 'Untitled Session'}</h1>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {session && (
              <span className="text-sm text-muted-foreground">
                Status: {session.status}
              </span>
            )}
            <Button 
              variant="ghost" 
              size="icon"
              onClick={handleRefresh}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 ${isMessagesFetching ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
        
        {/* Chat container */}
        <div className="flex-1 overflow-hidden relative">
          <ChatContainer
            sessionId={sessionId}
            messages={formattedMessages}
            isLoading={isLoading}
            isFetching={isMessagesFetching}
            isError={!!error}
            error={error as Error | null}
            isEmpty={isMessagesEmpty}
            isSending={isSending}
            onSendMessage={handleSendMessage}
            onRefresh={handleRefresh}
          />
        </div>
      </div>
    </AppShell>
  );
}
