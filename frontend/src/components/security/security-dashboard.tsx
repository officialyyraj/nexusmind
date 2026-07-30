"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/hooks/use-auth";
import { cn } from "@/lib/utils";
import {
  Shield,
  AlertTriangle,
  Key,
  Users,
  Activity,
  Clock,
  ChevronRight,
  Filter,
  Download,
  RefreshCw,
  ShieldCheck,
  ShieldAlert,
  AlertCircle,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface AuditLog {
  id: string;
  timestamp: string;
  action: string;
  level: string;
  user_id: string | null;
  ip_address: string | null;
  resource_type: string | null;
  details: Record<string, unknown>;
  status: string;
  error_message: string | null;
}

interface SecurityStats {
  failed_logins: number;
  api_key_usage: number;
  permission_changes: number;
  security_events: number;
  recent_events: AuditLog[];
}

const levelColors: Record<string, string> = {
  debug: "text-gray-400",
  info: "text-blue-400",
  warning: "text-yellow-400",
  error: "text-red-400",
  critical: "text-red-600",
};

const levelBgColors: Record<string, string> = {
  debug: "bg-gray-500",
  info: "bg-blue-500",
  warning: "bg-yellow-500",
  error: "bg-red-500",
  critical: "bg-red-700",
};

export function SecurityDashboard({ className }: { className?: string }) {
  const { user } = useAuth();
  const [stats, setStats] = useState<SecurityStats | null>(null);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [filter, setFilter] = useState<{
    action?: string;
    level?: string;
    startDate?: string;
    endDate?: string;
  }>({});

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Mock data for demonstration
      const mockStats: SecurityStats = {
        failed_logins: 3,
        api_key_usage: 156,
        permission_changes: 5,
        security_events: 8,
        recent_events: [
          {
            id: "1",
            timestamp: new Date().toISOString(),
            action: "auth:login",
            level: "info",
            user_id: "user-1",
            ip_address: "192.168.1.100",
            resource_type: null,
            details: {},
            status: "success",
            error_message: null,
          },
          {
            id: "2",
            timestamp: new Date(Date.now() - 300000).toISOString(),
            action: "auth:login_failed",
            level: "warning",
            user_id: null,
            ip_address: "10.0.0.50",
            resource_type: null,
            details: { reason: "Invalid password" },
            status: "failure",
            error_message: "Invalid credentials",
          },
          {
            id: "3",
            timestamp: new Date(Date.now() - 600000).toISOString(),
            action: "user:role_change",
            level: "warning",
            user_id: "admin-1",
            ip_address: "192.168.1.100",
            resource_type: "user",
            details: { old_role: "viewer", new_role: "developer", target_user_id: "user-2" },
            status: "success",
            error_message: null,
          },
        ],
      };

      const mockLogs: AuditLog[] = [
        {
          id: "1",
          timestamp: new Date().toISOString(),
          action: "auth:login",
          level: "info",
          user_id: "user-1",
          ip_address: "192.168.1.100",
          resource_type: null,
          details: {},
          status: "success",
          error_message: null,
        },
        {
          id: "2",
          timestamp: new Date(Date.now() - 300000).toISOString(),
          action: "auth:login_failed",
          level: "warning",
          user_id: null,
          ip_address: "10.0.0.50",
          resource_type: null,
          details: { reason: "Invalid password" },
          status: "failure",
          error_message: "Invalid credentials",
        },
        {
          id: "3",
          timestamp: new Date(Date.now() - 600000).toISOString(),
          action: "user:role_change",
          level: "warning",
          user_id: "admin-1",
          ip_address: "192.168.1.100",
          resource_type: "user",
          details: { old_role: "viewer", new_role: "developer" },
          status: "success",
          error_message: null,
        },
        {
          id: "4",
          timestamp: new Date(Date.now() - 900000).toISOString(),
          action: "apikey:create",
          level: "info",
          user_id: "user-1",
          ip_address: "192.168.1.100",
          resource_type: "api_key",
          details: { name: "Production Key" },
          status: "success",
          error_message: null,
        },
        {
          id: "5",
          timestamp: new Date(Date.now() - 1200000).toISOString(),
          action: "terminal:execute",
          level: "info",
          user_id: "user-1",
          ip_address: "192.168.1.100",
          resource_type: null,
          details: { command: "ls -la" },
          status: "success",
          error_message: null,
        },
      ];

      setStats(mockStats);
      setLogs(mockLogs);
    } catch (error) {
      console.error("Failed to fetch security data:", error);
    } finally {
      setLoading(false);
    }
  };

  const getActionLabel = (action: string): string => {
    const labels: Record<string, string> = {
      "auth:login": "Login",
      "auth:logout": "Logout",
      "auth:login_failed": "Failed Login",
      "user:create": "User Created",
      "user:role_change": "Role Changed",
      "project:create": "Project Created",
      "project:delete": "Project Deleted",
      "apikey:create": "API Key Created",
      "apikey:use": "API Key Used",
      "terminal:execute": "Terminal Command",
      "docker:container_start": "Container Started",
      "docker:container_stop": "Container Stopped",
      "plugin:install": "Plugin Installed",
    };
    return labels[action] || action;
  };

  if (loading) {
    return (
      <div className={cn("flex items-center justify-center h-full bg-gray-900", className)}>
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-400">Loading security data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full bg-gray-900", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <Shield className="h-6 w-6 text-blue-400" />
          <div>
            <h1 className="text-lg font-medium text-white">Security Dashboard</h1>
            <p className="text-sm text-gray-400">Monitor security events and audit logs</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <TabsList className="w-full justify-start rounded-none border-b border-gray-800 bg-gray-900 px-6">
            <TabsTrigger value="overview" className="data-[state=active]:bg-gray-800">
              <Shield className="h-4 w-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="audit-logs" className="data-[state=active]:bg-gray-800">
              <Activity className="h-4 w-4 mr-2" />
              Audit Logs
            </TabsTrigger>
            <TabsTrigger value="failed-logins" className="data-[state=active]:bg-gray-800">
              <AlertTriangle className="h-4 w-4 mr-2" />
              Failed Logins
            </TabsTrigger>
            <TabsTrigger value="api-keys" className="data-[state=active]:bg-gray-800">
              <Key className="h-4 w-4 mr-2" />
              API Keys
            </TabsTrigger>
            <TabsTrigger value="permissions" className="data-[state=active]:bg-gray-800">
              <Users className="h-4 w-4 mr-2" />
              Permissions
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="flex-1 overflow-y-auto p-6 m-0">
            {/* Stats Grid */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <Card className="bg-gray-800 border-gray-700">
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Failed Logins (24h)</p>
                      <p className="text-2xl font-bold text-red-400">{stats?.failed_logins || 0}</p>
                    </div>
                    <AlertCircle className="h-10 w-10 text-red-500/20" />
                  </div>
                  <Progress value={(stats?.failed_logins || 0) / 10 * 100} className="h-1 mt-2" />
                </CardContent>
              </Card>

              <Card className="bg-gray-800 border-gray-700">
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">API Key Usage (24h)</p>
                      <p className="text-2xl font-bold text-blue-400">{stats?.api_key_usage || 0}</p>
                    </div>
                    <Key className="h-10 w-10 text-blue-500/20" />
                  </div>
                  <Progress value={(stats?.api_key_usage || 0) / 200 * 100} className="h-1 mt-2" />
                </CardContent>
              </Card>

              <Card className="bg-gray-800 border-gray-700">
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Permission Changes (7d)</p>
                      <p className="text-2xl font-bold text-yellow-400">{stats?.permission_changes || 0}</p>
                    </div>
                    <Users className="h-10 w-10 text-yellow-500/20" />
                  </div>
                  <Progress value={(stats?.permission_changes || 0) / 20 * 100} className="h-1 mt-2" />
                </CardContent>
              </Card>

              <Card className="bg-gray-800 border-gray-700">
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Security Events (24h)</p>
                      <p className="text-2xl font-bold text-orange-400">{stats?.security_events || 0}</p>
                    </div>
                    <ShieldAlert className="h-10 w-10 text-orange-500/20" />
                  </div>
                  <Progress value={(stats?.security_events || 0) / 20 * 100} className="h-1 mt-2" />
                </CardContent>
              </Card>
            </div>

            {/* Recent Events */}
            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Recent Security Events
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {stats?.recent_events.map((event) => (
                    <div
                      key={event.id}
                      className="flex items-start gap-4 p-3 rounded-lg bg-gray-700/50"
                    >
                      <div className={cn("p-2 rounded-lg", levelBgColors[event.level])}>
                        <Info className="h-4 w-4 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-white">
                            {getActionLabel(event.action)}
                          </span>
                          <Badge
                            variant="secondary"
                            className={cn("text-xs capitalize", levelColors[event.level])}
                          >
                            {event.level}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-gray-400">
                          <span>{formatTime(event.timestamp)}</span>
                          {event.ip_address && <span>{event.ip_address}</span>}
                          {event.user_id && <span>User: {event.user_id}</span>}
                        </div>
                      </div>
                      <ChevronRight className="h-4 w-4 text-gray-500" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="audit-logs" className="flex-1 overflow-hidden m-0">
            {/* Filters */}
            <div className="flex items-center gap-4 p-4 border-b border-gray-800">
              <Select value={filter.action || "all"} onValueChange={(v) => setFilter({ ...filter, action: v === "all" ? undefined : v })}>
                <SelectTrigger className="w-48 bg-gray-800 border-gray-700">
                  <SelectValue placeholder="All Actions" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Actions</SelectItem>
                  <SelectItem value="auth:login">Login</SelectItem>
                  <SelectItem value="auth:logout">Logout</SelectItem>
                  <SelectItem value="user:role_change">Role Change</SelectItem>
                  <SelectItem value="apikey:create">API Key Created</SelectItem>
                  <SelectItem value="apikey:use">API Key Used</SelectItem>
                </SelectContent>
              </Select>

              <Select value={filter.level || "all"} onValueChange={(v) => setFilter({ ...filter, level: v === "all" ? undefined : v })}>
                <SelectTrigger className="w-48 bg-gray-800 border-gray-700">
                  <SelectValue placeholder="All Levels" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="info">Info</SelectItem>
                  <SelectItem value="warning">Warning</SelectItem>
                  <SelectItem value="error">Error</SelectItem>
                </SelectContent>
              </Select>

              <Button variant="outline" size="sm">
                <Filter className="h-4 w-4 mr-2" />
                More Filters
              </Button>
            </div>

            {/* Logs Table */}
            <ScrollArea className="h-[calc(100%-64px)]">
              <Table>
                <TableHeader>
                  <TableRow className="border-gray-800 hover:bg-transparent">
                    <TableHead className="text-gray-400">Timestamp</TableHead>
                    <TableHead className="text-gray-400">Action</TableHead>
                    <TableHead className="text-gray-400">Level</TableHead>
                    <TableHead className="text-gray-400">User</TableHead>
                    <TableHead className="text-gray-400">IP Address</TableHead>
                    <TableHead className="text-gray-400">Status</TableHead>
                    <TableHead className="text-gray-400">Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow key={log.id} className="border-gray-800 hover:bg-gray-800/50">
                      <TableCell className="text-gray-300">
                        {formatDateTime(log.timestamp)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-normal">
                          {getActionLabel(log.action)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={cn("capitalize", levelColors[log.level])}
                        >
                          {log.level}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-gray-300">
                        {log.user_id || "-"}
                      </TableCell>
                      <TableCell className="text-gray-300">
                        {log.ip_address || "-"}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={log.status === "success" ? "default" : "destructive"}
                          className="capitalize"
                        >
                          {log.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-gray-400 text-xs max-w-xs truncate">
                        {Object.keys(log.details).length > 0
                          ? JSON.stringify(log.details)
                          : "-"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="failed-logins" className="flex-1 overflow-y-auto p-6 m-0">
            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-red-400" />
                  Failed Login Attempts
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow className="border-gray-800">
                      <TableHead className="text-gray-400">Time</TableHead>
                      <TableHead className="text-gray-400">IP Address</TableHead>
                      <TableHead className="text-gray-400">User Agent</TableHead>
                      <TableHead className="text-gray-400">Reason</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow className="border-gray-800">
                      <TableCell className="text-gray-300">{formatDateTime(new Date().toISOString())}</TableCell>
                      <TableCell className="text-gray-300">10.0.0.50</TableCell>
                      <TableCell className="text-gray-400">Mozilla/5.0...</TableCell>
                      <TableCell>
                        <Badge variant="destructive">Invalid Password</Badge>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="api-keys" className="flex-1 overflow-y-auto p-6 m-0">
            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Key className="h-4 w-4" />
                  API Key Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-400">API key usage statistics and history will be displayed here.</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="permissions" className="flex-1 overflow-y-auto p-6 m-0">
            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Permission Changes
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-400">Permission change history will be displayed here.</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDateTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
