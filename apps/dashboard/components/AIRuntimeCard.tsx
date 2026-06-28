"use client";

import { useEffect, useState } from "react";
import { getAICapabilities, type ApiResult, type AICapabilities } from "../lib/api";

export function AIRuntimeCard() {
  const [result, setResult] = useState<ApiResult<AICapabilities> | null>(null);

  useEffect(() => {
    let mounted = true;
    getAICapabilities().then((r) => {
      if (mounted) setResult(r);
    });
    return () => {
      mounted = false;
    };
  }, []);

  if (!result) {
    return (
      <section className="card">
        <p className="eyebrow">AI Runtime</p>
        <h2>Loading...</h2>
      </section>
    );
  }

  if (!result.ok) {
    return (
      <section className="card">
        <p className="eyebrow">AI Runtime</p>
        <h2>Unavailable</h2>
        <p className="errorText">{result.error}</p>
      </section>
    );
  }

  const caps = result.data;

  return (
    <section className="card">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">AI Runtime</p>
          <h2>Kairos Intelligence</h2>
        </div>
        <span
          className="pill"
          style={{
            background: caps.ai_enabled
              ? "rgba(74, 222, 128, 0.15)"
              : "rgba(248, 113, 113, 0.15)",
            color: caps.ai_enabled ? "var(--accent)" : "#f87171",
            border: `1px solid ${caps.ai_enabled ? "var(--accent)" : "#f87171"}`,
          }}
        >
          {caps.ai_enabled ? "Enabled" : "Disabled"}
        </span>
      </div>

      <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {/* Provider row */}
        <div style={rowStyle}>
          <span style={labelStyle}>Provider</span>
          <span style={valueStyle}>{caps.provider}</span>
        </div>

        {/* Model row */}
        <div style={rowStyle}>
          <span style={labelStyle}>Model</span>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <span style={{ ...valueStyle, opacity: caps.model ? 1 : 0.45 }}>
              {caps.model ?? "not configured"}
            </span>
            {caps.model && caps.discovered_models_enabled && caps.provider === "ollama" && (
              <span
                className="pill"
                style={{
                  fontSize: "0.65rem",
                  padding: "0.1rem 0.35rem",
                  background: caps.configured_model_available
                    ? "rgba(74, 222, 128, 0.1)"
                    : "rgba(248, 113, 113, 0.1)",
                  color: caps.configured_model_available ? "var(--accent)" : "#f87171",
                }}
              >
                {caps.configured_model_available ? "Available" : "Missing"}
              </span>
            )}
          </div>
        </div>

        {/* Readiness row */}
        {caps.ai_enabled && caps.provider === "ollama" && (
          <div style={rowStyle}>
            <span style={labelStyle}>Readiness</span>
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <span 
                style={{ 
                  ...valueStyle, 
                  opacity: caps.provider_checked ? 1 : 0.65,
                  color: caps.provider_checked 
                    ? (caps.provider_reachable ? "var(--accent)" : "#f87171") 
                    : "var(--text-secondary)"
                }} 
                title={caps.provider_readiness_message || ""}
              >
                {!caps.provider_checked
                  ? "Not checked"
                  : caps.provider_reachable
                    ? "Reachable"
                    : "Not reachable"}
              </span>
              {caps.provider_reachable && caps.model_count !== null && (
                <span
                  className="pill"
                  style={{
                    fontSize: "0.65rem",
                    padding: "0.1rem 0.35rem",
                    background: "var(--bg-secondary)",
                    color: "var(--text-secondary)",
                    border: "1px solid var(--border-color)",
                  }}
                >
                  {caps.model_count} models
                </span>
              )}
            </div>
          </div>
        )}

        {/* Planning */}
        <div style={rowStyle}>
          <span style={labelStyle}>Planning</span>
          <span
            className="pill"
            style={{
              fontSize: "0.7rem",
              padding: "0.1rem 0.45rem",
              background: caps.planning_enabled
                ? "rgba(74, 222, 128, 0.1)"
                : "rgba(156,163,175,0.1)",
              color: caps.planning_enabled ? "var(--accent)" : "var(--text-secondary)",
            }}
          >
            {caps.planning_enabled ? "enabled" : "disabled"}
          </span>
        </div>

        {/* Execution — always locked in v2.0 */}
        <div style={rowStyle}>
          <span style={labelStyle}>Execution</span>
          <span
            className="pill"
            style={{
              fontSize: "0.7rem",
              padding: "0.1rem 0.45rem",
              background: "rgba(248, 113, 113, 0.1)",
              color: "#f87171",
            }}
            title="Execution is disabled in v2.0 — advisory planning only"
          >
            locked off
          </span>
        </div>

        {/* Dry-Run */}
        <div style={rowStyle}>
          <span style={labelStyle}>Dry-Run Contract</span>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <span
              className="pill"
              style={{
                fontSize: "0.7rem",
                padding: "0.1rem 0.45rem",
                background: caps.dry_run_enabled
                  ? "rgba(74, 222, 128, 0.1)"
                  : "rgba(156,163,175,0.1)",
                color: caps.dry_run_enabled ? "var(--accent)" : "var(--text-secondary)",
              }}
              title={`Max Context: ${caps.max_context_commands} commands, ${caps.max_context_plugins} plugins, ${caps.max_context_connectors} connectors`}
            >
              {caps.dry_run_enabled ? "enabled" : "disabled"}
            </span>
          </div>
        </div>

        {/* Divider */}
        <hr style={{ border: "none", borderTop: "1px solid var(--border-color)", margin: "0.25rem 0" }} />

        {/* Registry counts */}
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <CountBadge label="Plugins" value={caps.available_plugins} />
          <CountBadge label="Commands" value={caps.available_commands} />
          <CountBadge label="Connectors" value={caps.available_connectors} />
          {caps.dangerous_commands > 0 && (
            <CountBadge label="Dangerous" value={caps.dangerous_commands} danger />
          )}
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const rowStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  fontSize: "0.82rem",
};

const labelStyle: React.CSSProperties = {
  color: "var(--text-secondary)",
  fontWeight: 500,
};

const valueStyle: React.CSSProperties = {
  color: "var(--text-primary)",
  fontFamily: "monospace",
  fontSize: "0.78rem",
};

function CountBadge({
  label,
  value,
  danger,
}: {
  label: string;
  value: number;
  danger?: boolean;
}) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "0.35rem 0.6rem",
        borderRadius: "6px",
        background: danger ? "rgba(248,113,113,0.08)" : "var(--bg-secondary)",
        border: `1px solid ${danger ? "rgba(248,113,113,0.3)" : "var(--border-color)"}`,
        minWidth: "60px",
      }}
    >
      <span
        style={{
          fontSize: "1.1rem",
          fontWeight: 700,
          color: danger ? "#f87171" : "var(--text-primary)",
        }}
      >
        {value}
      </span>
      <span style={{ fontSize: "0.65rem", color: "var(--text-secondary)", marginTop: "1px" }}>
        {label}
      </span>
    </div>
  );
}
