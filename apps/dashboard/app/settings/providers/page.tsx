"use client";

import { useEffect, useState, useCallback } from "react";
import { KAIROS_API_URL } from "../../../lib/api";

interface ProviderInfo {
  id: string;
  name: string;
  provider_type: string;
  functional: boolean;
  status: string;
  auth_type: string;
  default_model?: string | null;
  supports_local: boolean;
  supports_chat: boolean;
  supports_tools: boolean;
  supports_vision: boolean;
  notes?: string[];
  configured_model?: string | null;
  external_api_calls_enabled: boolean;
  capabilities?: string[];
}

interface ProviderSession {
  provider_id: string;
  status: string;
  session_id: string;
}

const PROVIDER_DOCS: Record<string, { description: string; setupGuide: string; envVars: string[] }> = {
  "ai.codex": {
    description: "OpenAI Codex CLI — local execution via `codex exec`.",
    setupGuide: "Install Codex CLI (`npm i -g @openai/codex`), then run `codex` to authenticate.",
    envVars: [],
  },
  "ai.ollama": {
    description: "Ollama local LLM runtime — runs models on your machine.",
    setupGuide: "Install Ollama from https://ollama.com, then `ollama pull llama3.2`.",
    envVars: ["KAIROS_OLLAMA_BASE_URL"],
  },
  "ai.openai": {
    description: "OpenAI API — GPT-4o, o3, and other models via API key.",
    setupGuide: "Get an API key from https://platform.openai.com/api-keys.",
    envVars: ["OPENAI_API_KEY"],
  },
  "ai.gemini": {
    description: "Google Gemini — via Google AI Studio API key.",
    setupGuide: "Get an API key from https://aistudio.google.com/apikey.",
    envVars: ["GEMINI_API_KEY", "KAIROS_GEMINI_API_KEY"],
  },
  "ai.claude": {
    description: "Anthropic Claude — via API key.",
    setupGuide: "Get an API key from https://console.anthropic.com/.",
    envVars: ["ANTHROPIC_API_KEY"],
  },
};

function statusBadge(provider: ProviderInfo): { text: string; className: string } {
  if (provider.functional && provider.external_api_calls_enabled) {
    return { text: "Ready", className: "bg-green-100 text-green-700 border-green-200" };
  }
  if (provider.functional) {
    return { text: "Local Only", className: "bg-blue-100 text-blue-700 border-blue-200" };
  }
  if (provider.status === "metadata_only") {
    return { text: "Not Configured", className: "bg-gray-200 text-gray-600 border-gray-300" };
  }
  return { text: provider.status, className: "bg-yellow-100 text-yellow-700 border-yellow-200" };
}

export default function ProvidersSettingsPage() {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [sessions, setSessions] = useState<ProviderSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [error, setError] = useState("");

  const fetchProviders = useCallback(async () => {
    try {
      const res = await fetch(`${KAIROS_API_URL}/api/v1/ai/provider-router/providers`);
      if (!res.ok) throw new Error("Failed to fetch providers");
      const data = await res.json();
      setProviders(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  }, []);

  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(`${KAIROS_API_URL}/api/v1/auth/sessions`);
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
      }
    } catch {
      // Sessions endpoint may not be available — that's OK
    }
  }, []);

  useEffect(() => {
    Promise.all([fetchProviders(), fetchSessions()]).finally(() => setLoading(false));
  }, [fetchProviders, fetchSessions]);

  const handleConnect = async (providerId: string) => {
    setConnecting(providerId);
    setError("");
    try {
      const res = await fetch(`${KAIROS_API_URL}/api/v1/auth/providers/${providerId}/connect`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Connection failed");
      await Promise.all([fetchProviders(), fetchSessions()]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setConnecting(null);
    }
  };

  const hasActiveSession = (providerId: string) =>
    sessions.some((s) => s.provider_id === providerId && s.status === "active");

  return (
    <div className="p-8 max-w-4xl mx-auto font-sans text-gray-900">
      <h1 className="text-3xl font-bold mb-2">Provider Configuration</h1>
      <p className="text-gray-500 mb-8">
        Connected to <code className="bg-gray-100 px-1 rounded">{KAIROS_API_URL}</code>
      </p>

      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded mb-4 text-sm">{error}</div>
      )}

      <section className="space-y-4">
        {loading ? (
          <p className="text-gray-400 text-sm">Loading providers...</p>
        ) : (
          providers.map((provider) => {
            const badge = statusBadge(provider);
            const doc = PROVIDER_DOCS[provider.id] ?? {
              description: "AI provider.",
              setupGuide: "No setup guide available.",
              envVars: [],
            };

            return (
              <div
                key={provider.id}
                className="bg-white p-5 rounded-lg shadow-sm border border-gray-200"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-lg">{provider.name}</h3>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${badge.className}`}>
                        {badge.text}
                      </span>
                      {hasActiveSession(provider.id) && (
                        <span className="px-2 py-0.5 bg-green-100 text-green-700 border border-green-200 rounded-full text-xs font-medium">
                          Active Session
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{doc.description}</p>

                    {doc.envVars.length > 0 && !provider.functional && (
                      <div className="mt-2">
                        <p className="text-xs font-medium text-gray-700">Required environment variables:</p>
                        <ul className="text-xs text-gray-500 list-disc list-inside">
                          {doc.envVars.map((env) => (
                            <li key={env}>
                              <code className="bg-gray-100 px-1 rounded">{env}</code>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {doc.envVars.length === 0 && !provider.functional && (
                      <p className="text-xs text-gray-500 mt-2">{doc.setupGuide}</p>
                    )}

                    {provider.configured_model && (
                      <p className="text-xs text-gray-400 mt-1">
                        Configured model: <code>{provider.configured_model}</code>
                      </p>
                    )}
                    {provider.default_model && (
                      <p className="text-xs text-gray-400">
                        Default model: <code>{provider.default_model}</code>
                      </p>
                    )}

                    <div className="flex gap-3 mt-2">
                      {provider.capabilities?.map((cap: string) => (
                        <span key={cap} className="text-xs text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded">
                          {cap}
                        </span>
                      ))}
                    </div>
                  </div>

                  {provider.auth_type !== "none" && !provider.functional && (
                    <button
                      onClick={() => handleConnect(provider.id)}
                      disabled={connecting === provider.id}
                      className="ml-4 px-4 py-2 bg-black text-white text-sm font-medium rounded hover:bg-gray-800 disabled:opacity-50 transition-colors shrink-0"
                    >
                      {connecting === provider.id ? "Connecting..." : "Connect"}
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </section>

      {sessions.length > 0 && (
        <section className="mt-8 border-t pt-4">
          <h3 className="text-sm font-semibold mb-3 text-gray-600 uppercase tracking-wider">
            Debug: Active Sessions
          </h3>
          <ul className="text-xs text-gray-600 space-y-2">
            {sessions.map((s) => (
              <li key={s.session_id} className="font-mono bg-gray-100 p-2 rounded">
                <span className="font-bold">{s.provider_id}</span> — {s.status}{" "}
                <span className="text-gray-400">({s.session_id})</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}


