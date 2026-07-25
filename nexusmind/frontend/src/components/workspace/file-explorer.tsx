"use client";

import { useCallback, useMemo, useState } from "react";
import {
  FolderOpen,
  Folder,
  File,
  ChevronRight,
  ChevronDown,
  Plus,
  Search,
  MoreHorizontal,
  RefreshCw,
  Copy,
  Trash2,
  FileText,
  Image,
  Code,
  FileJson,
  Eye,
  GitCompare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { useWorkspaceStore, type WorkspaceFile } from "@/lib/stores/workspace";

interface FileNode {
  id: string;
  name: string;
  path: string;
  type: "file" | "folder";
  children?: FileNode[];
  expanded?: boolean;
}

interface FileExplorerProps {
  className?: string;
  onFileSelect?: (file: WorkspaceFile) => void;
  onFileOpen?: (file: WorkspaceFile) => void;
  onFilePreview?: (file: WorkspaceFile) => void;
  onFileCompare?: (file1: WorkspaceFile, file2: WorkspaceFile) => void;
  onCreateFile?: (path: string) => void;
  onCreateFolder?: (path: string) => void;
  onDeleteFile?: (path: string) => void;
  onRenameFile?: (oldPath: string, newPath: string) => void;
}

// Mock file tree for demonstration
const mockFileTree: FileNode[] = [
  {
    id: "1",
    name: "src",
    path: "/src",
    type: "folder",
    expanded: true,
    children: [
      {
        id: "2",
        name: "components",
        path: "/src/components",
        type: "folder",
        expanded: true,
        children: [
          { id: "3", name: "Button.tsx", path: "/src/components/Button.tsx", type: "file" },
          { id: "4", name: "Input.tsx", path: "/src/components/Input.tsx", type: "file" },
        ],
      },
      {
        id: "5",
        name: "lib",
        path: "/src/lib",
        type: "folder",
        children: [
          { id: "6", name: "utils.ts", path: "/src/lib/utils.ts", type: "file" },
          { id: "7", name: "api.ts", path: "/src/lib/api.ts", type: "file" },
        ],
      },
      { id: "8", name: "app.tsx", path: "/src/app.tsx", type: "file" },
      { id: "9", name: "index.ts", path: "/src/index.ts", type: "file" },
    ],
  },
  {
    id: "10",
    name: "package.json",
    path: "/package.json",
    type: "file",
  },
  {
    id: "11",
    name: "README.md",
    path: "/README.md",
    type: "file",
  },
];

// Get file icon based on extension
function getFileIcon(name: string) {
  const ext = name.split(".").pop()?.toLowerCase();
  
  const iconClass = "h-3 w-3";
  
  switch (ext) {
    case "ts":
    case "tsx":
      return <Code className={iconClass} />;
    case "js":
    case "jsx":
      return <Code className={iconClass} />;
    case "json":
      return <FileJson className={iconClass} />;
    case "md":
      return <FileText className={iconClass} />;
    case "png":
    case "jpg":
    case "jpeg":
    case "gif":
    case "svg":
      return <Image className={iconClass} />;
    default:
      return <File className={iconClass} />;
  }
}

// Get file color based on extension
function getFileColor(name: string): string {
  const ext = name.split(".").pop()?.toLowerCase();
  
  switch (ext) {
    case "ts":
    case "tsx":
      return "text-blue-400";
    case "js":
    case "jsx":
      return "text-yellow-400";
    case "json":
      return "text-orange-400";
    case "md":
      return "text-gray-400";
    case "png":
    case "jpg":
    case "jpeg":
    case "gif":
      return "text-purple-400";
    default:
      return "text-gray-300";
  }
}

function FileTreeNode({
  node,
  depth,
  onSelect,
  onOpen,
  onPreview,
  onCompare,
  onDelete,
  selectedFile,
}: {
  node: FileNode;
  depth: number;
  onSelect: (node: FileNode) => void;
  onOpen: (node: FileNode) => void;
  onPreview: (node: FileNode) => void;
  onCompare: (node: FileNode) => void;
  onDelete: (node: FileNode) => void;
  selectedFile: string | null;
}) {
  const [expanded, setExpanded] = useState(node.expanded || false);
  const [isHovered, setIsHovered] = useState(false);

  const handleClick = () => {
    if (node.type === "folder") {
      setExpanded(!expanded);
    } else {
      onSelect(node);
    }
  };

  const handleDoubleClick = () => {
    if (node.type === "file") {
      onOpen(node);
    }
  };

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-1 px-2 py-0.5 text-sm cursor-pointer rounded hover:bg-[#2a2d2e] transition-colors",
          selectedFile === node.id && "bg-[#094771]"
        )}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {node.type === "folder" ? (
          <>
            {expanded ? (
              <ChevronDown className="h-3 w-3 text-gray-500" />
            ) : (
              <ChevronRight className="h-3 w-3 text-gray-500" />
            )}
            {expanded ? (
              <FolderOpen className="h-3 w-3 text-yellow-500" />
            ) : (
              <Folder className="h-3 w-3 text-yellow-500" />
            )}
          </>
        ) : (
          <>
            <span className="w-3" />
            <span className={getFileColor(node.name)}>{getFileIcon(node.name)}</span>
          </>
        )}
        <span className="flex-1 truncate">{node.name}</span>
        
        {/* Context Menu */}
        {isHovered && node.type === "file" && (
          <div className="flex items-center gap-0.5">
            <Button
              variant="ghost"
              size="icon"
              className="h-5 w-5"
              onClick={(e) => {
                e.stopPropagation();
                onPreview(node);
              }}
            >
              <Eye className="h-3 w-3" />
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreHorizontal className="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onOpen(node)}>
                  <File className="h-4 w-4 mr-2" /> Open
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onPreview(node)}>
                  <Eye className="h-4 w-4 mr-2" /> Preview
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onCompare(node)}>
                  <GitCompare className="h-4 w-4 mr-2" /> Compare
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Copy className="h-4 w-4 mr-2" /> Copy Path
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigator.clipboard.writeText(node.name)}>
                  <File className="h-4 w-4 mr-2" /> Copy Name
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigator.clipboard.writeText(node.path)}>
                  <File className="h-4 w-4 mr-2" /> Copy Relative Path
                </DropdownMenuItem>
                <DropdownMenuItem onClick={onDelete} className="text-red-500">
                  <Trash2 className="h-4 w-4 mr-2" /> Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>

      {/* Children */}
      {node.type === "folder" && expanded && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTreeNode
              key={child.id}
              node={child}
              depth={depth + 1}
              onSelect={onSelect}
              onOpen={onOpen}
              onPreview={onPreview}
              onCompare={onCompare}
              onDelete={onDelete}
              selectedFile={selectedFile}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function FileExplorer({
  className,
  onFileSelect,
  onFileOpen,
  onFilePreview,
  onFileCompare,
  onCreateFile,
  onCreateFolder,
  onDeleteFile,
  onRenameFile,
}: FileExplorerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [compareFile, setCompareFile] = useState<FileNode | null>(null);

  const { openFile } = useWorkspaceStore();

  const filteredTree = useMemo(() => {
    if (!searchQuery) return mockFileTree;

    const filterTree = (nodes: FileNode[]): FileNode[] => {
      return nodes.reduce<FileNode[]>((acc, node) => {
        const matchesSearch = node.name.toLowerCase().includes(searchQuery.toLowerCase());
        const filteredChildren = node.children ? filterTree(node.children) : [];
        
        if (matchesSearch || filteredChildren.length > 0) {
          acc.push({
            ...node,
            expanded: true,
            children: filteredChildren,
          });
        }
        
        return acc;
      }, []);
    };

    return filterTree(mockFileTree);
  }, [searchQuery]);

  const handleSelect = useCallback((node: FileNode) => {
    setSelectedFile(node.id);
    onFileSelect?.({
      id: node.id,
      name: node.name,
      path: node.path,
      content: "// File content would be loaded here",
      language: node.name.split(".").pop() || "plaintext",
      modified: false,
    });
  }, [onFileSelect]);

  const handleOpen = useCallback((node: FileNode) => {
    openFile({
      id: node.id,
      name: node.name,
      path: node.path,
      content: "// File content would be loaded here",
      language: node.name.split(".").pop() || "plaintext",
      modified: false,
    });
    onFileOpen?.({
      id: node.id,
      name: node.name,
      path: node.path,
      content: "// File content would be loaded here",
      language: node.name.split(".").pop() || "plaintext",
      modified: false,
    });
  }, [openFile, onFileOpen]);

  const handlePreview = useCallback((node: FileNode) => {
    onFilePreview?.({
      id: node.id,
      name: node.name,
      path: node.path,
      content: "// File content would be loaded here",
      language: node.name.split(".").pop() || "plaintext",
      modified: false,
    });
  }, [onFilePreview]);

  const handleCompare = useCallback((node: FileNode) => {
    if (compareFile) {
      // Compare with previously selected file
      onFileCompare?.(compareFile as unknown as WorkspaceFile, {
        id: node.id,
        name: node.name,
        path: node.path,
        content: "// File content would be loaded here",
        language: node.name.split(".").pop() || "plaintext",
        modified: false,
      });
      setCompareFile(null);
    } else {
      // Select this file for comparison
      setCompareFile(node);
    }
  }, [compareFile, onFileCompare]);

  const handleDelete = useCallback((node: FileNode) => {
    if (confirm(`Delete "${node.name}"?`)) {
      onDeleteFile?.(node.path);
    }
  }, [onDeleteFile]);

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-2 py-1 border-b border-[#3c3c3c]">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Explorer
          </span>
          {compareFile && (
            <span className="text-xs text-yellow-500">Compare: {compareFile.name}</span>
          )}
        </div>
        <div className="flex items-center gap-0.5">
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={() => onCreateFile?.("/new-file.ts")}
            title="New File"
          >
            <Plus className="h-3 w-3" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={() => onCreateFolder?.("/new-folder")}
            title="New Folder"
          >
            <FolderOpen className="h-3 w-3" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            title="Refresh"
          >
            <RefreshCw className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="px-2 py-1">
        <div className="relative">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-gray-500" />
          <Input
            type="text"
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-6 pl-6 pr-2 text-xs"
          />
        </div>
      </div>

      {/* File Tree */}
      <div className="flex-1 overflow-y-auto py-1">
        {filteredTree.map((node) => (
          <FileTreeNode
            key={node.id}
            node={node}
            depth={0}
            onSelect={handleSelect}
            onOpen={handleOpen}
            onPreview={handlePreview}
            onCompare={handleCompare}
            onDelete={handleDelete}
            selectedFile={selectedFile}
          />
        ))}
      </div>
    </div>
  );
}
