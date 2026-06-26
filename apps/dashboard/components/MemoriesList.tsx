"use client";

import { useEffect, useState } from "react";
import { getMemories, type ApiResult, type Memory } from "../lib/api";

export function MemoriesList() {
  const [result, setResult] = useState<ApiResult<Memory[]> | null>(null);

  useEffect(() => {
    let mounted = true;

    getMemories().then((nextResult) => {
      if (mounted) {
        setResult(nextResult);
      }
    });

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <section className="card">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Memories</p>
          <h2>Knowledge</h2>
        </div>
      </div>
      {!result && <p className="stateText">Loading memories...</p>}
      {result && !result.ok && <p className="errorText">Unable to load memories: {result.error}</p>}
      {result?.ok && result.data.length === 0 && (
        <p className="stateText">No memories yet. Captured context will appear here.</p>
      )}
      {result?.ok && result.data.length > 0 && (
        <div className="stack">
          {result.data.map((memory) => (
            <article className="record" key={memory.id}>
              <div className="recordHeader">
                <h3>{memory.type}</h3>
                <span className="pill">{memory.importance}</span>
              </div>
              <p>{memory.content}</p>
              <div className="metaRow">
                <span>Source: {memory.source ?? "-"}</span>
                <span>Tags: {memory.tags?.length ? memory.tags.join(", ") : "-"}</span>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
