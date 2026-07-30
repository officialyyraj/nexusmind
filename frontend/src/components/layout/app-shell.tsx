"use client";
import { usePanelsStore } from "@/lib/stores";
import { cn } from "@/lib/utils";
import { Sidebar } from "./sidebar";
import { TopBar } from "./top-bar";
import { RightSidebar } from "./right-sidebar";
import { BottomPanel } from "./bottom-panel";
import { PanelGroup, Panel, PanelResizeHandle } from "react-resizable-panels";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { sidebarCollapsed, rightPanelCollapsed, bottomPanelCollapsed, sidebarWidth, rightPanelWidth, bottomPanelHeight } = usePanelsStore();

  return (
    <div className="h-screen w-screen overflow-hidden bg-background">
      <TopBar />
      <PanelGroup direction="horizontal" className="flex-1 pt-12">
        {!sidebarCollapsed && (
          <>
            <Panel defaultSize={20} minSize={15} maxSize={35} className="flex-shrink-0">
              <Sidebar />
            </Panel>
            <PanelResizeHandle className="w-1 bg-border hover:bg-primary transition-colors cursor-col-resize" />
          </>
        )}
        <Panel defaultSize={60} minSize={30}>
          <PanelGroup direction="vertical">
            <Panel defaultSize={70} minSize={20}>
              {children}
            </Panel>
            {!bottomPanelCollapsed && (
              <>
                <PanelResizeHandle className="h-1 bg-border hover:bg-primary transition-colors cursor-row-resize" />
                <Panel defaultSize={30} minSize={10} maxSize={60} className="flex-shrink-0">
                  <BottomPanel />
                </Panel>
              </>
            )}
          </PanelGroup>
        </Panel>
        {!rightPanelCollapsed && (
          <>
            <PanelResizeHandle className="w-1 bg-border hover:bg-primary transition-colors cursor-col-resize" />
            <Panel defaultSize={20} minSize={15} maxSize={35} className="flex-shrink-0">
              <RightSidebar />
            </Panel>
          </>
        )}
      </PanelGroup>
    </div>
  );
}
