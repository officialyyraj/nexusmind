"use client";

import { useEffect, useRef, useCallback } from "react";
import type { ChatMessage } from "@/types";
import { MessageItem } from "./message-item";
import { TypingIndicator } from "./typing-indicator";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface MessageListProps {
  messages: ChatMessage[];
  isLoading?: boolean;
  isFetching?: boolean;
  isEmpty?: boolean;
  isTyping?: boolean;
  typingAgentType?: string;
  className?: string;
}

export function MessageList({
  messages,
  isLoading = false,
  isFetching = false,
  isEmpty = false,
  isTyping = false,
  typingAgentType,
  className = "",
}: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const isAutoScrollEnabled = useRef(true);
  
  // Scroll to bottom function
  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    bottomRef.current?.scrollIntoView({ behavior, block: "end" });
  }, []);
  
  // Handle scroll to detect if user scrolled up
  const handleScroll = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    
    const { scrollTop, scrollHeight, clientHeight } = container;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
    isAutoScrollEnabled.current = isNearBottom;
  }, []);
  
  // Auto-scroll when new messages arrive (if enabled)
  useEffect(() => {
    if (!isAutoScrollEnabled.current) return;
    
    let rafId: number | null = null;
    
    const handleScroll = () => {
      rafId = requestAnimationFrame(() => {
        scrollToBottom("smooth");
      });
    };
    
    handleScroll();
    
    return () => {
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
      }
    };
  }, [messages.length, scrollToBottom]);
  
  // Scroll to bottom on mount
  useEffect(() => {
    scrollToBottom("instant");
  }, [scrollToBottom]);
  
  // Loading skeleton
  if (isLoading) {
    return (
      <div className={cn("flex items-center justify-center h-full", className)}>
        <div className="flex flex-col items-center gap-4 text-muted-foreground">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="text-sm">Loading messages...</span>
        </div>
      </div>
    );
  }
  
  // Empty state
  if (isEmpty && messages.length === 0) {
    return (
      <div className={cn("flex items-center justify-center h-full", className)}>
        <div className="text-center">
          <div className="text-4xl mb-4">💬</div>
          <h3 className="text-lg font-medium mb-2">No messages yet</h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            Start a conversation with your AI agents. Type a message below to begin.
          </p>
        </div>
      </div>
    );
  }
  
  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className={cn("flex-1 overflow-y-auto p-4", className)}
    >
      <div className="space-y-4">
        {/* Fetching indicator */}
        {isFetching && messages.length > 0 && (
          <div className="flex justify-center">
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          </div>
        )}
        
        {/* Messages */}
        {messages.map((message, index) => (
          <MessageItem 
            key={message.id} 
            message={message}
            isOptimistic={!message.created_at}
          />
        ))}
        
        {/* Typing indicator */}
        {isTyping && (
          <TypingIndicator 
            agentType={typingAgentType}
            className="mt-4"
          />
        )}
        
        {/* Bottom anchor */}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
