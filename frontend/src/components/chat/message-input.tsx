"use client";

import { useState, useRef, useCallback, useEffect, type FormEvent, type KeyboardEvent } from "react";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

interface MessageInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
  placeholder?: string;
  className?: string;
  autoFocus?: boolean;
}

export function MessageInput({
  onSend,
  disabled = false,
  isLoading = false,
  placeholder = "Type your message...",
  className = "",
  autoFocus = false,
}: MessageInputProps) {
  const [value, setValue] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const formRef = useRef<HTMLFormElement>(null);
  
  // Submit handler
  const handleSubmit = useCallback((e?: FormEvent) => {
    e?.preventDefault();
    
    const trimmedValue = value.trim();
    if (!trimmedValue || disabled || isLoading) return;
    
    onSend(trimmedValue);
    setValue("");
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    
    // Refocus
    textareaRef.current?.focus();
  }, [value, disabled, isLoading, onSend]);
  
  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [value]);
  
  // Handle keyboard shortcuts
  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);
  
  // Determine if submit should be disabled
  const isSubmitDisabled = disabled || isLoading || !value.trim();
  
  return (
    <form 
      ref={formRef}
      onSubmit={handleSubmit}
      className={cn(
        "flex items-end gap-2 p-4 border-t bg-background",
        isFocused && "bg-accent/5",
        className
      )}
    >
      <div className="flex-1 relative">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="min-h-[44px] max-h-[200px] resize-none pr-12"
          autoFocus={autoFocus}
        />
        <div className={cn(
          "absolute right-2 bottom-2 transition-opacity",
          isSubmitDisabled ? "opacity-50" : "opacity-100"
        )}>
          <Button
            type="submit"
            size="icon"
            variant="ghost"
            className="h-8 w-8"
            disabled={isSubmitDisabled}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
      <Button 
        type="submit" 
        size="icon"
        className="shrink-0 h-11 w-11 hidden sm:flex"
        disabled={isSubmitDisabled}
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </Button>
    </form>
  );
}
