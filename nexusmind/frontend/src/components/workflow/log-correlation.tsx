"use client";

import { useState, useMemo } from "react";
import { useWorkflowStore } from "@/lib/stores/workflow";
import { cn } from "@/lib/utils";
import {
  Search,
  FileCode,
  Database,
  Wrench,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  Info,
  AlertTriangle,
  XCircle,
  Filter,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import type { LogCorrelation as LogType, NodeStatus } from "@/types";

const levelIcons: Record<string, React.ElementType> = {
  debug: Info,
  info: Info,
  warn: AlertTriangle,
  error: XCircle,
};

const levelColors: Record<string, string> = {
  debug: "text-gray-400",
  info: "text-blue-400",
  warn: "text-yellow-400",
  error: "text-red-400",
};

const levelBgColors: Record<string, string> = {
  debug: "bg-gray-800",
  info: "bg-blue-900/30",
  warn: "bg-yellow-900/30",
  error: "bg-red-900/30",
};

interface LogCorrelationPanelProps {
  className?: string;
}

export function LogCorrelationPanel({ className }: LogCorrelationPanelProps) {
  const {
    logs,
    relatedLogs,
    selectedLogId,
    selectedNodeId,
    selectLog,
    filter,
    setFilter,
  } = useWorkflowStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set());
  const [showFilters, setShowFilters] = useState(false);

  const displayLogs = selectedNodeId ? relatedLogs : logs;

  const filteredLogs = useMemo(() => {
    return displayLogs.filter((log) => {
      // Search filter
      if (searchQuery && !log.message.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      // Status filter
      if (filter.statuses && filter.statuses.length > 0) {
        // We'd need to add status to LogCorrelation
      }
      return true;
    });
  }, [displayLogs, searchQuery, filter]);

  const toggleLogExpanded = (logId: string) => {
    setExpandedLogs((prev) => {
      const next = new Set(prev);
      if (next.has(logId)) {
        next.delete(logId);
      } else {
        next.add(logId);
      }
      return next;
    });
  };

  // Group logs by node
  const groupedLogs = useMemo(() => {
    const groups: Record<string, LogType[]> = {};
    filteredLogs.forEach((log) => {
      if (!groups[log.nodeId]) {
        groups[log.nodeId] = [];
      }
      groups[log.nodeId].push(log);
    });
    return groups;
  }, [filteredLogs]);

  return (
    <div className={cn("flex flex-col h-full bg-gray-900 border-t border-gray-700", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-medium text-white">Log Correlation</h3>
          {selectedNodeId && (
            <Badge variant="secondary" className="text-xs">
              Related to selected node
            </Badge>
          )}
          <Badge variant="outline" className="text-xs">
            {filteredLogs.length} logs
          </Badge>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-gray-500" />
            <Input
              type="text"
              placeholder="Search logs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-7 pl-7 pr-3 text-xs w-48"
            />
          </div>
          
          {/* Filter */}
          <DropdownMenu open={showFilters} onOpenChange={setShowFilters}>
            <DropdownMenuTrigger>
              <Button variant="ghost" size="icon" className="h-7 w-7">
                <Filter className="h-3 w-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent  className="w-48">
              <DropdownMenuLabel>Filter by Level</DropdownMenuLabel>
              <DropdownMenuCheckboxItem checked>
                Debug
              </DropdownMenuCheckboxItem>
              <DropdownMenuCheckboxItem checked>
                Info
              </DropdownMenuCheckboxItem>
              <DropdownMenuCheckboxItem checked>
                Warning
              </DropdownMenuCheckboxItem>
              <DropdownMenuCheckboxItem checked>
                Error
              </DropdownMenuCheckboxItem>
              <DropdownMenuSeparator />
              <DropdownMenuLabel>Related Items</DropdownMenuLabel>
              <DropdownMenuCheckboxItem checked>
                <FileCode className="h-3 w-3 mr-2" />
                Files
              </DropdownMenuCheckboxItem>
              <DropdownMenuCheckboxItem checked>
                <Database className="h-3 w-3 mr-2" />
                Memory
              </DropdownMenuCheckboxItem>
              <DropdownMenuCheckboxItem checked>
                <Wrench className="h-3 w-3 mr-2" />
                Tools
              </DropdownMenuCheckboxItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Log List */}
      <ScrollArea className="flex-1">
        {filteredLogs.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <AlertCircle className="h-8 w-8 mx-auto mb-2 text-gray-600" />
              <p className="text-sm">No logs available</p>
              <p className="text-xs text-gray-600 mt-1">Logs will appear as workflow executes</p>
            </div>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {Object.entries(groupedLogs).map(([nodeId, nodeLogs]) => (
              <div key={nodeId} className="space-y-1">
                {/* Node Header */}
                <div className="px-2 py-1 text-xs font-medium text-gray-400 bg-gray-800/50 rounded">
                  {nodeLogs[0].nodeName}
                </div>
                
                {/* Logs */}
                {nodeLogs.map((log) => {
                  const Icon = levelIcons[log.level] || Info;
                  const isExpanded = expandedLogs.has(log.logId);
                  const isSelected = selectedLogId === log.logId;
                  
                  return (
                    <div
                      key={log.logId}
                      className={cn(
                        "rounded-lg overflow-hidden transition-colors",
                        levelBgColors[log.level],
                        isSelected && "ring-1 ring-blue-500"
                      )}
                    >
                      <div
                        className="flex items-start gap-2 px-2 py-1.5 cursor-pointer hover:bg-gray-700/50"
                        onClick={() => {
                          selectLog(log.logId === selectedLogId ? null : log.logId);
                        }}
                      >
                        <Icon className={cn("h-3 w-3 mt-0.5 flex-shrink-0", levelColors[log.level])} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-400">{formatTime(log.timestamp)}</span>
                            <Badge variant="outline" className="text-xs capitalize">
                              {log.level}
                            </Badge>
                          </div>
                          <p className="text-xs text-gray-200 mt-0.5 truncate">
                            {log.message}
                          </p>
                        </div>
                        {(log.relatedFiles?.length || log.relatedMemory?.length || log.relatedTools?.length) && (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-5 w-5 flex-shrink-0"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleLogExpanded(log.logId);
                            }}
                          >
                            {isExpanded ? (
                              <ChevronDown className="h-3 w-3" />
                            ) : (
                              <ChevronRight className="h-3 w-3" />
                            )}
                          </Button>
                        )}
                      </div>
                      
                      {/* Expanded Details */}
                      {isExpanded && (
                        <div className="px-2 pb-2 pt-0 space-y-2">
                          {/* Related Files */}
                          {log.relatedFiles && log.relatedFiles.length > 0 && (
                            <div className="flex items-start gap-2">
                              <FileCode className="h-3 w-3 mt-0.5 text-gray-500 flex-shrink-0" />
                              <div className="flex flex-wrap gap-1">
                                {log.relatedFiles.map((file, i) => (
                                  <Badge key={i} variant="secondary" className="text-xs">
                                    {file}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Related Memory */}
                          {log.relatedMemory && log.relatedMemory.length > 0 && (
                            <div className="flex items-start gap-2">
                              <Database className="h-3 w-3 mt-0.5 text-gray-500 flex-shrink-0" />
                              <div className="flex flex-wrap gap-1">
                                {log.relatedMemory.map((mem, i) => (
                                  <Badge key={i} variant="secondary" className="text-xs">
                                    {mem}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Related Tools */}
                          {log.relatedTools && log.relatedTools.length > 0 && (
                            <div className="flex items-start gap-2">
                              <Wrench className="h-3 w-3 mt-0.5 text-gray-500 flex-shrink-0" />
                              <div className="flex flex-wrap gap-1">
                                {log.relatedTools.map((tool, i) => (
                                  <Badge key={i} variant="secondary" className="text-xs">
                                    {tool}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}

// Helper function
function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
