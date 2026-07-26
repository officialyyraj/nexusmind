"use client";

import { useState, useEffect, createContext, useContext } from "react";
import { api } from "@/lib/api/client";

interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
}

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    refreshUser();
  }, []);

  const refreshUser = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // In a real app, this would fetch the current user from the API
      // For now, we'll simulate a logged-in user
      const storedUser = localStorage.getItem("nexusmind_user");
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      } else {
        // Demo mode - set a mock user
        const demoUser: User = {
          id: "demo-user-1",
          email: "demo@example.com",
          name: "Demo User",
        };
        setUser(demoUser);
        localStorage.setItem("nexusmind_user", JSON.stringify(demoUser));
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      // In a real app, this would call the login API
      // For demo, we'll just set a mock user
      const demoUser: User = {
        id: "user-" + Date.now(),
        email,
        name: email.split("@")[0],
      };
      setUser(demoUser);
      localStorage.setItem("nexusmind_user", JSON.stringify(demoUser));
    } catch (err) {
      setError((err as Error).message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    setError(null);

    try {
      setUser(null);
      localStorage.removeItem("nexusmind_user");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{ user, isLoading, error, login, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}