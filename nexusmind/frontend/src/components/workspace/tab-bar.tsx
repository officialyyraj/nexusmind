"use client";

import { useCallback, useMemo, useState, useRef, useEffect } from "react";
import { useDraggable, useDroppable, DndContext, DragEndEvent, closestCenter } from "@dnd-kit/core";
import { SortableContext, horizontalListSortingStrategy, useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  X,
  Pin,
  PinOff,
  MoreHorizontal,
  SplitSquareHorizontal,
  File,
  MessageSquare,
  GitBranch,
  Terminal,
  FileText,
  Eye,
  GitCompare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { useWorkspaceStore, type EditorTab } from "@/lib/stores/workspace";

interface TabBarProps {
  className?: string;
  onCloseOthers?: (tabId: string) => void;
  onCloseAll?: () => void;
  onSplitEditor?: (tabId: string) => void;
}

function SortableTab({
  tab,
  isActive,
  onClick,
  onClose,
  onPin,
  onUnpin,
  onContextMenu,
  tabIndex,
  isFocused,
  onKeyDown,
}: {
  tab: EditorTab;
  isActive: boolean;
  onClick: () => void;
  onClose: (e: React.MouseEvent) => void;
  onPin: () => void;
  onUnpin: () => void;
  onContextMenu: (e: React.MouseEvent) => void;
  tabIndex: number;
  isFocused: boolean;
  onKeyDown: (e: React.KeyboardEvent) => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: tab.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const getIcon = () => {
    switch (tab.type) {
      case "editor":
        return <File className="h-3 w-3" />;
      case "chat":
        return <MessageSquare className="h-3 w-3" />;
      case "workflow":
        return <GitBranch className="h-3 w-3" />;
      case "terminal":
        return <Terminal className="h-3 w-3" />;
      case "preview":
        return <Eye className="h-3 w-3" />;
      case "diff":
        return <GitCompare className="h-3 w-3" />;
      default:
        return <FileText className="h-3 w-3" />;
    }
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={cn(
        "group flex items-center gap-1.5 px-3 py-1.5 text-sm cursor-pointer transition-all border-r border-[#3c3c3c]",
        "hover:bg-[#2a2d2e]",
        isActive && "bg-[#1e1e1e] border-t-2 border-t-[#007acc]",
        isDragging && "opacity-50",
        tab.pinned && "bg-[#252526]",
        isFocused && "ring-2 ring-[#007acc] ring-inset"
      )}
      onClick={onClick}
      onContextMenu={onContextMenu}
      onKeyDown={onKeyDown}
      tabIndex={isFocused ? 0 : -1}
      role="tab"
      aria-selected={isActive}
      aria-label={`${tab.title}${tab.pinned ? " (pinned)" : ""}`}
    >
      {getIcon()}
      <span className="truncate max-w-[120px]">{tab.title}</span>
      
      {(tab.data?.modified as boolean) && (
        <span className="w-2 h-2 rounded-full bg-[#e8ab53]" aria-label="Modified" />
      )}

      {/* Tab Actions */}
      <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
        {tab.pinned ? (
          <Button
            variant="ghost"
            size="icon"
            className="h-5 w-5 text-yellow-500 hover:text-yellow-400"
            onClick={(e) => {
              e.stopPropagation();
              onUnpin();
            }}
            aria-label={`Unpin ${tab.title}`}
          >
            <Pin className="h-3 w-3" />
          </Button>
        ) : (
          <Button
            variant="ghost"
            size="icon"
            className="h-5 w-5 text-gray-400 hover:text-white"
            onClick={(e) => {
              e.stopPropagation();
              onPin();
            }}
            aria-label={`Pin ${tab.title}`}
          >
            <PinOff className="h-3 w-3" />
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="h-5 w-5 text-gray-400 hover:text-white"
          onClick={onClose}
          aria-label={`Close ${tab.title}`}
        >
          <X className="h-3 w-3" />
        </Button>
      </div>
    </div>
  );
}

export function TabBar({
  className,
  onCloseOthers,
  onCloseAll,
  onSplitEditor,
}: TabBarProps) {
  const {
    tabs,
    activeTabId,
    setActiveTab,
    closeTab,
    pinTab,
    unpinTab,
    reorderTabs,
  } = useWorkspaceStore();

  const [contextMenuTab, setContextMenuTab] = useState<string | null>(null);
  const [showOverflowMenu, setShowOverflowMenu] = useState(false);
  const [focusedTabIndex, setFocusedTabIndex] = useState<number>(-1);
  const tabBarRef = useRef<HTMLDivElement>(null);

  // Keyboard navigation handler
  const handleTabKeyDown = useCallback((e: React.KeyboardEvent, index: number, allTabs: EditorTab[]) => {
    const currentTab = allTabs[index];
    
    switch (e.key) {
      case "ArrowLeft":
        e.preventDefault();
        if (index > 0) {
          setFocusedTabIndex(index - 1);
          const prevTab = allTabs[index - 1];
          if (prevTab) setActiveTab(prevTab.id);
        }
        break;
      case "ArrowRight":
        e.preventDefault();
        if (index < allTabs.length - 1) {
          setFocusedTabIndex(index + 1);
          const nextTab = allTabs[index + 1];
          if (nextTab) setActiveTab(nextTab.id);
        }
        break;
      case "Enter":
      case " ":
        e.preventDefault();
        if (currentTab) setActiveTab(currentTab.id);
        break;
      case "Delete":
      case "w":
        if (e.ctrlKey || e.metaKey || !currentTab?.closable) {
          if (currentTab) {
            e.preventDefault();
            closeTab(currentTab.id);
          }
        }
        break;
      case "Home":
        e.preventDefault();
        if (allTabs.length > 0) {
          setFocusedTabIndex(0);
          setActiveTab(allTabs[0].id);
        }
        break;
      case "End":
        e.preventDefault();
        if (allTabs.length > 0) {
          setFocusedTabIndex(allTabs.length - 1);
          setActiveTab(allTabs[allTabs.length - 1].id);
        }
        break;
    }
  }, [setActiveTab, closeTab]);

  // Global keyboard shortcuts for tabs
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      // Ctrl+Tab - next tab
      if (e.ctrlKey && e.key === "Tab" && !e.shiftKey) {
        e.preventDefault();
        const currentIndex = tabs.findIndex((t) => t.id === activeTabId);
        const nextIndex = (currentIndex + 1) % tabs.length;
        if (tabs[nextIndex]) {
          setActiveTab(tabs[nextIndex].id);
          setFocusedTabIndex(nextIndex);
        }
      }
      
      // Ctrl+Shift+Tab - previous tab
      if (e.ctrlKey && e.key === "Tab" && e.shiftKey) {
        e.preventDefault();
        const currentIndex = tabs.findIndex((t) => t.id === activeTabId);
        const prevIndex = (currentIndex - 1 + tabs.length) % tabs.length;
        if (tabs[prevIndex]) {
          setActiveTab(tabs[prevIndex].id);
          setFocusedTabIndex(prevIndex);
        }
      }
      
      // Ctrl+W - close tab
      if (e.ctrlKey && e.key === "w" && activeTabId) {
        e.preventDefault();
        closeTab(activeTabId);
      }
    };

    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => window.removeEventListener("keydown", handleGlobalKeyDown);
  }, [tabs, activeTabId, setActiveTab, closeTab]);

  // Separate pinned and unpinned tabs
  const { pinnedTabs, unpinnedTabs } = useMemo(() => {
    const pinned: EditorTab[] = [];
    const unpinned: EditorTab[] = [];
    
    tabs.forEach((tab) => {
      if (tab.pinned) {
        pinned.push(tab);
      } else {
        unpinned.push(tab);
      }
    });
    
    return { pinnedTabs: pinned, unpinnedTabs: unpinned };
  }, [tabs]);

  // All tabs for keyboard navigation (pinned + visible unpinned)
  const allTabs = [...pinnedTabs, ...unpinnedTabs.slice(0, 10)];

  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event;
    
    if (over && active.id !== over.id) {
      const oldIndex = tabs.findIndex((t) => t.id === active.id);
      const newIndex = tabs.findIndex((t) => t.id === over.id);
      
      if (oldIndex !== -1 && newIndex !== -1) {
        reorderTabs(oldIndex, newIndex);
      }
    }
  }, [tabs, reorderTabs]);

  const handleContextMenu = useCallback((e: React.MouseEvent, tabId: string) => {
    e.preventDefault();
    setContextMenuTab(tabId);
  }, []);

  const handleCloseTab = useCallback((tabId: string) => (e: React.MouseEvent) => {
    e.stopPropagation();
    closeTab(tabId);
  }, [closeTab]);

  const handlePinTab = useCallback((tabId: string) => () => {
    pinTab(tabId);
  }, [pinTab]);

  const handleUnpinTab = useCallback((tabId: string) => () => {
    unpinTab(tabId);
  }, [unpinTab]);

  const handleTabClick = useCallback((tabId: string) => () => {
    setActiveTab(tabId);
  }, [setActiveTab]);

  const visibleTabs = unpinnedTabs;
  const maxVisibleTabs = 10;
  const visibleTabIds = visibleTabs.slice(0, maxVisibleTabs).map((t) => t.id);
  const overflowTabs = visibleTabs.slice(maxVisibleTabs);

  return (
    <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <div
        ref={tabBarRef}
        className={cn("flex items-center bg-[#252526] border-b border-[#3c3c3c] overflow-hidden", className)}
        role="tablist"
        aria-label="Editor tabs"
      >
        {/* Pinned Tabs */}
        {pinnedTabs.length > 0 && (
          <div className="flex items-center">
            {pinnedTabs.map((tab, index) => (
              <SortableTab
                key={tab.id}
                tab={tab}
                isActive={tab.id === activeTabId}
                onClick={handleTabClick(tab.id)}
                onClose={handleCloseTab(tab.id)}
                onPin={handlePinTab(tab.id)}
                onUnpin={handleUnpinTab(tab.id)}
                onContextMenu={(e) => handleContextMenu(e, tab.id)}
                tabIndex={index}
                isFocused={focusedTabIndex === index}
                onKeyDown={(e) => handleTabKeyDown(e, index, allTabs)}
              />
            ))}
            <div className="w-px h-6 bg-[#3c3c3c] mx-1" />
          </div>
        )}

        {/* Sortable Tabs */}
        <SortableContext items={visibleTabIds} strategy={horizontalListSortingStrategy}>
          {visibleTabIds.map((tabId, index) => {
            const tab = tabs.find((t) => t.id === tabId);
            if (!tab) return null;
            
            const absoluteIndex = pinnedTabs.length + index;
            
            return (
              <SortableTab
                key={tab.id}
                tab={tab}
                isActive={tab.id === activeTabId}
                onClick={handleTabClick(tab.id)}
                onClose={handleCloseTab(tab.id)}
                onPin={handlePinTab(tab.id)}
                onUnpin={handleUnpinTab(tab.id)}
                onContextMenu={(e) => handleContextMenu(e, tab.id)}
                tabIndex={absoluteIndex}
                isFocused={focusedTabIndex === absoluteIndex}
                onKeyDown={(e) => handleTabKeyDown(e, absoluteIndex, allTabs)}
              />
            );
          })}
        </SortableContext>

        {/* Overflow Menu */}
        {overflowTabs.length > 0 && (
          <DropdownMenu open={showOverflowMenu} onOpenChange={setShowOverflowMenu}>
            <DropdownMenuTrigger>
              <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="More tabs">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent  className="max-h-64 overflow-y-auto">
              {overflowTabs.map((tab) => (
                <DropdownMenuItem
                  key={tab.id}
                  onClick={handleTabClick(tab.id)}
                  className="flex items-center gap-2"
                >
                  {tab.title}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {/* Context Menu */}
        {contextMenuTab && (
          <div
            className="fixed z-50 bg-[#252526] border border-[#3c3c3c] rounded shadow-lg py-1 min-w-[180px]"
            style={{
              left: "50%",
              top: "50%",
            }}
            onClick={() => setContextMenuTab(null)}
          >
            <DropdownMenuItem onClick={handleCloseTab(contextMenuTab)} className="flex items-center gap-2">
              <X className="h-4 w-4" /> Close
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => { onCloseOthers?.(contextMenuTab); setContextMenuTab(null); }} className="flex items-center gap-2">
              Close Others
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => { onCloseAll?.(); setContextMenuTab(null); }} className="flex items-center gap-2">
              Close All
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => { onSplitEditor?.(contextMenuTab); setContextMenuTab(null); }} className="flex items-center gap-2">
              <SplitSquareHorizontal className="h-4 w-4" /> Split Editor
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            {tabs.find((t) => t.id === contextMenuTab)?.pinned ? (
              <DropdownMenuItem onClick={() => { unpinTab(contextMenuTab); setContextMenuTab(null); }} className="flex items-center gap-2">
                <PinOff className="h-4 w-4" /> Unpin
              </DropdownMenuItem>
            ) : (
              <DropdownMenuItem onClick={() => { pinTab(contextMenuTab); setContextMenuTab(null); }} className="flex items-center gap-2">
                <Pin className="h-4 w-4" /> Pin
              </DropdownMenuItem>
            )}
          </div>
        )}
      </div>
    </DndContext>
  );
}
