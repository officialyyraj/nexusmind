"use client";
import { usePanelsStore } from "@/lib/stores";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Terminal } from "@/components/workspace/terminal";
import { LogViewer } from "@/components/workspace/log-viewer";
import { DockerPanel } from "@/components/workspace/docker-panel";

export function BottomPanel() {
  const { bottomPanelTab, setBottomPanelTab, toggleBottomPanel } = usePanelsStore();

  return (
    <div className="h-full border-t bg-card flex flex-col">
      <div className="flex items-center justify-between border-b">
        <Tabs value={bottomPanelTab} onValueChange={setBottomPanelTab}>
          <TabsList className="h-8">
            <TabsTrigger value="terminal" className="h-7 text-xs">Terminal</TabsTrigger>
            <TabsTrigger value="logs" className="h-7 text-xs">Logs</TabsTrigger>
            <TabsTrigger value="docker" className="h-7 text-xs">Docker</TabsTrigger>
          </TabsList>
        </Tabs>
        <Button variant="ghost" size="icon" onClick={toggleBottomPanel}>×</Button>
      </div>
      <div className="flex-1 overflow-hidden">
        {bottomPanelTab === "terminal" && <Terminal />}
        {bottomPanelTab === "logs" && <LogViewer />}
        {bottomPanelTab === "docker" && <DockerPanel />}
      </div>
    </div>
  );
}
