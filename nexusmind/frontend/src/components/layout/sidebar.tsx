"use client";
import { usePanelsStore } from "@/lib/stores";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { SessionsList } from "@/components/dashboard/sessions-list";
import { ProjectsList } from "@/components/dashboard/projects-list";
import { FileExplorer } from "@/components/workspace/file-explorer";
import { MemoryExplorer } from "@/components/memory/memory-explorer";

export function Sidebar() {
  const { sidebarTab, setSidebarTab } = usePanelsStore();

  return (
    <div className="h-full border-r bg-card flex flex-col">
      <Tabs value={sidebarTab} onValueChange={(v) => setSidebarTab(v)} className="flex-1 flex flex-col">
        <TabsList className="w-full justify-start rounded-none border-b px-2">
          <TabsTrigger value="sessions">Sessions</TabsTrigger>
          <TabsTrigger value="projects">Projects</TabsTrigger>
          <TabsTrigger value="files">Files</TabsTrigger>
          <TabsTrigger value="memory">Memory</TabsTrigger>
        </TabsList>
        <ScrollArea className="flex-1">
          <TabsContent value="sessions" className="m-0 p-2"><SessionsList /></TabsContent>
          <TabsContent value="projects" className="m-0 p-2"><ProjectsList /></TabsContent>
          <TabsContent value="files" className="m-0 p-2"><FileExplorer /></TabsContent>
          <TabsContent value="memory" className="m-0 p-2"><MemoryExplorer /></TabsContent>
        </ScrollArea>
      </Tabs>
    </div>
  );
}
