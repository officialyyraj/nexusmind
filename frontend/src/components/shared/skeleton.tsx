"use client";

import { cn } from "@/lib/utils";

// Base skeleton component
interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-muted",
        className
      )}
      role="status"
      aria-label="Loading..."
    />
  );
}

// File tree skeleton
export function FileTreeSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="space-y-1 p-2" role="status" aria-label="Loading file tree">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-2 px-2 py-1.5"
        >
          <Skeleton className="h-4 w-4 rounded" />
          <Skeleton
            className={cn(
              "h-4 rounded",
              i % 3 === 0 ? "w-32" : i % 3 === 1 ? "w-24" : "w-40"
            )}
          />
        </div>
      ))}
    </div>
  );
}

// Tab bar skeleton
export function TabBarSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="flex items-center gap-1 px-2 h-10" role="status" aria-label="Loading tabs">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn(
            "h-7 rounded-t",
            i === 0 ? "w-24" : i === 1 ? "w-32" : "w-28"
          )}
        />
      ))}
    </div>
  );
}

// Editor skeleton
export function EditorSkeleton() {
  return (
    <div className="flex flex-col h-full bg-[#1e1e1e]" role="status" aria-label="Loading editor">
      {/* Line numbers */}
      <div className="flex">
        <div className="w-12 flex-shrink-0 p-4 border-r border-[#3c3c3c]">
          {Array.from({ length: 15 }).map((_, i) => (
            <Skeleton key={i} className="h-4 w-4 mb-2" />
          ))}
        </div>
        {/* Code lines */}
        <div className="flex-1 p-4 space-y-2">
          {Array.from({ length: 15 }).map((_, i) => (
            <Skeleton
              key={i}
              className={cn(
                "h-4",
                i === 0 ? "w-full" :
                i === 1 ? "w-3/4" :
                i === 2 ? "w-1/2" :
                i === 3 ? "w-4/5" :
                i === 4 ? "w-2/3" :
                i === 5 ? "w-full" :
                i === 6 ? "w-1/3" :
                i === 7 ? "w-4/5" :
                i === 8 ? "w-1/2" :
                i === 9 ? "w-3/4" :
                i === 10 ? "w-full" :
                i === 11 ? "w-2/5" :
                i === 12 ? "w-4/5" :
                i === 13 ? "w-1/2" :
                "w-3/4"
              )}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// Chat message skeleton
export function ChatMessageSkeleton({ isUser = false }: { isUser?: boolean }) {
  return (
    <div
      className={cn(
        "flex gap-3 p-4",
        isUser && "flex-row-reverse"
      )}
      role="status"
      aria-label={isUser ? "Loading your message" : "Loading assistant message"}
    >
      <Skeleton className="h-8 w-8 rounded-full flex-shrink-0" />
      <div className={cn("space-y-2", isUser && "items-end")}>
        <Skeleton className={cn("h-4", isUser ? "w-24" : "w-48")} />
        <Skeleton className="h-20 w-64 rounded-lg" />
      </div>
    </div>
  );
}

// Card skeleton
export function CardSkeleton() {
  return (
    <div
      className="p-4 rounded-lg border border-border bg-card"
      role="status"
      aria-label="Loading card"
    >
      <Skeleton className="h-5 w-32 mb-3" />
      <Skeleton className="h-4 w-full mb-2" />
      <Skeleton className="h-4 w-3/4" />
    </div>
  );
}

// Dashboard skeleton
export function DashboardSkeleton() {
  return (
    <div className="space-y-6 p-6" role="status" aria-label="Loading dashboard">
      <div className="flex items-center justify-between">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-10 w-32" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-64 w-full rounded-lg" />
        </div>
        <div className="space-y-4">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-64 w-full rounded-lg" />
        </div>
      </div>
    </div>
  );
}

// Workflow skeleton
export function WorkflowSkeleton() {
  return (
    <div className="flex items-center justify-center h-full" role="status" aria-label="Loading workflow">
      <div className="space-y-4 text-center">
        <div className="flex justify-center gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex flex-col items-center gap-2">
              <Skeleton className="h-12 w-12 rounded-full" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </div>
        <Skeleton className="h-4 w-48 mx-auto" />
      </div>
    </div>
  );
}

// Sidebar skeleton
export function SidebarSkeleton() {
  return (
    <div className="space-y-4 p-4" role="status" aria-label="Loading sidebar">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton className="h-5 w-5 rounded" />
          <Skeleton className="h-4 w-24" />
        </div>
      ))}
    </div>
  );
}

// Generic loading spinner with optional text
interface LoadingSpinnerProps {
  text?: string;
  size?: "sm" | "md" | "lg";
}

export function LoadingSpinner({ text, size = "md" }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-8 w-8",
  };

  return (
    <div
      className="flex flex-col items-center justify-center gap-3"
      role="status"
      aria-label={text || "Loading"}
    >
      <div
        className={cn(
          "animate-spin rounded-full border-2 border-muted border-t-primary",
          sizeClasses[size]
        )}
      />
      {text && (
        <p className="text-sm text-muted-foreground">{text}</p>
      )}
    </div>
  );
}

// Full page loading state
interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = "Loading..." }: LoadingStateProps) {
  return (
    <div className="flex items-center justify-center h-full min-h-[200px]">
      <LoadingSpinner text={message} size="lg" />
    </div>
  );
}

// Empty state with icon and message
interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[200px] p-8 text-center">
      {icon && (
        <div className="mb-4 text-muted-foreground">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-medium mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground max-w-sm mb-4">
          {description}
        </p>
      )}
      {action}
    </div>
  );
}
