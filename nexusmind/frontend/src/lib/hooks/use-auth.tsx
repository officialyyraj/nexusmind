"use client";

import { useState, useEffect, createContext, useContext, useCallback } from "react";
import { setAuth, clearAuth, getToken, getStoredUser, type StoredUser } from "@/lib/auth";

interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
  is_active: boolean;
}

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;
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
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const refreshUser = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const token = getToken();
      if (!token) {
        setUser(null);
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }

      // Fetch current user from the API
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const response = await fetch(`${API_BASE}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        const user: User = {
          id: userData.id,
          email: userData.email,
          name: userData.name,
          is_active: userData.is_active,
        };
        setUser(user);
        setIsAuthenticated(true);
      } else if (response.status === 401) {
        // Token is invalid, clear it
        clearAuth();
        setUser(null);
        setIsAuthenticated(false);
      } else {
        throw new Error(`Failed to fetch user: ${response.status}`);
      }
    } catch (err) {
      // Network error or other issue - don't clear token, just set user as null
      setError((err as Error).message);
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Invalid email or password");
      }

      const data = await response.json();
      
      // Store the auth token and user data
      setAuth(data);
      
      // Update state
      const user: User = {
        id: data.user.id,
        email: data.user.email,
        name: data.user.name,
        is_active: data.user.is_active,
      };
      setUser(user);
      setIsAuthenticated(true);
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
      // Clear local storage
      clearAuth();
      
      // Update state
      setUser(null);
      setIsAuthenticated(false);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{ user, isLoading, error, isAuthenticated, login, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}