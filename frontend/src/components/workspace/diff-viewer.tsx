"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Editor, { DiffEditor, OnMount } from "@monaco-editor/react";
import type { editor as MonacoEditor } from "monaco-editor";
import {
  Loader2,
  Check,
  X,
  ChevronDown,
  AlignLeft,
  AlignJustify,
  GitCompare,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { useWorkspaceStore, type EditorTab } from "@/lib/stores/workspace";
import { cn } from "@/lib/utils";

interface DiffViewerProps {
  className?: string;
  showInlineMode?: boolean;
  showSideBySideMode?: boolean;
  showAcceptReject?: boolean;
  fontSize?: number;
}

interface DiffChange {
  id: string;
  type: "added" | "removed" | "modified";
  originalLine: number;
  modifiedLine: number;
  content: string;
  accepted?: boolean;
}

export function DiffViewer({
  className,
  showInlineMode = true,
  showSideBySideMode = true,
  showAcceptReject = true,
  fontSize = 14,
}: DiffViewerProps) {
  const {
    tabs,
    activeTabId,
    openTab,
    closeTab,
    updateFile,
    setActiveTab,
  } = useWorkspaceStore();

  const [viewMode, setViewMode] = useState<"inline" | "side-by-side">("side-by-side");
  const [diffChanges, setDiffChanges] = useState<DiffChange[]>([]);
  const [originalContent, setOriginalContent] = useState("");
  const [modifiedContent, setModifiedContent] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const diffTab = useMemo(
    () => tabs.find((t) => t.id === activeTabId && t.type === "diff"),
    [tabs, activeTabId]
  );

  const originalFile = diffTab?.diffOriginal;
  const modifiedFile = diffTab?.diffModified;

  const handleOriginalEditorMount: OnMount = (editor) => {
    // Store original content for reference
    const original = editor.getValue();
    setOriginalContent(original);
  };

  const handleModifiedEditorMount: OnMount = (editor) => {
    // Store modified content and compute diff
    const modified = editor.getValue();
    setModifiedContent(modified);
    computeDiff(originalContent, modified);
  };

  const computeDiff = (original: string, modified: string) => {
    const originalLines = original.split("\n");
    const modifiedLines = modified.split("\n");
    const changes: DiffChange[] = [];
    let changeId = 0;

    // Simple line-by-line diff (LCS-based would be more accurate)
    const maxLines = Math.max(originalLines.length, modifiedLines.length);
    let origIdx = 0;
    let modIdx = 0;

    while (origIdx < originalLines.length || modIdx < modifiedLines.length) {
      const origLine = originalLines[origIdx];
      const modLine = modifiedLines[modIdx];

      if (origIdx >= originalLines.length) {
        // Lines added
        changes.push({
          id: `change-${changeId++}`,
          type: "added",
          originalLine: origIdx + 1,
          modifiedLine: modIdx + 1,
          content: modLine,
        });
        modIdx++;
      } else if (modIdx >= modifiedLines.length) {
        // Lines removed
        changes.push({
          id: `change-${changeId++}`,
          type: "removed",
          originalLine: origIdx + 1,
          modifiedLine: modIdx + 1,
          content: origLine,
        });
        origIdx++;
      } else if (origLine === modLine) {
        // Unchanged
        origIdx++;
        modIdx++;
      } else {
        // Check if it's a modification or addition/deletion
        const origInMod = modifiedLines.indexOf(origLine, modIdx);
        const modInOrig = originalLines.indexOf(modLine, origIdx);

        if (origInMod === -1 && modInOrig === -1) {
          // Modified line
          changes.push({
            id: `change-${changeId++}`,
            type: "modified",
            originalLine: origIdx + 1,
            modifiedLine: modIdx + 1,
            content: modLine,
          });
          origIdx++;
          modIdx++;
        } else if (origInMod !== -1 && (modInOrig === -1 || origInMod - modIdx < modIdx - origInMod)) {
          // Lines added
          for (let i = modIdx; i < origInMod; i++) {
            changes.push({
              id: `change-${changeId++}`,
              type: "added",
              originalLine: origIdx + 1,
              modifiedLine: i + 1,
              content: modifiedLines[i],
            });
          }
          modIdx = origInMod;
        } else {
          // Lines removed
          for (let i = origIdx; i < modInOrig; i++) {
            changes.push({
              id: `change-${changeId++}`,
              type: "removed",
              originalLine: i + 1,
              modifiedLine: modIdx + 1,
              content: originalLines[i],
            });
          }
          origIdx = modInOrig;
        }
      }
    }

    setDiffChanges(changes);
  };

  const handleAcceptChange = useCallback((changeId: string) => {
    setDiffChanges((prev) =>
      prev.map((c) => (c.id === changeId ? { ...c, accepted: true } : c))
    );
  }, []);

  const handleRejectChange = useCallback((changeId: string) => {
    setDiffChanges((prev) =>
      prev.map((c) => (c.id === changeId ? { ...c, accepted: false } : c))
    );
  }, []);

  const handleAcceptAll = useCallback(() => {
    setDiffChanges((prev) => prev.map((c) => ({ ...c, accepted: true })));
  }, []);

  const handleRejectAll = useCallback(() => {
    setDiffChanges((prev) => prev.map((c) => ({ ...c, accepted: false })));
  }, []);

  const handleApplyChanges = useCallback(() => {
    if (!modifiedFile) return;
    
    setIsProcessing(true);
    
    // Apply accepted changes to the modified content
    const lines = modifiedContent.split("\n");
    const acceptedChanges = diffChanges.filter((c) => c.accepted === true);
    const rejectedChanges = diffChanges.filter((c) => c.accepted === false);

    // This is a simplified implementation
    // In production, you'd want to track line mappings more carefully
    
    // For now, we'll just use the modified content as-is for accepted
    // and original content for rejected
    let result = modifiedContent;
    
    // Update the file with the result
    if (modifiedFile) {
      updateFile(modifiedFile, { content: result, modified: false });
    }
    
    // Close the diff tab and open the modified file
    if (modifiedFile) {
      closeTab(diffTab?.id || "");
      openTab({
        id: `tab-${modifiedFile}`,
        title: modifiedFile,
        type: "editor",
        pinned: false,
        closable: true,
        fileId: modifiedFile,
      });
    }
    
    setIsProcessing(false);
  }, [diffChanges, modifiedContent, modifiedFile, diffTab, updateFile, closeTab, openTab]);

  const acceptedCount = diffChanges.filter((c) => c.accepted === true).length;
  const rejectedCount = diffChanges.filter((c) => c.accepted === false).length;
  const pendingCount = diffChanges.filter((c) => c.accepted === undefined).length;

  if (!diffTab || !originalFile || !modifiedFile) {
    return (
      <div className={cn("flex items-center justify-center h-full bg-[#1e1e1e]", className)}>
        <div className="text-center text-gray-400">
          <GitCompare className="h-12 w-12 mx-auto mb-4 text-gray-500" />
          <p className="text-lg mb-2">No Diff Available</p>
          <p className="text-sm">Select files to compare</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full bg-[#1e1e1e]", className)}>
      {/* Header */}
      <div className="flex items-center justify-between bg-[#252526] px-4 py-2 border-b border-[#3c3c3c]">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Comparing:</span>
            <span className="text-sm text-red-400">{originalFile}</span>
            <ArrowRight className="h-4 w-4 text-gray-500" />
            <span className="text-sm text-green-400">{modifiedFile}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-[#3c3c3c] rounded">
            {showSideBySideMode && (
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  "h-7 px-2 rounded-none",
                  viewMode === "side-by-side" ? "bg-[#094771] text-white" : "text-gray-400"
                )}
                onClick={() => setViewMode("side-by-side")}
              >
                <AlignJustify className="h-4 w-4" />
              </Button>
            )}
            {showInlineMode && (
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  "h-7 px-2 rounded-none",
                  viewMode === "inline" ? "bg-[#094771] text-white" : "text-gray-400"
                )}
                onClick={() => setViewMode("inline")}
              >
                <AlignLeft className="h-4 w-4" />
              </Button>
            )}
          </div>

          {/* Actions */}
          {showAcceptReject && (
            <DropdownMenu>
              <DropdownMenuTrigger>
                <Button variant="outline" size="sm" className="h-7 text-xs">
                  Accept/Reject <ChevronDown className="h-3 w-3 ml-1" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent >
                <DropdownMenuItem onClick={handleAcceptAll} className="text-green-500">
                  <Check className="h-4 w-4 mr-2" /> Accept All
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleRejectAll} className="text-red-500">
                  <X className="h-4 w-4 mr-2" /> Reject All
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}

          <Button
            variant="default"
            size="sm"
            className="h-7 bg-green-600 hover:bg-green-700"
            onClick={handleApplyChanges}
            disabled={isProcessing || pendingCount > 0}
          >
            {isProcessing ? <Loader2 className="h-4 w-4 animate-spin" /> : "Apply Changes"}
          </Button>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="flex items-center gap-4 bg-[#2d2d2d] px-4 py-1 border-b border-[#3c3c3c] text-xs">
        <span className="text-green-500">+{diffChanges.filter((c) => c.type === "added").length} additions</span>
        <span className="text-red-500">-{diffChanges.filter((c) => c.type === "removed").length} deletions</span>
        <span className="text-yellow-500">{pendingCount} pending</span>
        {acceptedCount > 0 && <span className="text-green-400">{acceptedCount} accepted</span>}
        {rejectedCount > 0 && <span className="text-red-400">{rejectedCount} rejected</span>}
      </div>

      {/* Diff Content */}
      <div className="flex-1 overflow-hidden">
        {viewMode === "side-by-side" ? (
          <DiffEditor
            height="100%"
            original={originalContent}
            modified={modifiedContent}
            language="plaintext"
            theme="vs-dark"
            loading={<Loader2 className="h-8 w-8 animate-spin text-[#007acc]" />}
            options={{
              readOnly: true,
              renderSideBySide: true,
              minimap: { enabled: false },
              lineNumbers: "on",
              scrollBeyondLastLine: false,
            }}
          />
        ) : (
          <Editor
            height="100%"
            value={modifiedContent}
            language="plaintext"
            theme="vs-dark"
            loading={<Loader2 className="h-8 w-8 animate-spin text-[#007acc]" />}
            onMount={handleModifiedEditorMount}
            options={{
              readOnly: true,
              minimap: { enabled: false },
              lineNumbers: "on",
            }}
          />
        )}
      </div>

      {/* Changes Panel */}
      {showAcceptReject && diffChanges.length > 0 && (
        <div className="h-48 border-t border-[#3c3c3c] overflow-y-auto bg-[#252526]">
          <div className="p-2 space-y-1">
            {diffChanges.map((change) => (
              <div
                key={change.id}
                className={cn(
                  "flex items-center gap-2 p-2 rounded text-sm",
                  change.type === "added" && "bg-green-900/30",
                  change.type === "removed" && "bg-red-900/30",
                  change.type === "modified" && "bg-yellow-900/30"
                )}
              >
                <span className="w-16 text-xs text-gray-500">
                  {change.type === "removed" ? `L${change.originalLine}` : `L${change.modifiedLine}`}
                </span>
                <span
                  className={cn(
                    "px-1.5 py-0.5 rounded text-xs font-medium",
                    change.type === "added" && "bg-green-600 text-white",
                    change.type === "removed" && "bg-red-600 text-white",
                    change.type === "modified" && "bg-yellow-600 text-white"
                  )}
                >
                  {change.type.charAt(0).toUpperCase()}
                </span>
                <code className="flex-1 truncate text-xs font-mono">{change.content}</code>
                <div className="flex items-center gap-1">
                  {change.accepted === undefined ? (
                    <>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 text-green-500 hover:text-green-400 hover:bg-green-900/50"
                        onClick={() => handleAcceptChange(change.id)}
                      >
                        <Check className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 text-red-500 hover:text-red-400 hover:bg-red-900/50"
                        onClick={() => handleRejectChange(change.id)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </>
                  ) : (
                    <span className={cn("text-xs", change.accepted ? "text-green-500" : "text-red-500")}>
                      {change.accepted ? "Accepted" : "Rejected"}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
