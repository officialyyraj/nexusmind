"use client";

import { useState } from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { WorkflowGraph } from "./workflow-graph";
import { AgentInspectorPanel } from "./agent-inspector";
import { ExecutionTimeline } from "./execution-timeline";
import { LogCorrelationPanel } from "./log-correlation";
import { WorkflowOverview } from "./workflow-overview";
import { useWorkflowStore } from "@/lib/stores/workflow";
import { cn } from "@/lib/utils";
import {
  BarChart3,
  GitBranch,
  ScrollText,
  ListFilter,
  X,
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

type ViewMode = "graph" | "overview";

interface WorkflowPageProps {
  className?: string;
}

export function WorkflowPage({ className }: WorkflowPageProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("graph");
  const [showRightPanel, setShowRightPanel] = useState(true);
  const [showBottomPanel, setShowBottomPanel] = useState(true);
  const [activeBottomTab, setActiveBottomTab] = useState<"timeline" | "logs">("timeline");
  const [activeRightTab, setActiveRightTab] = useState<"inspector" | "overview">("inspector");
  
  const { selectedNodeId, selectedAgent, selectNode, selectAgent } = useWorkflowStore();

  return (
    <div className={cn("flex flex-col h-full bg-gray-900", className)}>
      <PanelGroup direction="vertical" className="flex-1">
        {/* Main Content Area */}
        <Panel defaultSize={70} minSize={30}>
          <PanelGroup direction="horizontal">
            {/* Left/Bottom Panel - Graph or Overview */}
            <Panel defaultSize={showRightPanel ? 75 : 100} minSize={40}>
              <div className="h-full flex flex-col">
                {/* View Mode Tabs */}
                <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700 bg-gray-800">
                  <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as ViewMode)}>
                    <TabsList className="h-8">
                      <TabsTrigger value="graph" className="text-xs data-[state=active]:bg-gray-700">
                        <GitBranch className="h-3 w-3 mr-1" />
                        Graph
                      </TabsTrigger>
                      <TabsTrigger value="overview" className="text-xs data-[state=active]:bg-gray-700">
                        <BarChart3 className="h-3 w-3 mr-1" />
                        Overview
                      </TabsTrigger>
                    </TabsList>
                  </Tabs>
                  
                  <div className="flex items-center gap-2">
                    {selectedNodeId && (
                      <Badge variant="secondary" className="text-xs">
                        Node: {selectedNodeId}
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-4 w-4 ml-1"
                          onClick={() => selectNode(null)}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </Badge>
                    )}
                  </div>
                </div>
                
                {/* Content */}
                <div className="flex-1 overflow-hidden">
                  {viewMode === "graph" ? (
                    <WorkflowGraph
                      onNodeSelect={(nodeId) => selectNode(nodeId)}
                    />
                  ) : (
                    <WorkflowOverview className="h-full overflow-y-auto" />
                  )}
                </div>
              </div>
            </Panel>

            {/* Right Panel - Inspector or Overview */}
            {showRightPanel && (
              <>
                <PanelResizeHandle className="w-1 bg-gray-700 hover:bg-blue-500 transition-colors cursor-col-resize" />
                
                <Panel defaultSize={25} minSize={15} maxSize={40}>
                  <div className="h-full border-l border-gray-700">
                    <Tabs value={activeRightTab} onValueChange={(v) => setActiveRightTab(v as typeof activeRightTab)}>
                      <TabsList className="w-full justify-start rounded-none border-b border-gray-700 h-9 bg-gray-900">
                        <TabsTrigger value="inspector" className="text-xs data-[state=active]:bg-gray-800">
                          <ListFilter className="h-3 w-3 mr-1" />
                          Inspector
                          {selectedAgent && <span className="ml-1 w-2 h-2 rounded-full bg-blue-500" />}
                        </TabsTrigger>
                        <TabsTrigger value="overview" className="text-xs data-[state=active]:bg-gray-800">
                          <BarChart3 className="h-3 w-3 mr-1" />
                          Stats
                        </TabsTrigger>
                      </TabsList>
                      
                      <TabsContent value="inspector" className="h-[calc(100%-37px)] m-0">
                        <AgentInspectorPanel
                          onClose={() => {
                            selectAgent(null);
                            selectNode(null);
                          }}
                        />
                      </TabsContent>
                      
                      <TabsContent value="overview" className="h-[calc(100%-37px)] m-0 overflow-y-auto">
                        <WorkflowOverview />
                      </TabsContent>
                    </Tabs>
                  </div>
                </Panel>
              </>
            )}
          </PanelGroup>
        </Panel>

        {/* Bottom Panel - Timeline and Logs */}
        {showBottomPanel && (
          <>
            <PanelResizeHandle className="h-1 bg-gray-700 hover:bg-blue-500 transition-colors cursor-row-resize" />
            
            <Panel defaultSize={30} minSize={15} maxSize={50}>
              <div className="h-full border-t border-gray-700">
                <Tabs value={activeBottomTab} onValueChange={(v) => setActiveBottomTab(v as typeof activeBottomTab)}>
                  <TabsList className="w-full justify-start rounded-none border-b border-gray-700 h-9 bg-gray-900">
                    <TabsTrigger value="timeline" className="text-xs data-[state=active]:bg-gray-800">
                      <ScrollText className="h-3 w-3 mr-1" />
                      Timeline
                    </TabsTrigger>
                    <TabsTrigger value="logs" className="text-xs data-[state=active]:bg-gray-800">
                      <ListFilter className="h-3 w-3 mr-1" />
                      Logs
                    </TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="timeline" className="h-[calc(100%-37px)] m-0">
                    <ExecutionTimeline />
                  </TabsContent>
                  
                  <TabsContent value="logs" className="h-[calc(100%-37px)] m-0">
                    <LogCorrelationPanel />
                  </TabsContent>
                </Tabs>
              </div>
            </Panel>
          </>
        )}
      </PanelGroup>

      {/* Toggle Buttons */}
      <div className="absolute bottom-4 right-4 flex items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          className="h-8 text-xs bg-gray-800 border-gray-700 hover:bg-gray-700"
          onClick={() => setShowBottomPanel(!showBottomPanel)}
        >
          {showBottomPanel ? <ScrollText className="h-3 w-3 mr-1" /> : null}
          {showBottomPanel ? "Hide" : "Show"} Timeline & Logs
        </Button>
        <Button
          variant="secondary"
          size="sm"
          className="h-8 text-xs bg-gray-800 border-gray-700 hover:bg-gray-700"
          onClick={() => setShowRightPanel(!showRightPanel)}
        >
          {showRightPanel ? <ListFilter className="h-3 w-3 mr-1" /> : null}
          {showRightPanel ? "Hide" : "Show"} Inspector
        </Button>
      </div>
    </div>
  );
}
