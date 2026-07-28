"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  CheckCircle, 
  XCircle, 
  Plus, 
  Trash2, 
  RefreshCw, 
  Settings, 
  Eye, 
  EyeOff,
  MoreVertical,
  ExternalLink,
  Loader2,
  AlertCircle
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useToast } from "@/components/ui/use-toast";

// Provider definitions
const PROVIDERS = [
  {
    id: "openai",
    name: "OpenAI",
    description: "GPT-4, GPT-4o, and more",
    logo: "https://upload.wikimedia.org/wikipedia/commons/4/4d/OpenAI_Logo.svg",
    website: "https://openai.com",
    color: "bg-green-500",
    models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
  },
  {
    id: "anthropic",
    name: "Anthropic",
    description: "Claude 3.5 Sonnet, Claude 3 Opus",
    logo: "https://upload.wikimedia.org/wikipedia/commons/7/78/Anthropic_logo.svg",
    website: "https://anthropic.com",
    color: "bg-orange-500",
    models: ["claude-sonnet-4", "claude-3-5-sonnet", "claude-3-haiku"],
  },
  {
    id: "google",
    name: "Google Gemini",
    description: "Gemini 1.5 Pro, Gemini 1.5 Flash",
    logo: "https://upload.wikimedia.org/wikipedia/commons/0/0c/Google_Gemini_logo.svg",
    website: "https://ai.google.dev",
    color: "bg-blue-500",
    models: ["gemini-1.5-pro", "gemini-1.5-flash"],
  },
  {
    id: "groq",
    name: "Groq",
    description: "Fast inference with Llama, Mixtral",
    logo: "https://groq.com/wp-content/uploads/2024/03/groq-logo.svg",
    website: "https://console.groq.com",
    color: "bg-purple-500",
    models: ["llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
  },
  {
    id: "openrouter",
    name: "OpenRouter",
    description: "Access 100+ models from a single API",
    logo: "https://openrouter.ai/openrouter-logo.svg",
    website: "https://openrouter.ai",
    color: "bg-indigo-500",
    models: ["Many models available"],
  },
  {
    id: "together",
    name: "Together AI",
    description: "Open models at scale",
    logo: "https://together.ai/favicon.ico",
    website: "https://together.ai",
    color: "bg-pink-500",
    models: ["Llama-3-70b", "Mixtral-8x7B"],
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    description: "DeepSeek Coder, DeepSeek Chat",
    logo: "https://www.deepseek.com/favicon.ico",
    website: "https://platform.deepseek.com",
    color: "bg-cyan-500",
    models: ["deepseek-chat", "deepseek-coder"],
  },
  {
    id: "mistral",
    name: "Mistral AI",
    description: "Mistral Large, Mistral Small",
    logo: "https://mistral.ai/favicon.svg",
    website: "https://mistral.ai",
    color: "bg-orange-400",
    models: ["mistral-large-latest", "mistral-small-latest"],
  },
  {
    id: "xai",
    name: "xAI",
    description: "Grok models",
    logo: "https://x.ai/favicon.ico",
    website: "https://x.ai",
    color: "bg-slate-700",
    models: ["grok-2", "grok-2-mini"],
  },
  {
    id: "ollama",
    name: "Ollama (Local)",
    description: "Run models locally on your machine",
    logo: "https://ollama.ai/public/ollama-logo.svg",
    website: "https://ollama.ai",
    color: "bg-emerald-500",
    models: ["llama3.2", "codellama", "mistral"],
  },
];

// Mock connection type
interface ProviderConnection {
  id: string;
  provider: string;
  nickname: string | null;
  base_url: string | null;
  default_model: string | null;
  enabled: boolean;
  is_default: boolean;
  verification_status: string | null;
  last_verified: string | null;
  verification_error: string | null;
  use_count: number;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
}

export default function ProvidersPage() {
  const { toast } = useToast();
  const [connections, setConnections] = useState<ProviderConnection[]>([]);
  const [loading, setLoading] = useState(false);
  const [verifyingId, setVerifyingId] = useState<string | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);
  
  // Form state
  const [apiKey, setApiKey] = useState("");
  const [nickname, setNickname] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [defaultModel, setDefaultModel] = useState("");

  // Fetch connections
  const fetchConnections = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/v1/providers/", {
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setConnections(data);
      }
    } catch (error) {
      console.error("Failed to fetch connections:", error);
    } finally {
      setLoading(false);
    }
  };

  // Verify connection
  const verifyConnection = async (id: string) => {
    setVerifyingId(id);
    try {
      const response = await fetch(`/api/v1/providers/${id}/verify`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
      });
      const result = await response.json();
      
      if (result.success) {
        toast({
          title: "Verification successful",
          description: `Connected to ${result.verified_models?.length || 0} models`,
        });
      } else {
        toast({
          title: "Verification failed",
          description: result.message,
          variant: "destructive",
        });
      }
      
      await fetchConnections();
    } catch (error) {
      toast({
        title: "Verification failed",
        description: "An error occurred",
        variant: "destructive",
      });
    } finally {
      setVerifyingId(null);
    }
  };

  // Add connection
  const addConnection = async () => {
    if (!selectedProvider || !apiKey) return;
    
    try {
      const response = await fetch("/api/v1/providers/", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          provider: selectedProvider,
          api_key: apiKey,
          nickname: nickname || null,
          base_url: baseUrl || null,
          default_model: defaultModel || null,
        }),
      });
      
      if (response.ok) {
        toast({
          title: "Provider connected",
          description: "Your API key has been securely encrypted",
        });
        setShowAddDialog(false);
        setApiKey("");
        setNickname("");
        setBaseUrl("");
        setDefaultModel("");
        setSelectedProvider(null);
        await fetchConnections();
      } else {
        const error = await response.json();
        toast({
          title: "Connection failed",
          description: error.detail || "An error occurred",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Connection failed",
        description: "An error occurred",
        variant: "destructive",
      });
    }
  };

  // Delete connection
  const deleteConnection = async (id: string) => {
    try {
      const response = await fetch(`/api/v1/providers/${id}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
      });
      
      if (response.ok) {
        toast({
          title: "Provider disconnected",
          description: "Connection removed successfully",
        });
        await fetchConnections();
      }
    } catch (error) {
      toast({
        title: "Deletion failed",
        description: "An error occurred",
        variant: "destructive",
      });
    }
  };

  // Set default
  const setDefault = async (id: string) => {
    try {
      await fetch(`/api/v1/providers/${id}/default`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
      });
      await fetchConnections();
    } catch (error) {
      toast({
        title: "Failed to set default",
        description: "An error occurred",
        variant: "destructive",
      });
    }
  };

  // Toggle enabled
  const toggleEnabled = async (id: string, enabled: boolean) => {
    const endpoint = enabled ? `${id}/enable` : `${id}/disable`;
    try {
      await fetch(`/api/v1/providers/${endpoint}`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
      });
      await fetchConnections();
    } catch (error) {
      toast({
        title: "Failed to update",
        description: "An error occurred",
        variant: "destructive",
      });
    }
  };

  // Get provider info
  const getProviderInfo = (providerId: string) => {
    return PROVIDERS.find((p) => p.id === providerId);
  };

  // Mask API key for display
  const maskKey = (key: string) => {
    if (!key) return "••••••••";
    return key.slice(0, 4) + "••••••••" + key.slice(-4);
  };

  // Format date
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "Never";
    return new Date(dateStr).toLocaleDateString();
  };

  return (
    <AppShell>
      <div className="p-6 max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">AI Providers</h1>
            <p className="text-muted-foreground">
              Connect your own AI provider API keys
            </p>
          </div>
          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Provider
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Connect AI Provider</DialogTitle>
                <DialogDescription>
                  Add your own API key. Keys are encrypted with AES-256-GCM.
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  {PROVIDERS.map((provider) => (
                    <button
                      key={provider.id}
                      onClick={() => setSelectedProvider(provider.id)}
                      className={`p-4 rounded-lg border-2 text-left transition-colors ${
                        selectedProvider === provider.id
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/50"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${provider.color}`} />
                        <div>
                          <div className="font-medium">{provider.name}</div>
                          <div className="text-xs text-muted-foreground">
                            {provider.description}
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>

                {selectedProvider && (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="apiKey">API Key</Label>
                      <div className="relative">
                        <Input
                          id="apiKey"
                          type={showApiKey ? "text" : "password"}
                          value={apiKey}
                          onChange={(e) => setApiKey(e.target.value)}
                          placeholder="sk-..."
                          className="pr-10"
                        />
                        <button
                          type="button"
                          onClick={() => setShowApiKey(!showApiKey)}
                          className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        >
                          {showApiKey ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Your API key is encrypted before storage and never shared.
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="nickname">Nickname (optional)</Label>
                      <Input
                        id="nickname"
                        value={nickname}
                        onChange={(e) => setNickname(e.target.value)}
                        placeholder="My OpenAI Key"
                      />
                    </div>

                    {selectedProvider === "ollama" && (
                      <div className="space-y-2">
                        <Label htmlFor="baseUrl">Base URL</Label>
                        <Input
                          id="baseUrl"
                          value={baseUrl}
                          onChange={(e) => setBaseUrl(e.target.value)}
                          placeholder="http://localhost:11434"
                        />
                      </div>
                    )}

                    <div className="space-y-2">
                      <Label htmlFor="defaultModel">Default Model (optional)</Label>
                      <select
                        id="defaultModel"
                        value={defaultModel}
                        onChange={(e) => setDefaultModel(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-input bg-background"
                      >
                        <option value="">Auto-select</option>
                        {getProviderInfo(selectedProvider)?.models.map((model) => (
                          <option key={model} value={model}>
                            {model}
                          </option>
                        ))}
                      </select>
                    </div>
                  </>
                )}
              </div>
              
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowAddDialog(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={addConnection}
                  disabled={!selectedProvider || !apiKey}
                >
                  Connect Provider
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* Connected Providers */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Connected Providers</CardTitle>
            <CardDescription>
              Your encrypted API keys and connection status
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : connections.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No providers connected yet</p>
                <p className="text-sm">
                  Add a provider above to get started
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {connections.map((conn) => {
                  const provider = getProviderInfo(conn.provider);
                  const isVerifying = verifyingId === conn.id;
                  
                  return (
                    <div
                      key={conn.id}
                      className={`p-4 rounded-lg border ${
                        conn.enabled ? "border-border" : "border-border opacity-60"
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-4">
                          <div className={`w-3 h-3 rounded-full mt-1.5 ${
                            conn.enabled ? provider?.color || "bg-green-500" : "bg-gray-400"
                          }`} />
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">
                                {provider?.name || conn.provider}
                              </span>
                              {conn.is_default && (
                                <Badge variant="secondary" className="text-xs">
                                  Default
                                </Badge>
                              )}
                              {conn.enabled ? (
                                <Badge
                                  variant="outline"
                                  className="text-xs text-green-600 border-green-600"
                                >
                                  <CheckCircle className="h-3 w-3 mr-1" />
                                  Connected
                                </Badge>
                              ) : (
                                <Badge
                                  variant="outline"
                                  className="text-xs text-gray-500"
                                >
                                  <XCircle className="h-3 w-3 mr-1" />
                                  Disabled
                                </Badge>
                              )}
                            </div>
                            <div className="text-sm text-muted-foreground mt-1">
                              {conn.nickname && (
                                <span className="mr-3">{conn.nickname}</span>
                              )}
                              <span>API Key: ••••••••</span>
                              {conn.default_model && (
                                <span className="mx-3">•</span>
                              )}
                              {conn.default_model && (
                                <span>Model: {conn.default_model}</span>
                              )}
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                              Used {conn.use_count} times • Last used {formatDate(conn.last_used_at)}
                              {conn.verification_status === "verified" && (
                                <span className="mx-2">•</span>
                              )}
                              {conn.verification_status === "verified" && (
                                <span className="text-green-600">
                                  Verified {formatDate(conn.last_verified)}
                                </span>
                              )}
                              {conn.verification_status === "failed" && (
                                <>
                                  <span className="mx-2">•</span>
                                  <span className="text-red-600">
                                    Verification failed
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => verifyConnection(conn.id)}
                            disabled={isVerifying}
                          >
                            {isVerifying ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <RefreshCw className="h-4 w-4" />
                            )}
                            <span className="ml-2 hidden sm:inline">
                              {conn.verification_status === "verified" ? "Re-verify" : "Verify"}
                            </span>
                          </Button>
                          
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              {!conn.is_default && (
                                <DropdownMenuItem onClick={() => setDefault(conn.id)}>
                                  <Settings className="h-4 w-4 mr-2" />
                                  Set as Default
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuItem
                                onClick={() => toggleEnabled(conn.id, !conn.enabled)}
                              >
                                {conn.enabled ? (
                                  <>
                                    <XCircle className="h-4 w-4 mr-2" />
                                    Disable
                                  </>
                                ) : (
                                  <>
                                    <CheckCircle className="h-4 w-4 mr-2" />
                                    Enable
                                  </>
                                )}
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={() => deleteConnection(conn.id)}
                                className="text-red-600"
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Disconnect
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Available Providers */}
        <Card>
          <CardHeader>
            <CardTitle>Available Providers</CardTitle>
            <CardDescription>
              All supported BYOK providers
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {PROVIDERS.map((provider) => {
                const hasConnection = connections.some(
                  (c) => c.provider === provider.id
                );
                
                return (
                  <div
                    key={provider.id}
                    className={`p-4 rounded-lg border ${
                      hasConnection ? "border-green-200 bg-green-50" : "border-border"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className={`w-3 h-3 rounded-full ${provider.color}`} />
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{provider.name}</span>
                            {hasConnection && (
                              <Badge variant="secondary" className="text-xs">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Connected
                              </Badge>
                            )}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {provider.description}
                          </div>
                        </div>
                      </div>
                      
                      {!hasConnection && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedProvider(provider.id);
                            setShowAddDialog(true);
                          }}
                        >
                          <Plus className="h-4 w-4 mr-1" />
                          Connect
                        </Button>
                      )}
                      
                      <a
                        href={provider.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-muted-foreground hover:text-foreground"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
