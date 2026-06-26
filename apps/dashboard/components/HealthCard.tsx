"use client";

import { useEffect, useState } from "react";
import { getHealth, type ApiResult, type Health } from "../lib/api";

export function HealthCard() {
  const [result, setResult] = useState<ApiResult<Health> | null>(null);

  useEffect(() => {
    let mounted = true;

    getHealth().then((nextResult) => {
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
      <section className="card cardWide">
        <p className="eyebrow">API Health</p>
        <h2>Loading API status</h2>
        <p className="stateText">Checking the Kairos API connection...</p>
      </section>
    );
  }

  if (!result.ok) {
    return (
      <section className="card cardWide">
        <p className="eyebrow">API Health</p>
        <h2>API unavailable</h2>
        <p className="errorText">{result.error}</p>
      </section>
    );
  }

  return (
    <section className="card cardWide">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">API Health</p>
          <h2>Connection</h2>
        </div>
        <span className="pill">{result.data.status}</span>
      </div>
      <dl className="statGrid">
        <div>
          <dt>Status</dt>
          <dd>{result.data.status}</dd>
        </div>
        <div>
          <dt>Service</dt>
          <dd>{result.data.service}</dd>
        </div>
        <div>
          <dt>Version</dt>
          <dd>{result.data.version}</dd>
        </div>
      </dl>
    </section>
  );
}
