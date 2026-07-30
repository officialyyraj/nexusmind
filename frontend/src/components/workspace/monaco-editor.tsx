"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Editor, { Monaco, OnMount } from "@monaco-editor/react";
import type { editor as MonacoEditor } from "monaco-editor";
import { Loader2, SplitSquareHorizontal, SplitSquareVertical, Minimize2, Maximize2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useWorkspaceStore, type WorkspaceFile } from "@/lib/stores/workspace";
import { cn } from "@/lib/utils";

interface MonacoEditorProps {
  className?: string;
  autoSave?: boolean;
  autoSaveDelay?: number;
  showMinimap?: boolean;
  showLineNumbers?: boolean;
  showBreadcrumbs?: boolean;
  showFileOutline?: boolean;
  fontSize?: number;
}

export function WorkspaceEditor({
  className,
  autoSave = true,
  autoSaveDelay = 2000,
  showMinimap = true,
  showLineNumbers = true,
  showBreadcrumbs = true,
  showFileOutline = true,
  fontSize = 14,
}: MonacoEditorProps) {
  const {
    openFiles,
    activeFileId,
    tabs,
    activeTabId,
    splitLayout,
    updateFile,
    setActiveFile,
    setActiveTab,
  } = useWorkspaceStore();

  const [editorInstance, setEditorInstance] = useState<MonacoEditor.IStandaloneCodeEditor | null>(null);
  const [diffEditorInstance, setDiffEditorInstance] = useState<MonacoEditor.IStandaloneDiffEditor | null>(null);
  const [splitView, setSplitView] = useState(false);
  const [splitDirection, setSplitDirection] = useState<"horizontal" | "vertical">("horizontal");
  const [isMaximized, setIsMaximized] = useState(false);
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);

  const activeFile = useMemo(
    () => openFiles.find((f) => f.id === activeFileId),
    [openFiles, activeFileId]
  );

  const activeTab = useMemo(
    () => tabs.find((t) => t.id === activeTabId),
    [tabs, activeTabId]
  );

  const editorTabs = useMemo(
    () => tabs.filter((t) => t.type === "editor"),
    [tabs]
  );

  const handleEditorMount: OnMount = (editor, monaco) => {
    setEditorInstance(editor);

    // Configure editor
    editor.updateOptions({
      fontSize,
      minimap: { enabled: showMinimap },
      lineNumbers: showLineNumbers ? "on" : "off",
      scrollBeyondLastLine: false,
      automaticLayout: true,
      wordWrap: "on",
      padding: { top: 8 },
      renderLineHighlight: "all",
      cursorBlinking: "smooth",
      smoothScrolling: true,
      tabSize: 2,
      insertSpaces: true,
    });

    // Add keyboard shortcuts
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      if (autoSave) {
        handleSave(activeFile?.id);
      }
    });

    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KeyF, () => {
      // Trigger global search
    });
  };

  const handleDiffEditorMount: OnMount = (editor, _monaco) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    setDiffEditorInstance(editor as unknown as MonacoEditor.IStandaloneDiffEditor);
  };

  const handleSave = useCallback((fileId?: string) => {
    if (!fileId || !editorInstance) return;
    
    const file = openFiles.find((f) => f.id === fileId);
    if (!file || file.readonly) return;

    const content = editorInstance.getValue();
    updateFile(fileId, { content, modified: false });
  }, [editorInstance, openFiles, updateFile]);

  const handleContentChange = useCallback((value: string | undefined) => {
    if (!value || !activeFileId || activeFile?.readonly) return;

    updateFile(activeFileId, { content: value, modified: true });

    // Auto-save
    if (autoSave) {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
      autoSaveTimerRef.current = setTimeout(() => {
        handleSave(activeFileId);
      }, autoSaveDelay);
    }
  }, [activeFileId, activeFile, autoSave, autoSaveDelay, handleSave, updateFile]);

  const handleTabClick = useCallback((tabId: string) => {
    setActiveTab(tabId);
  }, [setActiveTab]);

  const handleEditorChange = useCallback((value: string | undefined) => {
    handleContentChange(value);
  }, [handleContentChange]);

  // Cleanup auto-save timer
  useEffect(() => {
    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, []);

  const toggleSplitView = () => {
    setSplitView(!splitView);
  };

  const toggleSplitDirection = () => {
    setSplitDirection(splitDirection === "horizontal" ? "vertical" : "horizontal");
  };

  const toggleMaximize = () => {
    setIsMaximized(!isMaximized);
  };

  // Get language from file extension
  const getLanguage = (filename: string): string => {
    const ext = filename.split(".").pop()?.toLowerCase() || "";
    const languageMap: Record<string, string> = {
      ts: "typescript",
      tsx: "typescript",
      js: "javascript",
      jsx: "javascript",
      py: "python",
      rs: "rust",
      go: "go",
      java: "java",
      c: "c",
      cpp: "cpp",
      cs: "csharp",
      rb: "ruby",
      php: "php",
      swift: "swift",
      kt: "kotlin",
      scala: "scala",
      md: "markdown",
      json: "json",
      yaml: "yaml",
      yml: "yaml",
      xml: "xml",
      html: "html",
      css: "css",
      scss: "scss",
      less: "less",
      sql: "sql",
      sh: "shell",
      bash: "shell",
      zsh: "shell",
      ps1: "powershell",
      dockerfile: "dockerfile",
      tf: "hcl",
      vue: "html",
      svelte: "html",
    };
    return languageMap[ext] || "plaintext";
  };

  if (!activeFile) {
    return (
      <div className={cn("flex items-center justify-center h-full bg-[#1e1e1e]", className)}>
        <div className="text-center text-gray-400">
          <p className="text-lg mb-2">No file open</p>
          <p className="text-sm">Select a file from the explorer to start editing</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full bg-[#1e1e1e]", className)}>
      {/* Tab Bar */}
      {showBreadcrumbs && (
        <div className="flex items-center bg-[#252526] border-b border-[#3c3c3c] overflow-x-auto">
          {editorTabs.map((tab) => (
            <div
              key={tab.id}
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 text-sm cursor-pointer border-r border-[#3c3c3c] min-w-[120px] max-w-[200px]",
                "hover:bg-[#2a2d2e] transition-colors",
                tab.id === activeTabId ? "bg-[#1e1e1e] border-t-2 border-t-[#007acc]" : ""
              )}
              onClick={() => handleTabClick(tab.id)}
            >
              {tab.pinned && <span className="text-yellow-500">📌</span>}
              <span className="truncate flex-1">{tab.title}</span>
              {(tab.data?.modified as boolean) && <span className="text-[#e8ab53]">●</span>}
            </div>
          ))}
        </div>
      )}

      {/* Editor Toolbar */}
      <div className="flex items-center justify-between bg-[#252526] px-2 py-1 border-b border-[#3c3c3c]">
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span>{activeFile.path}</span>
          {activeFile.readonly && <span className="text-yellow-500">(Read-only)</span>}
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-gray-400 hover:text-white"
            onClick={toggleSplitView}
            title="Split Editor"
          >
            <SplitSquareHorizontal className="h-4 w-4" />
          </Button>
          {splitView && (
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 text-gray-400 hover:text-white"
              onClick={toggleSplitDirection}
              title={splitDirection === "horizontal" ? "Vertical Split" : "Horizontal Split"}
            >
              {splitDirection === "horizontal" ? (
                <SplitSquareVertical className="h-4 w-4" />
              ) : (
                <SplitSquareHorizontal className="h-4 w-4" />
              )}
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-gray-400 hover:text-white"
            onClick={toggleMaximize}
            title={isMaximized ? "Restore" : "Maximize"}
          >
            {isMaximized ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Editor Content */}
      <div className={cn("flex-1 overflow-hidden", isMaximized ? "fixed inset-0 z-50" : "")}>
        {splitView ? (
          <div
            className={cn(
              "flex h-full",
              splitDirection === "horizontal" ? "flex-col" : "flex-row"
            )}
          >
            <div className="flex-1 min-w-0 min-h-0">
              <Editor
                height="100%"
                language={getLanguage(activeFile.name)}
                value={activeFile.content}
                onChange={handleEditorChange}
                onMount={handleEditorMount}
                theme="vs-dark"
                loading={<Loader2 className="h-8 w-8 animate-spin text-[#007acc]" />}
                options={{
                  readOnly: activeFile.readonly,
                  minimap: { enabled: showMinimap },
                  lineNumbers: showLineNumbers ? "on" : "off",
                }}
              />
            </div>
            <div className={cn("bg-[#3c3c3c]", splitDirection === "horizontal" ? "h-1 cursor-row-resize" : "w-1 cursor-col-resize")} />
            <div className="flex-1 min-w-0 min-h-0">
              <Editor
                height="100%"
                language={getLanguage(activeFile.name)}
                value={activeFile.content}
                theme="vs-dark"
                loading={<Loader2 className="h-8 w-8 animate-spin text-[#007acc]" />}
                options={{
                  readOnly: true,
                  minimap: { enabled: false },
                }}
              />
            </div>
          </div>
        ) : (
          <Editor
            height="100%"
            language={getLanguage(activeFile.name)}
            value={activeFile.content}
            onChange={handleEditorChange}
            onMount={handleEditorMount}
            theme="vs-dark"
            loading={<Loader2 className="h-8 w-8 animate-spin text-[#007acc]" />}
            options={{
              readOnly: activeFile.readonly,
              minimap: { enabled: showMinimap },
              lineNumbers: showLineNumbers ? "on" : "off",
            }}
          />
        )}
      </div>
    </div>
  );
}
