"use client";

import { useUIStore } from "@/lib/stores";
import { Command } from "cmdk";
import { useEffect, useState, useCallback, useMemo } from "react";
import { useTheme } from "next-themes";
import { useRouter } from "next/navigation";
import {
  Search,
  FolderOpen,
  MessageSquare,
  Settings,
  Plus,
  Moon,
  Sun,
  Monitor,
  Terminal,
  LayoutDashboard,
  FileCode,
  PanelLeftClose,
  PanelRightClose,
  Play,
  Square,
  RotateCcw,
  Keyboard,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";

export interface CommandItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  shortcut?: string;
  category?: string;
  action: () => void;
  disabled?: boolean;
}

export function CommandPalette() {
  const router = useRouter();
  const { commandPaletteOpen, toggleCommandPalette, toggleSidebar, toggleTerminal } = useUIStore();
  const { theme, setTheme } = useTheme();
  const [search, setSearch] = useState("");

  // Handle keyboard shortcut
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        toggleCommandPalette();
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [toggleCommandPalette]);

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && commandPaletteOpen) {
        toggleCommandPalette();
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [commandPaletteOpen, toggleCommandPalette]);

  // Reset search when opening
  useEffect(() => {
    if (commandPaletteOpen) {
      setSearch("");
    }
  }, [commandPaletteOpen]);

  // Define commands
  const commands = useMemo<CommandItem[]>(() => [
    // Navigation
    {
      id: "nav-dashboard",
      label: "Go to Dashboard",
      icon: <LayoutDashboard className="h-4 w-4" />,
      shortcut: "Ctrl+Shift+D",
      category: "Navigation",
      action: () => router.push("/"),
    },
    {
      id: "nav-chat",
      label: "Go to Chat",
      icon: <MessageSquare className="h-4 w-4" />,
      shortcut: "Ctrl+Shift+C",
      category: "Navigation",
      action: () => router.push("/sessions"),
    },
    {
      id: "nav-settings",
      label: "Go to Settings",
      icon: <Settings className="h-4 w-4" />,
      shortcut: "Ctrl+,",
      category: "Navigation",
      action: () => router.push("/settings"),
    },
    // Sessions
    {
      id: "session-new",
      label: "New Session",
      icon: <Plus className="h-4 w-4" />,
      shortcut: "Ctrl+Shift+N",
      category: "Sessions",
      action: () => {
        toggleCommandPalette();
        router.push("/sessions");
      },
    },
    // View
    {
      id: "view-sidebar",
      label: "Toggle Sidebar",
      icon: <PanelLeftClose className="h-4 w-4" />,
      shortcut: "Ctrl+B",
      category: "View",
      action: () => toggleSidebar(),
    },
    {
      id: "view-terminal",
      label: "Toggle Terminal",
      icon: <Terminal className="h-4 w-4" />,
      shortcut: "Ctrl+`",
      category: "View",
      action: () => toggleTerminal(),
    },
    // Appearance
    {
      id: "theme-dark",
      label: "Dark Mode",
      icon: <Moon className="h-4 w-4" />,
      category: "Appearance",
      action: () => setTheme("dark"),
      disabled: theme === "dark",
    },
    {
      id: "theme-light",
      label: "Light Mode",
      icon: <Sun className="h-4 w-4" />,
      category: "Appearance",
      action: () => setTheme("light"),
      disabled: theme === "light",
    },
    {
      id: "theme-system",
      label: "System Theme",
      icon: <Monitor className="h-4 w-4" />,
      category: "Appearance",
      action: () => setTheme("system"),
      disabled: theme === "system",
    },
    // Workflow
    {
      id: "workflow-start",
      label: "Start Workflow",
      icon: <Play className="h-4 w-4" />,
      shortcut: "F5",
      category: "Workflow",
      action: () => {
        // Start workflow action
      },
    },
    {
      id: "workflow-stop",
      label: "Stop Workflow",
      icon: <Square className="h-4 w-4" />,
      shortcut: "Shift+F5",
      category: "Workflow",
      action: () => {
        // Stop workflow action
      },
    },
    {
      id: "workflow-restart",
      label: "Restart Workflow",
      icon: <RotateCcw className="h-4 w-4" />,
      shortcut: "Ctrl+Shift+F5",
      category: "Workflow",
      action: () => {
        // Restart workflow action
      },
    },
  ], [router, theme, setTheme, toggleSidebar, toggleTerminal]);

  // Filter commands based on search
  const filteredCommands = useMemo(() => {
    if (!search) return commands;
    const lowerSearch = search.toLowerCase();
    return commands.filter(
      (cmd) =>
        cmd.label.toLowerCase().includes(lowerSearch) ||
        cmd.category?.toLowerCase().includes(lowerSearch)
    );
  }, [commands, search]);

  // Group commands by category
  const groupedCommands = useMemo(() => {
    const groups: Record<string, CommandItem[]> = {};
    for (const cmd of filteredCommands) {
      const category = cmd.category || "General";
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(cmd);
    }
    return groups;
  }, [filteredCommands]);

  // Handle command selection
  const handleSelect = useCallback((command: CommandItem) => {
    if (!command.disabled) {
      command.action();
      toggleCommandPalette();
    }
  }, [toggleCommandPalette]);

  if (!commandPaletteOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 animate-in fade-in duration-200"
      onClick={toggleCommandPalette}
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
    >
      <div
        className="fixed left-1/2 top-[20%] -translate-x-1/2 w-full max-w-lg animate-in fade-in slide-in-from-top-4 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        <Command className="bg-card border rounded-lg shadow-2xl overflow-hidden" loop>
          {/* Search input */}
          <div className="flex items-center border-b px-3">
            <Search className="h-4 w-4 mr-2 text-muted-foreground flex-shrink-0" />
            <Command.Input
              placeholder="Type a command or search..."
              className="flex-1 bg-transparent border-0 outline-none text-sm py-3 placeholder:text-muted-foreground"
              value={search}
              onValueChange={setSearch}
              autoFocus
              aria-label="Search commands"
            />
            <kbd className="hidden sm:inline-flex h-5 items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
              ESC
            </kbd>
          </div>

          {/* Command list */}
          <ScrollArea className="max-h-80 overflow-auto">
            <Command.List className="p-2">
              <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
                No results found. Try a different search.
              </Command.Empty>

              {Object.entries(groupedCommands).map(([category, categoryCommands]) => (
                <Command.Group
                  key={category}
                  heading={category}
                  className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground"
                >
                  {categoryCommands.map((cmd) => (
                    <Command.Item
                      key={cmd.id}
                      value={cmd.label}
                      onSelect={() => handleSelect(cmd)}
                      disabled={cmd.disabled}
                      className={cn(
                        "relative flex cursor-pointer select-none items-center rounded-md px-2 py-2 text-sm outline-none transition-colors",
                        "aria-selected:bg-accent aria-selected:text-accent-foreground",
                        "data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-50",
                        "hover:bg-accent/50"
                      )}
                    >
                      {cmd.icon && (
                        <span className="mr-3 flex h-5 w-5 items-center justify-center text-muted-foreground">
                          {cmd.icon}
                        </span>
                      )}
                      <span className="flex-1">{cmd.label}</span>
                      {cmd.shortcut && (
                        <kbd className="pointer-events-none hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex">
                          {cmd.shortcut}
                        </kbd>
                      )}
                    </Command.Item>
                  ))}
                </Command.Group>
              ))}
            </Command.List>
          </ScrollArea>

          {/* Footer */}
          <div className="flex items-center justify-between border-t px-3 py-2 text-xs text-muted-foreground">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="h-4 w-4 rounded border bg-muted px-1 font-mono text-[10px]">↑↓</kbd>
                <span>to navigate</span>
              </span>
              <span className="flex items-center gap-1">
                <kbd className="h-4 w-4 rounded border bg-muted px-1 font-mono text-[10px]">↵</kbd>
                <span>to select</span>
              </span>
            </div>
            <span className="flex items-center gap-1">
              <Keyboard className="h-3 w-3" />
              <span>Ctrl+K to toggle</span>
            </span>
          </div>
        </Command>
      </div>
    </div>
  );
}
