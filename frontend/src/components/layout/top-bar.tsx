"use client";
import { useUIStore } from "@/lib/stores";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CommandPalette } from "@/components/shared/command-palette";
import { Bell, Search, Moon, Sun } from "lucide-react";

export function TopBar() {
  const { theme, setTheme, toggleCommandPalette } = useUIStore();

  return (
    <header className="fixed top-0 left-0 right-0 h-12 border-b bg-card z-50 flex items-center px-4 gap-4">
      <div className="flex items-center gap-2">
        <span className="font-bold text-lg">NexusMind</span>
      </div>
      <Button variant="outline" size="sm" className="w-64 justify-start text-muted-foreground" onClick={toggleCommandPalette}>
        <Search className="h-4 w-4 mr-2" />
        Search or command...
        <kbd className="ml-auto text-xs">⌘K</kbd>
      </Button>
      <div className="flex-1" />
      <Badge variant="secondary">GPT-4o</Badge>
      <Badge variant="outline">3 Agents</Badge>
      <Button variant="ghost" size="icon"><Bell className="h-4 w-4" /></Button>
      <Button variant="ghost" size="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
        {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </Button>
      <CommandPalette />
    </header>
  );
}
