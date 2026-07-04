"use client";

import { useEffect, useState } from "react";
import { getProviderReadiness, type AIProviderReadiness, type ApiResult } from "../lib/api";

function ProviderStatusBadge({ readiness, loading }: { readiness: ApiResult<AIProviderReadiness> | null, loading: boolean }) {
  if (loading) {
    return <span className="pill" style={{ color: "var(--muted)", borderColor: "var(--panel-border)", background: "transparent" }}>Checking...</span>;
  }
  
  if (!readiness) {
    return <span className="pill" style={{ color: "var(--muted)", borderColor: "var(--panel-border)", background: "transparent" }}>Unknown</span>;
  }
  
  if (!readiness.ok) {
    return <span className="pill" style={{ color: "var(--text)", borderColor: "var(--panel-border)", background: "var(--panel)" }} title={readiness.error}>Error</span>;
  }
  
  const state = readiness.data.state;
  if (state === "ok") {
    return <span className="pill" style={{ color: "#ffffff", borderColor: "var(--accent)", background: "var(--accent)" }}>Connected</span>;
  } else if (state === "unconfigured") {
    return <span className="pill" style={{ color: "var(--amber)", borderColor: "var(--amber)", background: "var(--amber-soft)" }}>Not Configured</span>;
  } else {
    return <span className="pill" style={{ color: "#d73a49", borderColor: "#d73a49", background: "#ffeef0" }} title={readiness.data.error_type || "Unknown Error"}>Offline</span>;
  }
}

export function ConnectedProvidersCard() {
  const [codex, setCodex] = useState<ApiResult<AIProviderReadiness> | null>(null);
  const [ollama, setOllama] = useState<ApiResult<AIProviderReadiness> | null>(null);
  const [loadingCodex, setLoadingCodex] = useState(true);
  const [loadingOllama, setLoadingOllama] = useState(true);

  useEffect(() => {
    let mounted = true;
    
    getProviderReadiness("ai.codex").then(res => {
      if (mounted) {
        setCodex(res);
        setLoadingCodex(false);
      }
    });
    
    getProviderReadiness("ai.ollama").then(res => {
      if (mounted) {
        setOllama(res);
        setLoadingOllama(false);
      }
    });
    
    return () => { mounted = false; };
  }, []);

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
            <tr>
              <td><strong>OpenAI Codex</strong></td>
              <td>Official ChatGPT CLI session</td>
              <td style={{ textAlign: "right" }}><ProviderStatusBadge readiness={codex} loading={loadingCodex} /></td>
            </tr>
            <tr>
              <td><strong>Ollama</strong></td>
              <td>Local, open-source execution</td>
              <td style={{ textAlign: "right" }}><ProviderStatusBadge readiness={ollama} loading={loadingOllama} /></td>
            </tr>
            <tr>
              <td><strong style={{ color: "var(--muted)" }}>Google Gemini</strong></td>
              <td style={{ color: "var(--muted)" }}>Native multimodal foundation model</td>
              <td style={{ textAlign: "right" }}>
                <span className="pill" style={{ color: "var(--muted)", borderColor: "var(--panel-border)", background: "transparent" }}>Coming Soon</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
