"use client";

import { useCallback, useState, useMemo } from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { WorkspaceEditor } from "./monaco-editor";
import { DiffViewer } from "./diff-viewer";
import { ArtifactViewer } from "./artifact-viewer";
import { WorkspaceSearch } from "./workspace-search";
import { TabBar } from "./tab-bar";
import { FileExplorer } from "./file-explorer";
import { useWorkspaceStore, type WorkspaceFile, type EditorTab } from "@/lib/stores/workspace";
import { cn } from "@/lib/utils";
import {
  FileCode,
  GitCompare,
  Search,
  FileText,
  X,
  PanelLeftClose,
  PanelLeft,
  PanelRightClose,
  PanelRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ErrorFallback } from "@/components/shared/error-boundary";
import { EmptyState } from "@/components/shared/skeleton";

interface WorkspaceProps {
  className?: string;
  showSidebar?: boolean;
  showRightPanel?: boolean;
  defaultSidebarWidth?: number;
  defaultRightPanelWidth?: number;
}

export function Workspace({
  className,
  showSidebar = true,
  showRightPanel = false,
  defaultSidebarWidth = 280,
  defaultRightPanelWidth = 320,
}: WorkspaceProps) {
  const {
    tabs,
    activeTabId,
    openTab,
    openFile,
    setActiveTab,
    closeTab,
  } = useWorkspaceStore();

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(!showRightPanel);
  const [activePanel, setActivePanel] = useState<"explorer" | "search" | "mcp">("explorer");

  const activeTab = tabs.find((t) => t.id === activeTabId);

  // Responsive sizes based on viewport
  const panelSizes = useMemo(() => ({
    sidebar: sidebarCollapsed ? 0 : (typeof window !== "undefined" && window.innerWidth < 1024 ? 0 : 20),
    content: typeof window !== "undefined" && window.innerWidth < 1024 ? 100 : 80,
    right: rightPanelCollapsed ? 0 : (typeof window !== "undefined" && window.innerWidth < 1024 ? 0 : 20),
  }), [sidebarCollapsed, rightPanelCollapsed]);

  const handleOpenFile = useCallback((file: WorkspaceFile) => {
    openFile(file);
  }, [openFile]);

  const handleOpenDiff = useCallback((original: string, modified: string, title: string) => {
    const tabId = `diff-${Date.now()}`;
    openTab({
      id: tabId,
      title: title || "Diff",
      type: "diff",
      pinned: false,
      closable: true,
      diffOriginal: original,
      diffModified: modified,
    });
  }, [openTab]);

  const handleOpenPreview = useCallback((content: string, type: "markdown" | "html" | "json" | "yaml" | "image" | "svg" | "pdf" | "mermaid" | "text", title: string) => {
    const tabId = `preview-${Date.now()}`;
    openTab({
      id: tabId,
      title: title || "Preview",
      type: "preview",
      pinned: false,
      closable: true,
      data: { content, type },
    });
  }, [openTab]);

  const handleCloseTab = useCallback((tabId: string) => {
    closeTab(tabId);
  }, [closeTab]);

  const renderContent = () => {
    if (!activeTab) {
      return (
        <EmptyState
          icon={<FileCode className="h-16 w-16 text-gray-600" />}
          title="No file open"
          description="Select a file from the explorer or create a new one"
          action={
            <Button variant="outline" size="sm">
              Create New File
            </Button>
          }
        />
      );
    }

    try {
      switch (activeTab.type) {
        case "editor":
          return <WorkspaceEditor />;
        case "diff":
          return <DiffViewer />;
        case "preview":
          return (
            <ArtifactViewer
              content={activeTab.data?.content as string}
              type={activeTab.data?.type as "markdown" | "html" | "json" | "yaml" | "image" | "svg" | "pdf" | "mermaid" | "text"}
              title={activeTab.title}
            />
          );
        case "search":
          return <WorkspaceSearch />;
        default:
          return (
            <EmptyState
              icon={<FileText className="h-16 w-16 text-gray-600" />}
              title="Unsupported tab type"
              description={`Cannot display tab type: ${activeTab.type}`}
            />
          );
      }
    } catch (error) {
      return <ErrorFallback error={error as Error} onRetry={() => closeTab(activeTab.id)} />;
    }
  };

  return (
    <div className={cn("flex flex-col h-full bg-[#1e1e1e]", className)}>
      <PanelGroup direction="horizontal" className="flex-1">
        {/* Sidebar */}
        {showSidebar && (
          <>
            <Panel
              defaultSize={panelSizes.sidebar}
              minSize={typeof window !== "undefined" && window.innerWidth < 768 ? 0 : 10}
              maxSize={40}
              collapsible={true}
              collapsedSize={0}
            >
              <div className="flex flex-col h-full border-r border-[#3c3c3c]">
                {/* Sidebar Tabs */}
                <Tabs value={activePanel} onValueChange={(v) => setActivePanel(v as "explorer" | "search" | "mcp")}>
                  <TabsList className="w-full justify-start rounded-none bg-[#252526] h-10 border-b border-[#3c3c3c]">
                    <TabsTrigger 
                      value="explorer" 
                      className="text-xs data-[state=active]:bg-[#1e1e1e]"
                      aria-label="File Explorer"
                    >
                      <PanelLeft className="h-4 w-4 mr-1 hidden sm:inline" />
                      <span className="sr-only sm:not-sr-only">Files</span>
                    </TabsTrigger>
                    <TabsTrigger 
                      value="search" 
                      className="text-xs data-[state=active]:bg-[#1e1e1e]"
                      aria-label="Search"
                    >
                      <Search className="h-4 w-4 mr-1 hidden sm:inline" />
                      <span className="sr-only sm:not-sr-only">Search</span>
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="explorer" className="flex-1 m-0 overflow-hidden">
                    <FileExplorer
                      onFileOpen={handleOpenFile}
                      onFilePreview={(file) => handleOpenPreview(
                        file.content,
                        file.language as "markdown" | "html" | "json" | "yaml" | "image" | "svg" | "pdf" | "mermaid" | "text",
                        file.name
                      )}
                      onFileCompare={(file1, file2) => handleOpenDiff(file1.path, file2.path, `${file1.name} ↔ ${file2.name}`)}
                    />
                  </TabsContent>

                  <TabsContent value="search" className="flex-1 m-0 overflow-hidden">
                    <WorkspaceSearch />
                  </TabsContent>
                </Tabs>
              </div>
            </Panel>

            <PanelResizeHandle 
              className="w-1 bg-[#3c3c3c] hover:bg-[#007acc] transition-colors cursor-col-resize"
              aria-label="Resize sidebar"
            />
          </>
        )}

        {/* Main Content */}
        <Panel defaultSize={panelSizes.content} minSize={30}>
          <div className="flex flex-col h-full">
            {/* Tab Bar */}
            <TabBar
              onCloseOthers={(tabId) => {
                tabs.filter((t) => t.id !== tabId).forEach((t) => closeTab(t.id));
              }}
              onCloseAll={() => {
                tabs.forEach((t) => !t.pinned && closeTab(t.id));
              }}
            />

            {/* Editor Content */}
            <div className="flex-1 overflow-hidden">
              {renderContent()}
            </div>
          </div>
        </Panel>

        {/* Right Panel - Hidden on smaller screens */}
        {!rightPanelCollapsed && (
          <>
            <PanelResizeHandle 
              className="w-1 bg-[#3c3c3c] hover:bg-[#007acc] transition-colors cursor-col-resize"
              aria-label="Resize outline panel"
            />
            
            <Panel 
              defaultSize={panelSizes.right} 
              minSize={15} 
              maxSize={40}
              className="hidden lg:block"
            >
              <div className="flex flex-col h-full border-l border-[#3c3c3c] bg-[#252526]">
                <div className="flex items-center justify-between px-4 py-2 border-b border-[#3c3c3c]">
                  <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Outline
                  </span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => setRightPanelCollapsed(true)}
                    aria-label="Close outline panel"
                  >
                    <PanelRightClose className="h-4 w-4" />
                  </Button>
                </div>
                <ScrollArea className="flex-1">
                  <div className="p-4 text-sm text-gray-400">
                    {activeTab?.type === "editor" ? (
                      <div className="space-y-2">
                        <p className="text-xs text-muted-foreground mb-4">FILE OUTLINE</p>
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 text-xs cursor-pointer hover:text-white" role="button" tabIndex={0}>
                            <span className="text-blue-400">TF</span>
                            <span>function Component</span>
                          </div>
                          <div className="flex items-center gap-2 text-xs cursor-pointer hover:text-white pl-4" role="button" tabIndex={0}>
                            <span className="text-blue-400">T</span>
                            <span>useState</span>
                          </div>
                          <div className="flex items-center gap-2 text-xs cursor-pointer hover:text-white pl-4" role="button" tabIndex={0}>
                            <span className="text-blue-400">T</span>
                            <span>useCallback</span>
                          </div>
                          <div className="flex items-center gap-2 text-xs cursor-pointer hover:text-white" role="button" tabIndex={0}>
                            <span className="text-green-400">C</span>
                            <span>const handleClick</span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-gray-500">Open a file to see its outline</p>
                    )}
                  </div>
                </ScrollArea>
              </div>
            </Panel>
          </>
        )}
      </PanelGroup>

      {/* Sidebar Toggle - Responsive */}
      {showSidebar && (
        <Button
          variant="ghost"
          size="icon"
          className={cn(
            "absolute z-10 h-8 w-8 bg-[#252526] border border-[#3c3c3c] transition-opacity",
            sidebarCollapsed ? "opacity-100" : "opacity-0 hover:opacity-100",
            "top-2 left-2"
          )}
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          aria-label={sidebarCollapsed ? "Show sidebar" : "Hide sidebar"}
        >
          {sidebarCollapsed ? (
            <PanelLeft className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
        </Button>
      )}

      {/* Right Panel Toggle - Responsive */}
      {!rightPanelCollapsed && (
        <Button
          variant="ghost"
          size="icon"
          className={cn(
            "absolute z-10 h-8 w-8 bg-[#252526] border border-[#3c3c3c] transition-opacity",
            "top-2 right-2 hidden lg:flex"
          )}
          onClick={() => setRightPanelCollapsed(true)}
          aria-label="Close outline panel"
        >
          <PanelRightClose className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
