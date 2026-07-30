"use client";

import { Bot } from "lucide-react";

interface TypingIndicatorProps {
  agentType?: string;
  className?: string;
}

export function TypingIndicator({ agentType, className = "" }: TypingIndicatorProps) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center shrink-0">
        <Bot className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="flex items-center gap-1">
        <span className="text-sm text-muted-foreground">
          {agentType ? `${agentType} is thinking` : 'Assistant is thinking'}
        </span>
        <span className="flex gap-1 ml-1">
          <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.3s]" />
          <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.15s]" />
          <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:0s]" />
        </span>
      </div>
    </div>
  );
}
