"use client";

import { useEffect, useCallback, useRef, useState } from "react";

// Keyboard shortcut types
export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  metaKey?: boolean;
  description?: string;
}

export interface UseKeyboardShortcutOptions {
  enabled?: boolean;
  preventDefault?: boolean;
  ignoreInput?: boolean;
}

const defaultOptions: UseKeyboardShortcutOptions = {
  enabled: true,
  preventDefault: true,
  ignoreInput: true,
};

// Hook for handling keyboard shortcuts
export function useKeyboardShortcut(
  shortcut: KeyboardShortcut,
  callback: (event: KeyboardEvent) => void,
  options: UseKeyboardShortcutOptions = defaultOptions
) {
  const { enabled, preventDefault, ignoreInput } = { ...defaultOptions, ...options };
  const callbackRef = useRef(callback);

  // Update callback ref on each render
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled) return;

    const handler = (event: KeyboardEvent) => {
      // Check if we're in an input field
      if (ignoreInput) {
        const target = event.target as HTMLElement;
        const isInput = target.tagName === "INPUT" ||
                        target.tagName === "TEXTAREA" ||
                        target.isContentEditable;
        if (isInput) return;
      }

      // Check if shortcut matches
      const matches =
        event.key.toLowerCase() === shortcut.key.toLowerCase() &&
        !!shortcut.ctrlKey === (event.ctrlKey || event.metaKey) &&
        !!shortcut.shiftKey === event.shiftKey &&
        !!shortcut.altKey === event.altKey;

      if (matches) {
        if (preventDefault) {
          event.preventDefault();
        }
        callbackRef.current(event);
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [enabled, preventDefault, ignoreInput, shortcut]);
}

// Common shortcuts
export const SHORTCUTS = {
  // Command palette
  COMMAND_PALETTE: { key: "k", ctrlKey: true, description: "Open command palette" },
  
  // Quick open
  QUICK_OPEN: { key: "p", ctrlKey: true, description: "Quick open file" },
  
  // Command palette (alternate)
  COMMAND_PALETTE_ALT: { key: "p", ctrlKey: true, shiftKey: true, description: "Open command palette" },
  
  // Toggle sidebar
  TOGGLE_SIDEBAR: { key: "b", ctrlKey: true, description: "Toggle sidebar" },
  
  // Close tab
  CLOSE_TAB: { key: "w", ctrlKey: true, description: "Close tab" },
  
  // Next tab
  NEXT_TAB: { key: "Tab", ctrlKey: true, description: "Next tab" },
  
  // Previous tab
  PREV_TAB: { key: "Tab", ctrlKey: true, shiftKey: true, description: "Previous tab" },
  
  // Toggle terminal
  TOGGLE_TERMINAL: { key: "`", ctrlKey: true, description: "Toggle terminal" },
  
  // Save
  SAVE: { key: "s", ctrlKey: true, description: "Save" },
  
  // Find
  FIND: { key: "f", ctrlKey: true, description: "Find" },
  
  // Replace
  REPLACE: { key: "h", ctrlKey: true, description: "Find and replace" },
  
  // Go to line
  GO_TO_LINE: { key: "g", ctrlKey: true, description: "Go to line" },
  
  // New file
  NEW_FILE: { key: "n", ctrlKey: true, description: "New file" },
  
  // Open file
  OPEN_FILE: { key: "o", ctrlKey: true, description: "Open file" },
  
  // Settings
  SETTINGS: { key: ",", ctrlKey: true, description: "Open settings" },
  
  // Toggle comment
  TOGGLE_COMMENT: { key: "/", ctrlKey: true, description: "Toggle line comment" },
  
  // Find next
  FIND_NEXT: { key: "f3", description: "Find next" },
  
  // Find previous
  FIND_PREV: { key: "f3", shiftKey: true, description: "Find previous" },
  
  // Escape
  ESCAPE: { key: "Escape", description: "Close dialog/menu" },
  
  // Arrow navigation
  ARROW_UP: { key: "ArrowUp", description: "Navigate up" },
  ARROW_DOWN: { key: "ArrowDown", description: "Navigate down" },
  ARROW_LEFT: { key: "ArrowLeft", description: "Navigate left" },
  ARROW_RIGHT: { key: "ArrowRight", description: "Navigate right" },
  
  // Enter
  ENTER: { key: "Enter", description: "Select/Confirm" },
  
  // Tab
  TAB: { key: "Tab", description: "Navigate/Indent" },
  
  // Help
  HELP: { key: "/", ctrlKey: true, shiftKey: true, description: "Show keyboard shortcuts" },
} as const;

// Focus management hook
export function useFocusManagement() {
  const [focusedElement, setFocusedElement] = useState<HTMLElement | null>(null);

  const focusNext = useCallback((container: HTMLElement) => {
    const focusableElements = container.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    if (document.activeElement === lastFocusable) {
      firstFocusable?.focus();
    } else {
      const nextElement = document.activeElement?.nextElementSibling as HTMLElement;
      nextElement?.focus();
    }
  }, []);

  const focusPrevious = useCallback((container: HTMLElement) => {
    const focusableElements = container.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    if (document.activeElement === firstFocusable) {
      lastFocusable?.focus();
    } else {
      const prevElement = document.activeElement?.previousElementSibling as HTMLElement;
      prevElement?.focus();
    }
  }, []);

  const trapFocus = useCallback((container: HTMLElement) => {
    const focusableElements = container.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;

      if (e.shiftKey) {
        if (document.activeElement === firstFocusable) {
          e.preventDefault();
          lastFocusable?.focus();
        }
      } else {
        if (document.activeElement === lastFocusable) {
          e.preventDefault();
          firstFocusable?.focus();
        }
      }
    };

    container.addEventListener("keydown", handleKeyDown);
    return () => container.removeEventListener("keydown", handleKeyDown);
  }, []);

  return {
    focusedElement,
    setFocusedElement,
    focusNext,
    focusPrevious,
    trapFocus,
  };
}

// List navigation hook
export function useListNavigation<T>(items: T[], options: {
  loop?: boolean;
  orientation?: "vertical" | "horizontal" | "both";
  onSelect?: (item: T, index: number) => void;
}) {
  const { loop = true, orientation = "vertical", onSelect } = options;
  const [focusedIndex, setFocusedIndex] = useState(-1);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (items.length === 0) return;

    switch (e.key) {
      case "ArrowDown":
        if (orientation === "vertical" || orientation === "both") {
          e.preventDefault();
          setFocusedIndex((prev) => {
            if (prev >= items.length - 1) {
              return loop ? 0 : prev;
            }
            return prev + 1;
          });
        }
        break;

      case "ArrowUp":
        if (orientation === "vertical" || orientation === "both") {
          e.preventDefault();
          setFocusedIndex((prev) => {
            if (prev <= 0) {
              return loop ? items.length - 1 : prev;
            }
            return prev - 1;
          });
        }
        break;

      case "ArrowRight":
        if (orientation === "horizontal" || orientation === "both") {
          e.preventDefault();
          setFocusedIndex((prev) => {
            if (prev >= items.length - 1) {
              return loop ? 0 : prev;
            }
            return prev + 1;
          });
        }
        break;

      case "ArrowLeft":
        if (orientation === "horizontal" || orientation === "both") {
          e.preventDefault();
          setFocusedIndex((prev) => {
            if (prev <= 0) {
              return loop ? items.length - 1 : prev;
            }
            return prev - 1;
          });
        }
        break;

      case "Enter":
        if (focusedIndex >= 0 && focusedIndex < items.length) {
          e.preventDefault();
          onSelect?.(items[focusedIndex], focusedIndex);
        }
        break;

      case "Home":
        e.preventDefault();
        setFocusedIndex(0);
        break;

      case "End":
        e.preventDefault();
        setFocusedIndex(items.length - 1);
        break;
    }
  }, [items, loop, orientation, focusedIndex, onSelect]);

  return {
    focusedIndex,
    setFocusedIndex,
    handleKeyDown,
    focusedItem: focusedIndex >= 0 ? items[focusedIndex] : undefined,
  };
}

// Escape handler hook
export function useEscapeHandler(callback: () => void, enabled = true) {
  useEffect(() => {
    if (!enabled) return;

    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        callback();
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [callback, enabled]);
}

// Global keyboard navigation provider
export function useGlobalKeyboard() {
  const shortcutsRef = useRef<Map<string, { shortcut: KeyboardShortcut; callback: () => void }>>(new Map());

  const registerShortcut = useCallback((id: string, shortcut: KeyboardShortcut, callback: () => void) => {
    shortcutsRef.current.set(id, { shortcut, callback });
  }, []);

  const unregisterShortcut = useCallback((id: string) => {
    shortcutsRef.current.delete(id);
  }, []);

  const isShortcutRegistered = useCallback((id: string) => {
    return shortcutsRef.current.has(id);
  }, []);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      const isInput = target.tagName === "INPUT" ||
                      target.tagName === "TEXTAREA" ||
                      target.isContentEditable;
      
      if (isInput) return;

      for (const { shortcut, callback } of shortcutsRef.current.values()) {
        const matches =
          event.key.toLowerCase() === shortcut.key.toLowerCase() &&
          !!shortcut.ctrlKey === (event.ctrlKey || event.metaKey) &&
          !!shortcut.shiftKey === event.shiftKey &&
          !!shortcut.altKey === event.altKey;

        if (matches) {
          event.preventDefault();
          callback();
          break;
        }
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return {
    registerShortcut,
    unregisterShortcut,
    isShortcutRegistered,
  };
}
