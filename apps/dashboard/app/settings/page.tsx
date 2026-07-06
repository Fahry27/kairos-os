"use client";

import { useState, useEffect } from "react";
import { KAIROS_API_URL } from "../../lib/api";

type Section = "ai" | "appearance" | "storage" | "advanced";

// ---------------------------------------------------------------------------
// AI Providers
// ---------------------------------------------------------------------------

const PROVIDER_DISPLAY: Record<string, { label: string; description: string }> = {
  "ai.openai": { label: "OpenAI", description: "GPT-4o, o3, and other models." },
  "ai.gemini": { label: "Google Gemini", description: "Gemini models from Google AI Studio." },
  "ai.claude": { label: "Anthropic Claude", description: "Claude models from Anthropic." },
  "ai.ollama": { label: "Local AI (Ollama)", description: "Run models on your own machine." },
  "ai.codex": { label: "OpenAI Codex CLI", description: "Local code suggestions via Codex CLI." },
  "ai.deepseek": { label: "DeepSeek", description: "DeepSeek models via API key." },
  "ai.9router": { label: "9Router", description: "Router-based model access." },
};

interface ProviderInfo {
  id: string;
  name: string;
  provider_type: string;
  functional: boolean;
  status: string;
  auth_type: string;
  default_model?: string | null;
  configured_model?: string | null;
  external_api_calls_enabled: boolean;
  capabilities?: string[];
}

function AiSection() {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [configuring, setConfiguring] = useState<string | null>(null);
  const [apiKeyDraft, setApiKeyDraft] = useState("");
  const [savedKeys, setSavedKeys] = useState<Record<string, string>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    // Load saved keys
    try {
      const stored = localStorage.getItem("kairos.providerKeys");
      if (stored) setSavedKeys(JSON.parse(stored));
    } catch {}

    // Fetch providers
    fetch(`${KAIROS_API_URL}/api/v1/ai/provider-router/providers`)
      .then((res) => res.json())
      .then((data) => {
        setProviders(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Could not load providers");
        setLoading(false);
      });
  }, []);

  const handleConfigure = (providerId: string) => {
    setConfiguring(providerId);
    setApiKeyDraft(savedKeys[providerId] || "");
    setError("");
  };

  const handleSaveKey = (providerId: string) => {
    const trimmed = apiKeyDraft.trim();
    if (!trimmed) return;
    const next = { ...savedKeys, [providerId]: trimmed };
    setSavedKeys(next);
    if (typeof window !== "undefined") {
      localStorage.setItem("kairos.providerKeys", JSON.stringify(next));
    }
    setConfiguring(null);
    setApiKeyDraft("");
  };

  const handleRemoveKey = (providerId: string) => {
    const next = { ...savedKeys };
    delete next[providerId];
    setSavedKeys(next);
    if (typeof window !== "undefined") {
      localStorage.setItem("kairos.providerKeys", JSON.stringify(next));
    }
  };

  if (loading) return <p style={{ color: "var(--muted)", fontSize: 14 }}>Loading providers…</p>;
  if (error) return <p className="errorText">{error}</p>;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {providers.map((p) => {
        const display = PROVIDER_DISPLAY[p.id] || {
          label: p.name,
          description: "AI provider.",
        };
        const hasKey = !!savedKeys[p.id];
        const status = hasKey ? "Configured" : p.functional && p.external_api_calls_enabled ? "Connected" : p.functional ? "Local Only" : "Not Configured";

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
              <p style={{ fontWeight: 600, margin: 0, fontSize: 15 }}>{display.label}</p>
              <p style={{ color: "var(--muted)", margin: "4px 0 0", fontSize: 13 }}>
                {display.description}
                {p.configured_model ? ` · ${p.configured_model}` : ""}
                {p.default_model && !p.configured_model ? ` · ${p.default_model}` : ""}
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
                  <button onClick={() => handleSaveKey(p.id)} className="btnSmall" style={{ minWidth: 50 }}>
                    Save
                  </button>
                  <button
                    onClick={() => setConfiguring(null)}
                    className="btnSmall btnOutline"
                  >
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
                  background:
                    status === "Connected" ? "var(--accent-soft)" :
                    status === "Configured" ? "var(--accent-soft)" :
                    "transparent",
                  border: "1px solid var(--panel-border)",
                  color:
                    status === "Connected" || status === "Configured" ? "var(--accent)" :
                    "var(--muted)",
                }}
              >
                {status}
              </span>
              {hasKey ? (
                <button onClick={() => handleRemoveKey(p.id)} className="btnSmall btnOutline" style={{ fontSize: 12 }}>
                  Disconnect
                </button>
              ) : p.auth_type !== "none" && !p.functional ? (
                <button onClick={() => handleConfigure(p.id)} className="btnSmall" style={{ fontSize: 12 }}>
                  Configure
                </button>
              ) : null}
            </div>
          </div>
        );
      })}
      <p style={{ color: "var(--muted)", fontSize: 12, marginTop: 8 }}>
        API keys are stored in your browser only and never sent to the Kairos server.
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
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
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
        Your missions, tasks, conversations, and workspace state are stored in the
        Kairos database. The database type and location are configured by the
        administrator.
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
    if (typeof window !== "undefined") {
      if (apiKey.trim()) {
        localStorage.setItem("kairos.apiKey", apiKey.trim());
      } else {
        localStorage.removeItem("kairos.apiKey");
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div>
        <p style={{ fontWeight: 600, margin: "0 0 4px", fontSize: 15 }}>API Key</p>
        <p style={{ color: "var(--muted)", margin: "0 0 8px", fontSize: 13 }}>
          Required for protected API access. Set by your administrator for shared deployments.
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

      {/* Section tabs */}
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

      {/* Section content */}
      {activeSection === "ai" && <AiSection />}
      {activeSection === "appearance" && <AppearanceSection />}
      {activeSection === "storage" && <StorageSection />}
      {activeSection === "advanced" && <AdvancedSection />}
    </div>
  );
}
