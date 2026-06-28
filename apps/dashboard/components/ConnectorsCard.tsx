"use client";

import { useEffect, useState } from "react";
import { getConnectors, type ApiResult, type ConnectorManifest } from "../lib/api";

export function ConnectorsCard() {
  const [result, setResult] = useState<ApiResult<ConnectorManifest[]> | null>(null);

  useEffect(() => {
    let mounted = true;
    getConnectors().then((nextResult) => {
      if (mounted) {
        setResult(nextResult);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  if (!result) {
    return (
      <section className="card">
        <p className="eyebrow">Connectors</p>
        <h2>Loading...</h2>
      </section>
    );
  }

  if (!result.ok) {
    return (
      <section className="card">
        <p className="eyebrow">Connectors</p>
        <h2>Unavailable</h2>
        <p className="errorText">{result.error}</p>
      </section>
    );
  }

  const activeConnectors = result.data.filter((c) => c.enabled);

  return (
    <section className="card">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Connectors</p>
          <h2>External Services</h2>
        </div>
        <span className="pill">{activeConnectors.length} discovered</span>
      </div>
      <div style={{ marginTop: "1rem" }}>
        <ul
          style={{
            listStyle: "none",
            padding: 0,
            margin: 0,
            display: "flex",
            flexDirection: "column",
            gap: "0.5rem",
          }}
        >
          {activeConnectors.map((connector) => (
            <li
              key={connector.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "0.35rem 0.5rem",
                borderRadius: "4px",
                background: "var(--bg-secondary)",
                border: "1px solid var(--border-color)",
                fontSize: "0.8rem",
              }}
              title={connector.description}
            >
              <span style={{ fontWeight: 500 }}>{connector.name}</span>
              <span
                style={{
                  fontSize: "0.7rem",
                  color: "var(--text-secondary)",
                  background: "rgba(255,255,255,0.05)",
                  padding: "0.1rem 0.3rem",
                  borderRadius: "3px",
                }}
              >
                {connector.service_type}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
