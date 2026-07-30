"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider, useAuth } from "@/lib/hooks/use-auth";
import { Loader2 } from "lucide-react";

// Routes that don't require authentication
const PUBLIC_ROUTES = ["/login", "/register"];

function ProtectedRoutesHandler({ children }: { children: ReactNode }) {
  const { isLoading, isAuthenticated } = useAuth();
  const pathname = usePathname();
  const [hasRedirected, setHasRedirected] = useState(false);

  // Don't redirect on public routes
  const isPublicRoute = PUBLIC_ROUTES.some((route) => pathname?.startsWith(route));

  // Show loading state while checking authentication (but not on public routes)
  if (isLoading && !hasRedirected && !isPublicRoute) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Redirect to login if not authenticated and not on public route
  if (!isAuthenticated && !isPublicRoute && pathname !== "/login") {
    // Use window.location for a full page redirect
    if (typeof window !== "undefined") {
      window.location.href = `/login?redirect=${encodeURIComponent(pathname || "/")}`;
      setHasRedirected(true);
    }
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // If authenticated but on login page, redirect to home
  if (isAuthenticated && isPublicRoute) {
    if (typeof window !== "undefined") {
      window.location.href = "/";
      setHasRedirected(true);
    }
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return <>{children}</>;
}

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: { staleTime: 60 * 1000, retry: 1 },
      mutations: { retry: 0 },
    },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
        <TooltipProvider delayDuration={0}>
          <AuthProvider>
            <ProtectedRoutesHandler>
              {children}
            </ProtectedRoutesHandler>
          </AuthProvider>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
