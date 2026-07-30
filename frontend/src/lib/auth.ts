/**
 * Authentication utilities for JWT token management.
 * 
 * Uses localStorage for token storage in the browser.
 * Tokens are attached to API requests via the api client.
 */

const TOKEN_KEY = "nexusmind_auth_token";
const USER_KEY = "nexusmind_user";

export interface StoredUser {
  id: string;
  email: string;
  name?: string;
  is_active: boolean;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  user: StoredUser;
}

/**
 * Get the stored authentication token.
 */
export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Store the authentication token and user data.
 */
export function setAuth(data: AuthTokens): void {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.setItem(TOKEN_KEY, data.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(data.user));
}

/**
 * Clear the stored authentication token and user data.
 */
export function clearAuth(): void {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Get the stored user data.
 */
export function getStoredUser(): StoredUser | null {
  if (typeof window === "undefined") {
    return null;
  }
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) {
    return null;
  }
  try {
    return JSON.parse(userStr) as StoredUser;
  } catch {
    return null;
  }
}

/**
 * Check if the user is authenticated.
 */
export function isAuthenticated(): boolean {
  return !!getToken();
}
