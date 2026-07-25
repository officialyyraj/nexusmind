"use client";
import { useUIStore } from "@/lib/stores";
import { Command } from "cmdk";
import { useEffect } from "react";
import { Search, FolderOpen, MessageSquare, Settings, Plus } from "lucide-react";

export function CommandPalette() {
  const { commandPaletteOpen, toggleCommandPalette } = useUIStore();
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
  if (!commandPaletteOpen) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/50" onClick={toggleCommandPalette}>
      <div className="fixed left-1/2 top-1/4 -translate-x-1/2 w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
        <Command className="bg-card border rounded-lg shadow-2xl">
          <div className="flex items-center border-b px-3">
            <Search className="h-4 w-4 mr-2 text-muted-foreground" />
            <Command.Input placeholder="Type a command or search..." className="flex-1 bg-transparent border-0 outline-none text-sm" />
          </div>
          <Command.List className="p-2 max-h-64 overflow-y-auto">
            <Command.Empty className="py-6 text-center text-sm text-muted-foreground">No results found.</Command.Empty>
            <Command.Group heading="Navigation">
              <Command.Item><FolderOpen className="h-4 w-4 mr-2" />Go to Dashboard</Command.Item>
              <Command.Item><MessageSquare className="h-4 w-4 mr-2" />Go to Chat</Command.Item>
              <Command.Item><Settings className="h-4 w-4 mr-2" />Go to Settings</Command.Item>
            </Command.Group>
            <Command.Group heading="Actions">
              <Command.Item><Plus className="h-4 w-4 mr-2" />New Session</Command.Item>
              <Command.Item><Plus className="h-4 w-4 mr-2" />New Project</Command.Item>
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
}
