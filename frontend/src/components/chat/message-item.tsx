"use client";

import { Bot, User, Settings, Wrench } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { ChatMessage } from "@/types";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

interface MessageItemProps {
  message: ChatMessage;
  isOptimistic?: boolean;
  className?: string;
}

const roleIcons = {
  user: User,
  assistant: Bot,
  system: Settings,
  tool: Wrench,
};

const roleColors = {
  user: "bg-primary text-primary-foreground",
  assistant: "bg-muted text-muted-foreground",
  system: "bg-secondary text-secondary-foreground",
  tool: "bg-accent text-accent-foreground",
};

export function MessageItem({ message, isOptimistic = false, className = "" }: MessageItemProps) {
  const Icon = roleIcons[message.role] || Bot;
  const isUser = message.role === "user";
  
  // Safely format date, handling invalid dates
  const formattedTime = (() => {
    if (!message.created_at) return "...";
    const date = new Date(message.created_at);
    if (isNaN(date.getTime())) return "...";
    return format(date, "HH:mm");
  })();
  
  return (
    <div 
      className={cn(
        "flex gap-3",
        isUser ? "flex-row-reverse" : "",
        className
      )}
    >
      <div 
        className={cn(
          "h-8 w-8 rounded-full flex items-center justify-center shrink-0",
          roleColors[message.role]
        )}
      >
        <Icon className="h-4 w-4" />
      </div>
      <div className={cn("flex flex-col gap-1", isUser ? "items-end" : "items-start")}>
        <Card 
          className={cn(
            "max-w-[70%]",
            isOptimistic && "opacity-70"
          )}
        >
          <CardContent className="p-3 text-sm whitespace-pre-wrap break-words">
            {message.content}
          </CardContent>
        </Card>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {message.agent_type && (
            <span className="px-1.5 py-0.5 rounded bg-secondary text-secondary-foreground text-[10px]">
              {message.agent_type}
            </span>
          )}
          <span>{formattedTime}</span>
          {isOptimistic && <span className="text-[10px] italic">sending...</span>}
        </div>
      </div>
    </div>
  );
}
