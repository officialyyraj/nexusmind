"use client";

import { Component, type ReactNode } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <ErrorFallback
          error={this.state.error}
          onRetry={this.handleRetry}
        />
      );
    }

    return this.props.children;
  }
}

interface ErrorFallbackProps {
  error: Error | null;
  onRetry: () => void;
}

export function ErrorFallback({ error, onRetry }: ErrorFallbackProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[400px] p-8 bg-background">
      <div className="max-w-md text-center space-y-6">
        <div className="mx-auto w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center">
          <AlertTriangle className="h-8 w-8 text-destructive" />
        </div>

        <div className="space-y-2">
          <h2 className="text-2xl font-semibold tracking-tight">
            Something went wrong
          </h2>
          <p className="text-sm text-muted-foreground">
            We encountered an unexpected error. This has been logged and we'll look into it.
          </p>
        </div>

        {error && (
          <details className="text-left p-4 rounded-lg bg-muted/50 border border-border">
            <summary className="text-sm font-medium cursor-pointer">
              Error Details
            </summary>
            <pre className="mt-2 text-xs text-muted-foreground overflow-auto max-h-32">
              {error.message}
              {"\n\n"}
              {error.stack}
            </pre>
          </details>
        )}

        <div className="flex gap-3 justify-center pt-4">
          <Button onClick={onRetry} variant="default">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
          <Button onClick={() => window.location.href = "/"} variant="outline">
            <Home className="h-4 w-4 mr-2" />
            Go Home
          </Button>
        </div>
      </div>
    </div>
  );
}

// Hook for component-level error handling
export function useErrorHandler() {
  const handleError = (error: Error) => {
    console.error("Handled error:", error);
    // Could dispatch to error reporting service
  };

  return handleError;
}

// Global error handler for unhandled promise rejections
export function setupGlobalErrorHandlers() {
  if (typeof window === "undefined") return;

  const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
    event.preventDefault();
    console.error("Unhandled promise rejection:", event.reason);
  };

  const handleError = (event: ErrorEvent) => {
    console.error("Global error:", event.error);
  };

  window.addEventListener("unhandledrejection", handleUnhandledRejection);
  window.addEventListener("error", handleError);

  return () => {
    window.removeEventListener("unhandledrejection", handleUnhandledRejection);
    window.removeEventListener("error", handleError);
  };
}
