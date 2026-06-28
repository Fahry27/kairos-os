"use client";

import { useEffect, useState } from "react";
import { getPlugins, type ApiResult, type PluginManifest } from "../lib/api";

export function ExtensionsCard() {
  const [result, setResult] = useState<ApiResult<PluginManifest[]> | null>(null);

  useEffect(() => {
    let mounted = true;
    getPlugins().then((nextResult) => {
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
        <p className="eyebrow">Extensions</p>
        <h2>Loading...</h2>
      </section>
    );
  }

  if (!result.ok) {
    return (
      <section className="card">
        <p className="eyebrow">Extensions</p>
        <h2>Unavailable</h2>
        <p className="errorText">{result.error}</p>
      </section>
    );
  }

  const activePlugins = result.data.filter((p) => p.enabled);
  const totalCommands = activePlugins.reduce((sum, p) => sum + (p.commands?.length || 0), 0);

  return (
    <section className="card">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Extensions</p>
          <h2>OS Registry</h2>
        </div>
        <span className="pill" title={`${totalCommands} commands available`}>
          {activePlugins.length} active ({totalCommands} commands)
        </span>
      </div>
      <div style={{ marginTop: "1rem" }}>
        <ul
          style={{
            listStyle: "none",
            padding: 0,
            margin: 0,
            display: "flex",
            flexWrap: "wrap",
            gap: "0.5rem",
          }}
        >
          {activePlugins.map((plugin) => (
            <li
              key={plugin.id}
              className="pill"
              style={{
                fontSize: "0.75rem",
                background: "var(--bg-secondary)",
                color: "var(--text-secondary)",
                border: "1px solid var(--border-color)",
                cursor: "help",
              }}
              title={plugin.description}
            >
              {plugin.name.replace(" Extension", "")}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
