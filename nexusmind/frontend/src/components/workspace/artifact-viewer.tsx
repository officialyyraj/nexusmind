"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark, oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import {
  Copy,
  Check,
  Download,
  Maximize2,
  Minimize2,
  FileText,
  Image,
  FileJson,
  Code,
  File,
  Eye,
  ZoomIn,
  ZoomOut,
  RotateCw,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useTheme } from "next-themes";

// Type helper for syntax highlighter styles
type SyntaxStyle = typeof oneDark;

interface ArtifactViewerProps {
  content: string;
  type?: "markdown" | "html" | "json" | "yaml" | "xml" | "image" | "svg" | "pdf" | "mermaid" | "text";
  title?: string;
  language?: string;
  className?: string;
  showCopyButton?: boolean;
  showDownloadButton?: boolean;
  showMaximizeButton?: boolean;
  onClose?: () => void;
}

type ViewMode = "preview" | "fullscreen" | "raw";

export function ArtifactViewer({
  content,
  type = "text",
  title = "Preview",
  language = "plaintext",
  className,
  showCopyButton = true,
  showDownloadButton = true,
  showMaximizeButton = true,
  onClose,
}: ArtifactViewerProps) {
  const { theme } = useTheme();
  const [viewMode, setViewMode] = useState<ViewMode>("preview");
  const [copied, setCopied] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [imageZoom, setImageZoom] = useState(100);
  const [pdfPage, setPdfPage] = useState(1);
  const [mermaidError, setMermaidError] = useState<string | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  // Detect type from content if not provided
  const detectedType = useMemo(() => {
    if (type !== "text") return type;
    
    const trimmed = content.trim();
    if (trimmed.startsWith("#") || trimmed.startsWith("- ") || trimmed.includes("```")) {
      return "markdown";
    }
    if (trimmed.startsWith("<!DOCTYPE") || trimmed.startsWith("<html")) {
      return "html";
    }
    if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
      return "json";
    }
    if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
      return "json";
    }
    if (trimmed.includes(":") && !trimmed.includes("<")) {
      return "yaml";
    }
    if (trimmed.startsWith("<?xml")) {
      return "xml";
    }
    if (trimmed.startsWith("data:image")) {
      return "image";
    }
    if (trimmed.startsWith("<svg")) {
      return "svg";
    }
    if (trimmed.startsWith("%PDF")) {
      return "pdf";
    }
    if (trimmed.includes("graph") || trimmed.includes("pie") || trimmed.includes("flowchart")) {
      return "mermaid";
    }
    return "text";
  }, [content, type]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  }, [content]);

  const handleDownload = useCallback(() => {
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = title || "artifact";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [content, title]);

  const handleZoomIn = () => setImageZoom((z) => Math.min(z + 25, 400));
  const handleZoomOut = () => setImageZoom((z) => Math.max(z - 25, 25));
  const handleZoomReset = () => setImageZoom(100);

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // Mermaid diagram rendering (simplified - would use mermaid library in production)
  const renderMermaid = () => {
    try {
      // In production, you'd use the mermaid library
      // For now, show the raw content in a code block
      return (
        <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <div className="text-center text-sm text-gray-500 dark:text-gray-400 mb-2">
            Mermaid Diagram Preview
          </div>
          <pre className="text-xs overflow-auto bg-gray-200 dark:bg-gray-700 p-2 rounded">
            {content}
          </pre>
        </div>
      );
    } catch (err) {
      setMermaidError(err instanceof Error ? err.message : "Failed to render diagram");
      return (
        <div className="p-4 bg-red-100 dark:bg-red-900/30 rounded-lg">
          <div className="text-red-600 dark:text-red-400 text-sm">
            Failed to render Mermaid diagram: {mermaidError}
          </div>
        </div>
      );
    }
  };

  const renderMarkdown = () => (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const inline = !match;
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const CodeBlock = SyntaxHighlighter as any;
            return !inline ? (
              <div className="relative group">
                <CodeBlock
                  style={theme === "dark" ? oneDark : oneLight}
                  language={match[1]}
                  PreTag="div"
                  className="rounded-lg !mt-2 !mb-2"
                >
                  {String(children).replace(/\n$/, "")}
                </CodeBlock>
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute top-2 right-2 h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={() => navigator.clipboard.writeText(String(children))}
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
          a({ node, children, href, ...props }) {
            return (
              <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline" {...props}>
                {children}
              </a>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );

  const renderImage = () => (
    <div className="flex flex-col items-center justify-center h-full bg-gray-100 dark:bg-gray-900">
      <div 
        className="relative overflow-auto max-w-full max-h-full"
        style={{ transform: `scale(${imageZoom / 100})`, transition: "transform 0.2s" }}
      >
        <img
          src={content}
          alt={title}
          className="max-w-none"
          onError={(e) => {
            e.currentTarget.src = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle'>Image not available</text></svg>";
          }}
        />
      </div>
      <div className="fixed bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-white dark:bg-gray-800 rounded-full shadow-lg px-4 py-2">
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleZoomOut}>
          <ZoomOut className="h-4 w-4" />
        </Button>
        <span className="text-sm font-medium w-16 text-center">{imageZoom}%</span>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleZoomIn}>
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleZoomReset}>
          <RotateCw className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );

  const renderSvg = () => (
    <div 
      className="flex items-center justify-center h-full bg-white dark:bg-gray-900 p-4"
      dangerouslySetInnerHTML={{ __html: content }}
    />
  );

  const renderJson = () => {
    try {
      const formatted = JSON.stringify(JSON.parse(content), null, 2);
      return (
        <SyntaxHighlighter
          language="json"
          style={theme === "dark" ? oneDark : oneLight}
          className="rounded-lg !m-0"
        >
          {formatted}
        </SyntaxHighlighter>
      );
    } catch {
      return <pre className="text-red-500">{content}</pre>;
    }
  };

  const renderYaml = () => (
    <SyntaxHighlighter
      language="yaml"
      style={theme === "dark" ? oneDark : oneLight}
      className="rounded-lg !m-0"
    >
      {content}
    </SyntaxHighlighter>
  );

  const renderXml = () => (
    <SyntaxHighlighter
      language="xml"
      style={theme === "dark" ? oneDark : oneLight}
      className="rounded-lg !m-0"
    >
      {content}
    </SyntaxHighlighter>
  );

  const renderHtml = () => (
    <iframe
      srcDoc={content}
      className="w-full h-full border-0"
      sandbox="allow-scripts"
      title={title}
    />
  );

  const renderPdf = () => (
    <div className="flex flex-col items-center justify-center h-full bg-gray-100 dark:bg-gray-900">
      <div className="text-center text-gray-500 dark:text-gray-400 mb-4">
        PDF Preview
        <br />
        <span className="text-sm">Page {pdfPage}</span>
      </div>
      <div className="bg-white shadow-lg p-4 rounded">
        <pre className="text-xs text-gray-600">{content.substring(0, 200)}...</pre>
      </div>
      <div className="flex items-center gap-4 mt-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setPdfPage((p) => Math.max(1, p - 1))}
          disabled={pdfPage <= 1}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setPdfPage((p) => p + 1)}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );

  const renderText = () => (
    <pre className="whitespace-pre-wrap font-mono text-sm">{content}</pre>
  );

  const renderRaw = () => (
    <SyntaxHighlighter
      language={language}
      style={theme === "dark" ? oneDark : oneLight}
      className="rounded-lg !m-0 h-full"
    >
      {content}
    </SyntaxHighlighter>
  );

  const renderContent = () => {
    if (viewMode === "raw") {
      return renderRaw();
    }

    switch (detectedType) {
      case "markdown":
        return renderMarkdown();
      case "html":
        return renderHtml();
      case "json":
        return renderJson();
      case "yaml":
        return renderYaml();
      case "xml":
        return renderXml();
      case "image":
        return renderImage();
      case "svg":
        return renderSvg();
      case "pdf":
        return renderPdf();
      case "mermaid":
        return renderMermaid();
      default:
        return renderText();
    }
  };

  const getTypeIcon = () => {
    switch (detectedType) {
      case "markdown":
      case "html":
        return <FileText className="h-4 w-4" />;
      case "json":
        return <FileJson className="h-4 w-4" />;
      case "image":
      case "svg":
        return <Image className="h-4 w-4" />;
      default:
        return <File className="h-4 w-4" />;
    }
  };

  const containerClass = isFullscreen
    ? "fixed inset-0 z-50 bg-white dark:bg-gray-900"
    : cn("flex flex-col h-full bg-white dark:bg-gray-900", className);

  return (
    <div className={containerClass}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          {getTypeIcon()}
          <span className="text-sm font-medium">{title}</span>
          <span className="text-xs text-gray-500 dark:text-gray-400 uppercase">{detectedType}</span>
        </div>
        <div className="flex items-center gap-1">
          {/* View Mode Toggle */}
          <Button
            variant="ghost"
            size="icon"
            className={cn("h-8 w-8", viewMode === "preview" ? "text-blue-500" : "text-gray-500")}
            onClick={() => setViewMode("preview")}
            title="Preview"
          >
            <Eye className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className={cn("h-8 w-8", viewMode === "raw" ? "text-blue-500" : "text-gray-500")}
            onClick={() => setViewMode("raw")}
            title="Raw"
          >
            <Code className="h-4 w-4" />
          </Button>

          {showCopyButton && (
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleCopy} title="Copy">
              {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
            </Button>
          )}
          {showDownloadButton && (
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleDownload} title="Download">
              <Download className="h-4 w-4" />
            </Button>
          )}
          {showMaximizeButton && (
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={toggleFullscreen} title={isFullscreen ? "Minimize" : "Maximize"}>
              {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </Button>
          )}
          {onClose && (
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
              ×
            </Button>
          )}
        </div>
      </div>

      {/* Content */}
      <div ref={contentRef} className="flex-1 overflow-auto p-4">
        {renderContent()}
      </div>
    </div>
  );
}
