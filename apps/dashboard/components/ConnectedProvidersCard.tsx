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
    <div className="card" style={{ padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <h3 style={{ fontSize: "1rem", margin: 0 }}>Connected Providers</h3>
      </div>
      
      <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
        {loading && <span className="stateText" style={{ fontSize: "0.85rem" }}>Checking runtime availability...</span>}
        {!loading && runtimes.map(runtime => (
          <div key={runtime.id} style={{ display: "flex", alignItems: "center", gap: "8px", background: "var(--background)", padding: "4px 12px", borderRadius: "100px", border: "1px solid var(--panel-border)" }}>
            <span style={{ fontSize: "0.85rem", fontWeight: 500, color: runtime.status === "coming_soon" ? "var(--muted)" : "inherit" }}>
              {runtime.name}
            </span>
            <ProviderStatusBadge provider={runtime} loading={false} />
          </div>
        ))}
      </div>
    </div>
  );
}
