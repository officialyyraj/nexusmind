"use client";

import { useCallback, useState, useEffect } from "react";
import type { ChatMessage } from "@/types";
import { MessageList } from "./message-list";
import { MessageInput } from "./message-input";
import { Button } from "@/components/ui/button";
import { RefreshCw, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatContainerProps {
  sessionId: string;
  messages: ChatMessage[];
  isLoading: boolean;
  isFetching: boolean;
  isError: boolean;
  error: Error | null;
  isEmpty: boolean;
  isSending: boolean;
  onSendMessage: (content: string) => void;
  onRefresh: () => void;
  className?: string;
}

export function ChatContainer({
  sessionId,
  messages,
  isLoading,
  isFetching,
  isError,
  error,
  isEmpty,
  isSending,
  onSendMessage,
  onRefresh,
  className = "",
}: ChatContainerProps) {
  const [showRefresh, setShowRefresh] = useState(false);
  
  // Show refresh button when fetching after initial load
  useEffect(() => {
    if (!isLoading && isFetching) {
      setShowRefresh(true);
    }
  }, [isLoading, isFetching]);
  
  const handleRefresh = useCallback(() => {
    onRefresh();
    setShowRefresh(false);
  }, [onRefresh]);
  
  const handleSend = useCallback((content: string) => {
    onSendMessage(content);
  }, [onSendMessage]);
  
  // Error state
  if (isError) {
    return (
      <div className={cn("flex flex-col h-full", className)}>
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="text-center max-w-md">
            <div className="flex justify-center mb-4">
              <XCircle className="h-12 w-12 text-destructive" />
            </div>
            <h3 className="text-lg font-medium mb-2">Failed to load messages</h3>
            <p className="text-sm text-muted-foreground mb-4">
              {error?.message || "An unknown error occurred"}
            </p>
            <Button onClick={onRefresh} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try again
            </Button>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Refresh indicator */}
      {showRefresh && (
        <div className="absolute top-16 left-1/2 -translate-x-1/2 z-10">
          <Button
            size="sm"
            variant="secondary"
            onClick={handleRefresh}
            className="shadow-md animate-pulse"
          >
            <RefreshCw className="h-3 w-3 mr-1" />
            New messages
          </Button>
        </div>
      )}
      
      {/* Message list */}
      <MessageList
        messages={messages}
        isLoading={isLoading}
        isFetching={isFetching}
        isEmpty={isEmpty}
        className="flex-1"
      />
      
      {/* Message input */}
      <MessageInput
        onSend={handleSend}
        disabled={isLoading || isError || !sessionId}
        isLoading={isSending}
        placeholder="Type your message..."
        autoFocus
      />
    </div>
  );
}
