"use client";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useUIStore } from "@/lib/stores";
import { Moon, Sun, Monitor } from "lucide-react";

export default function SettingsPage() {
  const { theme, setTheme } = useUIStore();

  return (
    <AppShell>
      <div className="p-6 max-w-2xl mx-auto space-y-6">
        <h1 className="text-2xl font-bold">Settings</h1>
        <Card>
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Theme</Label>
              <div className="flex gap-2 mt-2">
                <Button variant={theme === "light" ? "default" : "outline"} size="lg" onClick={() => setTheme("light")}>
                  <Sun className="h-4 w-4 mr-2" />Light
                </Button>
                <Button variant={theme === "dark" ? "default" : "outline"} size="lg" onClick={() => setTheme("dark")}>
                  <Moon className="h-4 w-4 mr-2" />Dark
                </Button>
                <Button variant={theme === "system" ? "default" : "outline"} size="lg" onClick={() => setTheme("system")}>
                  <Monitor className="h-4 w-4 mr-2" />System
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>API Keys</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>OpenAI API Key</Label>
              <Input type="password" placeholder="sk-..." className="mt-1" />
            </div>
            <div>
              <Label>Anthropic API Key</Label>
              <Input type="password" placeholder="sk-ant-..." className="mt-1" />
            </div>
            <div>
              <Label>Ollama Endpoint</Label>
              <Input placeholder="http://localhost:11434" defaultValue="http://localhost:11434" className="mt-1" />
            </div>
            <Button>Save Changes</Button>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
