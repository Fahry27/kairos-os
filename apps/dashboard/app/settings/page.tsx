"use client";

import { useState, useEffect } from "react";
import { KAIROS_API_URL } from "../../lib/api";

type Section = "ai" | "appearance" | "storage" | "advanced";

const PROVIDER_LABELS: Record<string, { label: string; description: string }> = {
  "ai.ollama": { label: "Ollama", description: "Run AI models locally on your machine." },
  "ai.openai": { label: "OpenAI", description: "GPT-4o, o3, and other models via API key." },
  "ai.gemini": { label: "Google Gemini", description: "Gemini models from Google AI Studio." },
  "ai.claude": { label: "Anthropic Claude", description: "Claude models from Anthropic." },
  "ai.codex": { label: "Codex CLI", description: "OpenAI Codex CLI for local code suggestions." },
  "ai.deepseek": { label: "DeepSeek", description: "DeepSeek models via API key." },
  "ai.9router": { label: "9Router", description: "Router-based model access." },
};

interface RouteProvider {
  id: string;
  name: string;
  functional: boolean;
  status: string;
  auth_type: string;
  default_model?: string | null;
  configured_model?: string | null;
  external_api_calls_enabled: boolean;
  supports_local: boolean;
  supports_chat: boolean;
  supports_tools: boolean;
}

interface ProviderRoute {
  providers: RouteProvider[];
  selected_provider: RouteProvider | null;
  dispatch_enabled: boolean;
  policy?: { reason?: string };
}

function AiSection() {
  const [route, setRoute] = useState<ProviderRoute | null>(null);
  const [loading, setLoading] = useState(true);
  const [configuring, setConfiguring] = useState<string | null>(null);
  const [apiKeyDraft, setApiKeyDraft] = useState("");
  const [savedKeys, setSavedKeys] = useState<Record<string, string>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    try {
      const stored = localStorage.getItem("kairos.providerKeys");
      if (stored) setSavedKeys(JSON.parse(stored));
    } catch {}

    fetch(`${KAIROS_API_URL}/api/v1/ai/provider-router/route`)
      .then((res) => {
        const ct = res.headers.get("content-type") || "";
        if (!res.ok) throw new Error(`Backend unavailable (${res.status})`);
        if (!ct.includes("application/json")) throw new Error("Unexpected response from backend");
        return res.json();
      })
      .then((data) => {
        setRoute(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(
          err instanceof Error
            ? err.message === "Failed to fetch" ? "Kairos backend is not running" : err.message
            : "Could not load providers"
        );
        setLoading(false);
      });
  }, []);

  const handleConfigure = (id: string) => {
    setConfiguring(id);
    setApiKeyDraft(savedKeys[id] || "");
    setError("");
  };

  const handleSaveKey = (id: string) => {
    const trimmed = apiKeyDraft.trim();
    if (!trimmed) return;
    const next = { ...savedKeys, [id]: trimmed };
    setSavedKeys(next);
    localStorage.setItem("kairos.providerKeys", JSON.stringify(next));
    setConfiguring(null);
    setApiKeyDraft("");
  };

  const handleRemoveKey = (id: string) => {
    const next = { ...savedKeys };
    delete next[id];
    setSavedKeys(next);
    localStorage.setItem("kairos.providerKeys", JSON.stringify(next));
  };

  function providerStatus(p: RouteProvider): string {
    const isOllama = p.id === "ai.ollama";
    if (isOllama && p.functional && route?.dispatch_enabled) return "Ready";
    if (isOllama && p.functional && !route?.dispatch_enabled) return "Not running";
    if (p.functional) return "Available";
    if (p.id === "ai.codex" && p.functional) return "Installed";
    return "Not configured";
  }

  function canConfigure(p: RouteProvider): boolean {
    return p.auth_type !== "none" || p.id === "ai.ollama";
  }

  if (loading) return <p style={{ color: "var(--muted)", fontSize: 14 }}>Checking providers…</p>;
  if (error) return <p className="errorText">{error}</p>;

  const providers = route?.providers || [];
  const hasAnyReady = route?.dispatch_enabled || false;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {!hasAnyReady && (
        <div
          style={{
            background: "var(--amber-soft)",
            border: "1px solid rgba(138, 90, 0, 0.25)",
            borderRadius: 6,
            padding: "12px 14px",
            fontSize: 14,
            color: "var(--amber)",
            marginBottom: 4,
          }}
        >
          No AI provider is ready. Install{" "}
          <a href="https://ollama.com" target="_blank" rel="noopener" style={{ color: "var(--accent)", fontWeight: 600 }}>
            Ollama
          </a>{" "}
          for local AI, or configure an API key for a cloud provider below.
        </div>
      )}

      {providers.map((p) => {
        const label = PROVIDER_LABELS[p.id] || { label: p.name, description: "" };
        const hasKey = !!savedKeys[p.id];
        const status = providerStatus(p);
        const statusColor =
          status === "Ready" || status === "Available" || status === "Installed"
            ? "var(--accent)"
            : status === "Not running"
              ? "var(--amber)"
              : "var(--muted)";
        const statusBg =
          status === "Ready" || status === "Available" || status === "Installed"
            ? "var(--accent-soft)"
            : status === "Not running"
              ? "var(--amber-soft)"
              : "transparent";

        return (
          <div
            key={p.id}
            style={{
              border: "1px solid var(--panel-border)",
              borderRadius: 6,
              padding: "14px 16px",
              background: "var(--panel)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <p style={{ fontWeight: 600, margin: 0, fontSize: 15 }}>{label.label}</p>
              <p style={{ color: "var(--muted)", margin: "4px 0 0", fontSize: 13 }}>
                {label.description}
                {p.default_model ? ` · ${p.default_model}` : ""}
              </p>
              {configuring === p.id && (
                <div style={{ display: "flex", gap: 6, marginTop: 10, alignItems: "center" }}>
                  <input
                    type="password"
                    placeholder="API key"
                    value={apiKeyDraft}
                    onChange={(e) => setApiKeyDraft(e.target.value)}
                    style={{ maxWidth: 260, fontSize: 13 }}
                    autoFocus
                  />
                  <button onClick={() => handleSaveKey(p.id)} className="btnSmall">
                    Save
                  </button>
                  <button onClick={() => setConfiguring(null)} className="btnSmall btnOutline">
                    Cancel
                  </button>
                </div>
              )}
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  padding: "4px 10px",
                  borderRadius: 999,
                  background: statusBg,
                  border: `1px solid var(--panel-border)`,
                  color: statusColor,
                }}
              >
                {status}
              </span>
              {hasKey ? (
                <button onClick={() => handleRemoveKey(p.id)} className="btnSmall btnOutline" style={{ fontSize: 12 }}>
                  Remove
                </button>
              ) : canConfigure(p) ? (
                <button onClick={() => handleConfigure(p.id)} className="btnSmall" style={{ fontSize: 12 }}>
                  Configure
                </button>
              ) : null}
            </div>
          </div>
        );
      })}

      <p style={{ color: "var(--muted)", fontSize: 12, marginTop: 4 }}>
        API keys are stored in your browser only.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Appearance
// ---------------------------------------------------------------------------

function AppearanceSection() {
  const [theme, setTheme] = useState<"system" | "light" | "dark">("system");

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0" }}>
        <div>
          <p style={{ fontWeight: 600, margin: 0, fontSize: 15 }}>Theme</p>
          <p style={{ color: "var(--muted)", margin: "2px 0 0", fontSize: 13 }}>
            {theme === "system" ? "Follows your system settings." : theme === "dark" ? "Always dark." : "Always light."}
          </p>
        </div>
        <select
          value={theme}
          onChange={(e) => setTheme(e.target.value as typeof theme)}
          style={{ width: "auto", fontSize: 13, minWidth: 120 }}
        >
          <option value="system">System</option>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Storage
// ---------------------------------------------------------------------------

function StorageSection() {
  return (
    <div>
      <p style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.6 }}>
        Your missions, tasks, and conversations are stored in the Kairos database.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Advanced
// ---------------------------------------------------------------------------

function AdvancedSection() {
  const [apiKey, setApiKey] = useState("");
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    if (apiKey.trim()) {
      localStorage.setItem("kairos.apiKey", apiKey.trim());
    } else {
      localStorage.removeItem("kairos.apiKey");
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div>
      <p style={{ fontWeight: 600, margin: "0 0 4px", fontSize: 15 }}>API Key</p>
      <p style={{ color: "var(--muted)", margin: "0 0 8px", fontSize: 13 }}>
        For shared deployments that require authentication.
      </p>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <input
          type="password"
          placeholder="Enter API key"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          style={{ maxWidth: 320, fontSize: 13 }}
        />
        <button onClick={handleSave} className="btnSmall" style={{ minWidth: 60 }}>
          {saved ? "Saved" : "Save"}
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Settings Page
// ---------------------------------------------------------------------------

const SECTIONS: { key: Section; label: string }[] = [
  { key: "ai", label: "AI" },
  { key: "appearance", label: "Appearance" },
  { key: "storage", label: "Storage" },
  { key: "advanced", label: "Advanced" },
];

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState<Section>("ai");

  return (
    <div style={{ maxWidth: 720, margin: "0 auto" }}>
      <h1 style={{ fontSize: 28, fontWeight: 720, margin: "0 0 24px" }}>Settings</h1>

      <div style={{ display: "flex", gap: 4, marginBottom: 28 }}>
        {SECTIONS.map((s) => (
          <button
            key={s.key}
            onClick={() => setActiveSection(s.key)}
            className={activeSection === s.key ? "" : "btnOutline"}
            style={{
              fontSize: 14,
              minHeight: 34,
              padding: "6px 16px",
              fontWeight: activeSection === s.key ? 700 : 500,
            }}
          >
            {s.label}
          </button>
        ))}
      </div>

      {activeSection === "ai" && <AiSection />}
      {activeSection === "appearance" && <AppearanceSection />}
      {activeSection === "storage" && <StorageSection />}
      {activeSection === "advanced" && <AdvancedSection />}
    </div>
  );
}
