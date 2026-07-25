"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useWorkspaceStore, type SearchQuery, type WorkspaceSearchResult } from "@/lib/stores/workspace";
import {
  Search,
  X,
  Replace,
  ChevronDown,
  ChevronRight,
  File,
  Folder,
  Loader2,
  CaseSensitive,
  Regex,
  WholeWord,
  IncludeHidden,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

interface WorkspaceSearchProps {
  className?: string;
  onResultClick?: (result: WorkspaceSearchResult) => void;
  onReplace?: (result: WorkspaceSearchResult, replacement: string) => void;
  onReplaceAll?: (query: string, replacement: string, results: WorkspaceSearchResult[]) => void;
}

export function WorkspaceSearch({
  className,
  onResultClick,
  onReplace,
  onReplaceAll,
}: WorkspaceSearchProps) {
  const {
    openFiles,
    searchQuery,
    searchResults,
    isSearching,
    setSearchQuery,
    setSearchResults,
    setIsSearching,
    openFile,
  } = useWorkspaceStore();

  const [localQuery, setLocalQuery] = useState(searchQuery?.query || "");
  const [localReplace, setLocalReplace] = useState("");
  const [showOptions, setShowOptions] = useState(false);
  const [regex, setRegex] = useState(searchQuery?.regex || false);
  const [caseSensitive, setCaseSensitive] = useState(searchQuery?.caseSensitive || false);
  const [wholeWord, setWholeWord] = useState(searchQuery?.wholeWord || false);
  const [includeHidden, setIncludeHidden] = useState(searchQuery?.includeHidden || false);

  const inputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Search when query changes
  useEffect(() => {
    if (!localQuery.trim()) {
      setSearchResults([]);
      return;
    }

    const performSearch = async () => {
      setIsSearching(true);

      try {
        const query: SearchQuery = {
          query: localQuery,
          regex,
          caseSensitive,
          wholeWord,
          includeHidden,
          maxResults: 100,
        };

        // Update store
        setSearchQuery(query);

        // Perform search across open files
        const results: WorkspaceSearchResult[] = [];
        const flags = caseSensitive ? "g" : "gi";
        let pattern: RegExp;

        if (regex) {
          pattern = new RegExp(localQuery, flags);
        } else if (wholeWord) {
          pattern = new RegExp(`\\b${localQuery.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, flags);
        } else {
          pattern = new RegExp(localQuery.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), flags);
        }

        for (const file of openFiles) {
          if (!includeHidden && file.name.startsWith(".")) continue;

          const lines = file.content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            let match: RegExpExecArray | null;

            pattern.lastIndex = 0; // Reset regex state
            while ((match = pattern.exec(line)) !== null) {
              results.push({
                fileId: file.id,
                filePath: file.path,
                line: i + 1,
                column: match.index + 1,
                match: match[0],
                context: line.trim().substring(Math.max(0, match.index - 30), match.index + match[0].length + 30),
              });

              if (results.length >= query.maxResults) break;
            }

            if (results.length >= query.maxResults) break;
          }

          if (results.length >= query.maxResults) break;
        }

        setSearchResults(results);
      } catch (err) {
        console.error("Search error:", err);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    };

    const debounce = setTimeout(performSearch, 300);
    return () => clearTimeout(debounce);
  }, [localQuery, regex, caseSensitive, wholeWord, includeHidden, openFiles, setSearchQuery, setSearchResults, setIsSearching]);

  const handleResultClick = useCallback((result: WorkspaceSearchResult) => {
    onResultClick?.(result);

    // Open the file and navigate to the result
    const file = openFiles.find((f) => f.id === result.fileId);
    if (file) {
      openFile({
        ...file,
        cursorPosition: { line: result.line, column: result.column },
      });
    }
  }, [onResultClick, openFiles, openFile]);

  const handleReplace = useCallback((result: WorkspaceSearchResult) => {
    if (!localReplace) return;
    onReplace?.(result, localReplace);
  }, [localReplace, onReplace]);

  const handleReplaceAll = useCallback(() => {
    if (!localQuery || !localReplace) return;
    onReplaceAll?.(localQuery, localReplace, searchResults);
  }, [localQuery, localReplace, searchResults, onReplaceAll]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      if (e.shiftKey && localReplace) {
        handleReplaceAll();
      }
    } else if (e.key === "Escape") {
      setSearchQuery(null);
    }
  };

  // Group results by file
  const groupedResults = useMemo(() => {
    const groups: Record<string, WorkspaceSearchResult[]> = {};
    for (const result of searchResults) {
      if (!groups[result.fileId]) {
        groups[result.fileId] = [];
      }
      groups[result.fileId].push(result);
    }
    return groups;
  }, [searchResults]);

  return (
    <div className={cn("flex flex-col h-full bg-white dark:bg-gray-900", className)}>
      {/* Search Input */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 space-y-2">
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4 text-gray-400" />
          <Input
            ref={inputRef}
            type="text"
            placeholder="Search..."
            value={localQuery}
            onChange={(e) => setLocalQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 h-8 text-sm"
          />
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setShowOptions(!showOptions)}
          >
            <ChevronDown className={cn("h-4 w-4 transition-transform", showOptions && "rotate-180")} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setSearchQuery(null)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Options */}
        <div className={cn("space-y-2", !showOptions && "hidden")}>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Checkbox
                id="regex"
                checked={regex}
                onCheckedChange={(checked) => setRegex(!!checked)}
              />
              <Label htmlFor="regex" className="text-sm flex items-center gap-1 cursor-pointer">
                <Regex className="h-3 w-3" /> Regex
              </Label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="caseSensitive"
                checked={caseSensitive}
                onCheckedChange={(checked) => setCaseSensitive(!!checked)}
              />
              <Label htmlFor="caseSensitive" className="text-sm flex items-center gap-1 cursor-pointer">
                <CaseSensitive className="h-3 w-3" /> Aa
              </Label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="wholeWord"
                checked={wholeWord}
                onCheckedChange={(checked) => setWholeWord(!!checked)}
              />
              <Label htmlFor="wholeWord" className="text-sm flex items-center gap-1 cursor-pointer">
                <WholeWord className="h-3 w-3" /> W
              </Label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="includeHidden"
                checked={includeHidden}
                onCheckedChange={(checked) => setIncludeHidden(!!checked)}
              />
              <Label htmlFor="includeHidden" className="text-sm flex items-center gap-1 cursor-pointer">
                <IncludeHidden className="h-3 w-3" /> Hidden
              </Label>
            </div>
          </div>

          {/* Replace */}
          <div className="flex items-center gap-2">
            <Replace className="h-4 w-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Replace..."
              value={localReplace}
              onChange={(e) => setLocalReplace(e.target.value)}
              className="flex-1 h-8 text-sm"
            />
            <Button
              variant="outline"
              size="sm"
              className="h-8 text-xs"
              onClick={handleReplaceAll}
              disabled={!localQuery || !localReplace || searchResults.length === 0}
            >
              Replace All ({searchResults.length})
            </Button>
          </div>
        </div>
      </div>

      {/* Results */}
      <div ref={resultsRef} className="flex-1 overflow-y-auto">
        {isSearching ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="h-6 w-6 animate-spin text-[#007acc]" />
          </div>
        ) : searchResults.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-gray-500">
            {localQuery ? "No results found" : "Enter a search query"}
          </div>
        ) : (
          <div className="py-2">
            {/* Summary */}
            <div className="px-4 py-2 text-xs text-gray-500 border-b border-gray-200 dark:border-gray-700">
              Found {searchResults.length} results in {Object.keys(groupedResults).length} files
            </div>

            {/* Grouped Results */}
            {Object.entries(groupedResults).map(([fileId, results]) => {
              const file = openFiles.find((f) => f.id === fileId);
              if (!file) return null;

              return (
                <div key={fileId} className="border-b border-gray-200 dark:border-gray-700 last:border-0">
                  {/* File Header */}
                  <div className="flex items-center gap-2 px-4 py-2 bg-gray-50 dark:bg-gray-800 sticky top-0">
                    <File className="h-4 w-4 text-gray-400" />
                    <span className="text-sm font-medium">{file.path}</span>
                    <span className="text-xs text-gray-500">({results.length} results)</span>
                  </div>

                  {/* File Results */}
                  <div className="pl-4">
                    {results.map((result, idx) => (
                      <div
                        key={`${result.fileId}-${result.line}-${result.column}-${idx}`}
                        className="flex items-start gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
                        onClick={() => handleResultClick(result)}
                      >
                        <span className="text-xs text-gray-400 w-8 text-right">{result.line}</span>
                        <span className="text-xs text-gray-400 w-8">{result.column}</span>
                        <span className="flex-1 text-sm font-mono truncate">
                          {highlightMatch(result.context, localQuery, regex, caseSensitive)}
                        </span>
                        {localReplace && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 text-xs"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleReplace(result);
                            }}
                          >
                            <Replace className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// Helper to highlight matching text
function highlightMatch(
  text: string,
  query: string,
  isRegex: boolean,
  caseSensitive: boolean
): React.ReactNode {
  if (!query) return text;

  try {
    const flags = caseSensitive ? "g" : "gi";
    const pattern = isRegex
      ? new RegExp(`(${query})`, flags)
      : new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, flags);

    const parts = text.split(pattern);
    if (parts.length === 1) return text;

    return parts.map((part, i) =>
      pattern.test(part) ? (
        <mark key={i} className="bg-yellow-400 text-black rounded px-0.5">
          {part}
        </mark>
      ) : (
        part
      )
    );
  } catch {
    return text;
  }
}
