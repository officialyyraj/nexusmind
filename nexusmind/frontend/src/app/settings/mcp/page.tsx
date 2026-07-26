"use client";

import { useEffect, useState, useCallback } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api/client";
import type { MCPServerInfo, MCPTool, MCPStatus, MCPServerHealth, TransportType } from "@/types";
import { 
  Server, 
  Plus, 
  Trash2, 
  Play, 
  Square, 
  RefreshCw, 
  CheckCircle2, 
  XCircle, 
  AlertCircle,
  Loader2,
  Wrench,
  Shield,
  Clock
} from "lucide-react";

export default function MCPSettingsPage() {
  const [status, setStatus] = useState<MCPStatus | null>(null);
  const [servers, setServers] = useState<MCPServerInfo[]>([]);
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [health, setHealth] = useState<Record<string, MCPServerHealth>>({});
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newServer, setNewServer] = useState<{
    name: string;
    transport: TransportType;
    command: string;
    args: string;
    url: string;
    enabled: boolean;
    trusted: boolean;
  }>({
    name: "",
    transport: "stdio",
    command: "",
    args: "",
    url: "",
    enabled: true,
    trusted: true,
  });

  const fetchData = useCallback(async () => {
    try {
      const [statusData, serversData, toolsData, healthData] = await Promise.all([
        api.mcp.getStatus(),
        api.mcp.listServers(),
        api.mcp.listTools(),
        api.mcp.getHealth(),
      ]);
      
      setStatus(statusData);
      setServers(serversData);
      setTools(toolsData);
      
      // Convert health array to record
      const healthRecord: Record<string, MCPServerHealth> = {};
      if (Array.isArray(healthData)) {
        healthData.forEach(h => {
          healthRecord[h.server_name] = h;
        });
      }
      setHealth(healthRecord);
    } catch (error) {
      console.error("Failed to fetch MCP data:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleStartServer = async (name: string) => {
    setActionLoading(name);
    try {
      await api.mcp.startServer(name);
      await fetchData();
    } catch (error) {
      console.error("Failed to start server:", error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleStopServer = async (name: string) => {
    setActionLoading(name);
    try {
      await api.mcp.stopServer(name);
      await fetchData();
    } catch (error) {
      console.error("Failed to stop server:", error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRestartServer = async (name: string) => {
    setActionLoading(name);
    try {
      await api.mcp.restartServer(name);
      await fetchData();
    } catch (error) {
      console.error("Failed to restart server:", error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleAddServer = async () => {
    if (!newServer.name) return;
    
    setActionLoading("add");
    try {
      await api.mcp.addServer({
        name: newServer.name,
        transport: newServer.transport,
        command: newServer.command || undefined,
        args: newServer.args ? newServer.args.split(" ").filter(Boolean) : undefined,
        url: newServer.url || undefined,
        enabled: newServer.enabled,
        trusted: newServer.trusted,
        auto_reconnect: true,
        health_check_interval: 30,
        timeout: 30,
        allowlist: [],
        blocklist: [],
      });
      setShowAddForm(false);
      setNewServer({
        name: "",
        transport: "stdio",
        command: "",
        args: "",
        url: "",
        enabled: true,
        trusted: true,
      });
      await fetchData();
    } catch (error) {
      console.error("Failed to add server:", error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRemoveServer = async (name: string) => {
    if (!confirm(`Remove server "${name}"?`)) return;
    
    setActionLoading(name);
    try {
      await api.mcp.removeServer(name);
      await fetchData();
    } catch (error) {
      console.error("Failed to remove server:", error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRefreshTools = async (serverName: string) => {
    setActionLoading(serverName);
    try {
      await api.mcp.discoverTools(serverName);
      await fetchData();
    } catch (error) {
      console.error("Failed to refresh tools:", error);
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusIcon = (serverStatus: string) => {
    switch (serverStatus) {
      case "running":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "error":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "starting":
        return <Loader2 className="h-4 w-4 text-yellow-500 animate-spin" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getHealthStatus = (serverName: string) => {
    const h = health[serverName];
    if (!h) return null;
    return h.healthy ? (
      <span className="text-green-500 text-sm flex items-center gap-1">
        <CheckCircle2 className="h-3 w-3" />
        {h.latency_ms ? `${h.latency_ms.toFixed(0)}ms` : "Healthy"}
      </span>
    ) : (
      <span className="text-red-500 text-sm flex items-center gap-1">
        <XCircle className="h-3 w-3" />
        {h.error || "Unhealthy"}
      </span>
    );
  };

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="p-6 max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">MCP Settings</h1>
            <p className="text-muted-foreground">
              Manage Model Context Protocol servers and tools
            </p>
          </div>
          <Button onClick={() => setShowAddForm(!showAddForm)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Server
          </Button>
        </div>

        {/* Status Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <Server className="h-8 w-8 text-primary" />
                <div>
                  <p className="text-2xl font-bold">{status?.servers.total || 0}</p>
                  <p className="text-sm text-muted-foreground">Total Servers</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <Play className="h-8 w-8 text-green-500" />
                <div>
                  <p className="text-2xl font-bold">{status?.servers.running || 0}</p>
                  <p className="text-sm text-muted-foreground">Running</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <Wrench className="h-8 w-8 text-blue-500" />
                <div>
                  <p className="text-2xl font-bold">{status?.tools.total || 0}</p>
                  <p className="text-sm text-muted-foreground">Available Tools</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-8 w-8 text-red-500" />
                <div>
                  <p className="text-2xl font-bold">{status?.servers.error || 0}</p>
                  <p className="text-sm text-muted-foreground">Errors</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Add Server Form */}
        {showAddForm && (
          <Card>
            <CardHeader>
              <CardTitle>Add MCP Server</CardTitle>
              <CardDescription>Configure a new MCP server connection</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Server Name</Label>
                  <Input
                    id="name"
                    value={newServer.name}
                    onChange={(e) => setNewServer({ ...newServer, name: e.target.value })}
                    placeholder="filesystem"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="transport">Transport</Label>
                  <select
                    id="transport"
                    value={newServer.transport}
                    onChange={(e) => setNewServer({ ...newServer, transport: e.target.value as TransportType })}
                    className="mt-1 w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                  >
                    <option value="stdio">Stdio</option>
                    <option value="http">HTTP</option>
                    <option value="sse">SSE</option>
                  </select>
                </div>
              </div>
              
              {newServer.transport === "stdio" ? (
                <>
                  <div>
                    <Label htmlFor="command">Command</Label>
                    <Input
                      id="command"
                      value={newServer.command}
                      onChange={(e) => setNewServer({ ...newServer, command: e.target.value })}
                      placeholder="npx"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label htmlFor="args">Arguments (space-separated)</Label>
                    <Input
                      id="args"
                      value={newServer.args}
                      onChange={(e) => setNewServer({ ...newServer, args: e.target.value })}
                      placeholder="-y @modelcontextprotocol/server-filesystem /workspace"
                      className="mt-1"
                    />
                  </div>
                </>
              ) : (
                <div>
                  <Label htmlFor="url">URL</Label>
                  <Input
                    id="url"
                    value={newServer.url}
                    onChange={(e) => setNewServer({ ...newServer, url: e.target.value })}
                    placeholder="https://api.example.com/mcp"
                    className="mt-1"
                  />
                </div>
              )}

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newServer.enabled}
                    onChange={(e) => setNewServer({ ...newServer, enabled: e.target.checked })}
                  />
                  <span className="text-sm">Enabled</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newServer.trusted}
                    onChange={(e) => setNewServer({ ...newServer, trusted: e.target.checked })}
                  />
                  <span className="text-sm">Trusted</span>
                </label>
              </div>

              <div className="flex gap-2">
                <Button onClick={handleAddServer} disabled={actionLoading === "add" || !newServer.name}>
                  {actionLoading === "add" ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4 mr-2" />
                  )}
                  Add Server
                </Button>
                <Button variant="outline" onClick={() => setShowAddForm(false)}>
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Servers List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              Servers
            </CardTitle>
          </CardHeader>
          <CardContent>
            {servers.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">
                No MCP servers configured. Add a server to get started.
              </p>
            ) : (
              <div className="space-y-4">
                {servers.map((server) => (
                  <div
                    key={server.name}
                    className="border rounded-lg p-4 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(server.status)}
                        <div>
                          <h3 className="font-semibold">{server.name}</h3>
                          <p className="text-sm text-muted-foreground">
                            {server.transport} • {server.tools_count} tools
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {getHealthStatus(server.name)}
                        <div className="flex items-center gap-1 ml-4">
                          {server.trusted && (
                            <Badge variant="secondary" className="gap-1">
                              <Shield className="h-3 w-3" />
                              Trusted
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>

                    {server.last_error && (
                      <div className="text-sm text-red-500 bg-red-50 dark:bg-red-950 p-2 rounded">
                        Error: {server.last_error}
                      </div>
                    )}

                    <div className="flex gap-2">
                      {server.status === "running" ? (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleStopServer(server.name)}
                            disabled={actionLoading === server.name}
                          >
                            {actionLoading === server.name ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <>
                                <Square className="h-4 w-4 mr-1" />
                                Stop
                              </>
                            )}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRestartServer(server.name)}
                            disabled={actionLoading === server.name}
                          >
                            <RefreshCw className="h-4 w-4 mr-1" />
                            Restart
                          </Button>
                        </>
                      ) : (
                        <Button
                          size="sm"
                          onClick={() => handleStartServer(server.name)}
                          disabled={actionLoading === server.name || server.status === "starting"}
                        >
                          {actionLoading === server.name ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <>
                              <Play className="h-4 w-4 mr-1" />
                              Start
                            </>
                          )}
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRefreshTools(server.name)}
                        disabled={actionLoading === server.name || server.status !== "running"}
                      >
                        <RefreshCw className="h-4 w-4 mr-1" />
                        Refresh Tools
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveServer(server.name)}
                        disabled={actionLoading === server.name}
                        className="text-red-500 hover:text-red-600"
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        Remove
                      </Button>
                    </div>

                    {/* Server Tools */}
                    {tools.filter(t => t.server_name === server.name).length > 0 && (
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-sm font-medium mb-2">Available Tools:</p>
                        <div className="flex flex-wrap gap-2">
                          {tools.filter(t => t.server_name === server.name).map((tool) => (
                            <Badge key={tool.name} variant="outline" className="gap-1">
                              <Wrench className="h-3 w-3" />
                              {tool.name}
                              {tool.permissions.length > 0 && (
                                <Shield className="h-3 w-3 text-amber-500" />
                              )}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* All Tools */}
        {tools.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wrench className="h-5 w-5" />
                All Available Tools
              </CardTitle>
              <CardDescription>
                Tools discovered from all connected MCP servers
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(
                  tools.reduce((acc, tool) => {
                    if (!acc[tool.server_name]) acc[tool.server_name] = [];
                    acc[tool.server_name].push(tool);
                    return acc;
                  }, {} as Record<string, MCPTool[]>)
                ).map(([serverName, serverTools]) => (
                  <div key={serverName}>
                    <h3 className="text-sm font-medium mb-2 flex items-center gap-2">
                      <Server className="h-4 w-4" />
                      {serverName}
                      <Badge variant="secondary">{serverTools.length}</Badge>
                    </h3>
                    <div className="space-y-2 pl-6">
                      {serverTools.map((tool) => (
                        <div key={tool.name} className="text-sm">
                          <div className="flex items-center gap-2">
                            <code className="bg-muted px-2 py-0.5 rounded">{tool.name}</code>
                            {tool.tags.map(tag => (
                              <Badge key={tag} variant="outline" className="text-xs">{tag}</Badge>
                            ))}
                          </div>
                          <p className="text-muted-foreground mt-1">{tool.description}</p>
                          {tool.parameters.length > 0 && (
                            <div className="mt-2 text-xs text-muted-foreground">
                              Parameters: {tool.parameters.map(p => p.name).join(", ")}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
