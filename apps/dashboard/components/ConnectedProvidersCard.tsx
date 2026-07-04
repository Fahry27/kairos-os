"use client";

import { useEffect, useState } from "react";
import { getRuntimeStatus, type RuntimeStatusResponse, type RuntimeProviderStatus, type ApiResult } from "../lib/api";

function ProviderStatusBadge({ provider, loading }: { provider: RuntimeProviderStatus | undefined, loading: boolean }) {
  if (loading) {
    return <span className="pill" style={{ color: "var(--muted)", borderColor: "var(--panel-border)", background: "transparent" }}>Checking...</span>;
  }
  
  if (!provider) {
    return <span className="pill" style={{ color: "var(--muted)", borderColor: "var(--panel-border)", background: "transparent" }}>Unknown</span>;
  }
  
  if (provider.status === "connected") {
    return <span className="pill" style={{ color: "#ffffff", borderColor: "var(--accent)", background: "var(--accent)" }} title={provider.message}>Connected</span>;
  } else if (provider.status === "offline") {
    return <span className="pill" style={{ color: "var(--amber)", borderColor: "var(--amber)", background: "var(--amber-soft)" }} title={provider.message}>Offline</span>;
  } else if (provider.status === "not_installed") {
    return <span className="pill" style={{ color: "var(--amber)", borderColor: "var(--amber)", background: "var(--amber-soft)" }} title={provider.message}>Not Installed</span>;
  } else if (provider.status === "not_authenticated") {
    return <span className="pill" style={{ color: "var(--amber)", borderColor: "var(--amber)", background: "var(--amber-soft)" }} title={provider.message}>Not Authenticated</span>;
  } else if (provider.status === "coming_soon") {
    return <span className="pill" style={{ color: "var(--muted)", borderColor: "var(--panel-border)", background: "transparent" }} title={provider.message}>Coming Soon</span>;
  } else {
    return <span className="pill" style={{ color: "#d73a49", borderColor: "#d73a49", background: "#ffeef0" }} title={provider.message || "Unknown Error"}>Error</span>;
  }
}

function getProviderDescription(id: string): string {
  if (id === "runtime.codex-cli") return "Official ChatGPT CLI session";
  if (id === "runtime.ollama") return "Local, open-source execution";
  if (id === "runtime.gemini") return "Native multimodal foundation model";
  return "AI Runtime";
}

export function ConnectedProvidersCard() {
  const [status, setStatus] = useState<ApiResult<RuntimeStatusResponse> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    
    getRuntimeStatus().then(res => {
      if (mounted) {
        setStatus(res);
        setLoading(false);
      }
    });
    
    return () => { mounted = false; };
  }, []);

  const runtimes = status?.ok ? status.data.runtimes : [];

  return (
    <div className="card">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Runtimes</p>
          <h2>Connected Providers</h2>
        </div>
      </div>
      
      <div className="tableWrap" style={{ marginTop: '16px' }}>
        <table>
          <thead>
            <tr>
              <th>Provider</th>
              <th>Description</th>
              <th style={{ textAlign: "right" }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {!loading && runtimes.map(runtime => (
              <tr key={runtime.id}>
                <td><strong style={runtime.status === "coming_soon" ? { color: "var(--muted)" } : undefined}>{runtime.name}</strong></td>
                <td style={runtime.status === "coming_soon" ? { color: "var(--muted)" } : undefined}>{getProviderDescription(runtime.id)}</td>
                <td style={{ textAlign: "right" }}><ProviderStatusBadge provider={runtime} loading={false} /></td>
              </tr>
            ))}
            {loading && (
              <tr>
                <td colSpan={3} style={{ textAlign: "center", color: "var(--muted)" }}>Checking runtime availability...</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
