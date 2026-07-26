"use client";

import { createContext, useContext, useState, useCallback, useEffect } from "react";
import { cn } from "@/lib/utils";
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContextValue {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, "id">) => {
    const id = crypto.randomUUID();
    const newToast: Toast = { ...toast, id };
    setToasts((prev) => [...prev, newToast]);

    // Auto-remove after duration
    const duration = toast.duration ?? 5000;
    if (duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, duration);
    }
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
}

interface ToastContainerProps {
  toasts: Toast[];
  removeToast: (id: string) => void;
}

function ToastContainer({ toasts, removeToast }: ToastContainerProps) {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  );
}

interface ToastItemProps {
  toast: Toast;
  onClose: () => void;
}

function ToastItem({ toast, onClose }: ToastItemProps) {
  const icons = {
    success: <CheckCircle className="h-5 w-5 text-green-500" />,
    error: <AlertCircle className="h-5 w-5 text-red-500" />,
    warning: <AlertTriangle className="h-5 w-5 text-yellow-500" />,
    info: <Info className="h-5 w-5 text-blue-500" />,
  };

  const bgColors = {
    success: "bg-green-950 border-green-700",
    error: "bg-red-950 border-red-700",
    warning: "bg-yellow-950 border-yellow-700",
    info: "bg-blue-950 border-blue-700",
  };

  return (
    <div
      className={cn(
        "flex items-start gap-3 p-4 rounded-lg border shadow-lg animate-in slide-in-from-right",
        bgColors[toast.type]
      )}
      role="alert"
    >
      {icons[toast.type]}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white">{toast.title}</p>
        {toast.message && (
          <p className="mt-1 text-xs text-gray-300">{toast.message}</p>
        )}
      </div>
      <button
        onClick={onClose}
        className="flex-shrink-0 text-gray-400 hover:text-white"
        aria-label="Close"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

// Convenience functions for common toast types
export function toast(options: Omit<Toast, "id">) {
  // This is a simplified version - in real usage, you'd use the context
  console.warn("Toast called outside of provider:", options);
}

// Error banner component
interface ErrorBannerProps {
  error: string;
  onDismiss?: () => void;
  onRetry?: () => void;
}

export function ErrorBanner({ error, onDismiss, onRetry }: ErrorBannerProps) {
  return (
    <div className="flex items-center gap-3 p-4 bg-red-950 border border-red-700 rounded-lg">
      <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white">{error}</p>
      </div>
      <div className="flex items-center gap-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-3 py-1 text-xs font-medium text-white bg-red-700 hover:bg-red-600 rounded"
          >
            Retry
          </button>
        )}
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-gray-400 hover:text-white"
            aria-label="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}

// Connection status indicator
interface ConnectionStatusProps {
  status: "connecting" | "connected" | "disconnected" | "reconnecting" | "error";
  reconnectAttempt?: number;
}

export function ConnectionStatus({ status, reconnectAttempt }: ConnectionStatusProps) {
  const statusConfig = {
    connecting: {
      color: "bg-yellow-500",
      text: "Connecting...",
      icon: "animate-pulse",
    },
    connected: {
      color: "bg-green-500",
      text: "Connected",
      icon: "",
    },
    disconnected: {
      color: "bg-gray-500",
      text: "Disconnected",
      icon: "",
    },
    reconnecting: {
      color: "bg-yellow-500",
      text: `Reconnecting (${reconnectAttempt ?? 0})...`,
      icon: "animate-pulse",
    },
    error: {
      color: "bg-red-500",
      text: "Connection Error",
      icon: "",
    },
  };

  const config = statusConfig[status];

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className={cn("w-2 h-2 rounded-full", config.color, config.icon)} />
      <span className="text-gray-400">{config.text}</span>
    </div>
  );
}
