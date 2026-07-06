"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { useKairosState } from "../../lib/state";
import { useMissions, useConversation } from "../../lib/runtime";

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

export default function HomePage() {
  const state = useKairosState();
  const missions = useMissions();

  const {
    sendMessage,
    isSending,
    conversations,
  } = useConversation();

  const [quickDraft, setQuickDraft] = useState("");

  const activeMissions = state.missions.filter(
    (m) => m.status === "executing" || m.status === "approved" || m.status === "planning"
  );
  const pendingTasks = state.decisions.filter(
    (d) => (d.status as string) === "open" || (d.status as string) === "pending"
  );

  const today = new Date(state.todayDate).toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  const handleQuickAsk = useCallback(async () => {
    const content = quickDraft.trim();
    if (!content || isSending) return;
    await sendMessage(content);
    setQuickDraft("");
  }, [quickDraft, sendMessage, isSending]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleQuickAsk();
    }
  };

  return (
    <div style={{ maxWidth: 640, margin: "0 auto" }}>
      <h1 style={{ fontSize: 28, fontWeight: 720, margin: "0 0 4px" }}>
        {getGreeting()}.
      </h1>
      <p style={{ color: "var(--muted)", margin: "0 0 32px", fontSize: 15 }}>
        {today}
      </p>

      {/* How can Kairos help? */}
      <div
        style={{
          background: "var(--panel)",
          border: "1px solid var(--panel-border)",
          borderRadius: 8,
          padding: "10px 14px",
          display: "flex",
          gap: 8,
          marginBottom: 32,
        }}
      >
        <input
          type="text"
          placeholder="What do you want Kairos to help with?"
          value={quickDraft}
          onChange={(e) => setQuickDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSending}
          style={{
            flex: 1,
            border: "none",
            background: "transparent",
            outline: "none",
            fontSize: 15,
          }}
          aria-label="Ask Kairos"
        />
        <button
          onClick={handleQuickAsk}
          disabled={!quickDraft.trim() || isSending}
          style={{ minWidth: 70, fontSize: 14 }}
        >
          {isSending ? "..." : "Ask"}
        </button>
      </div>

      {/* What was I working on? */}
      <div style={{ marginBottom: 32 }}>
        <h2
          style={{
            fontSize: 13,
            fontWeight: 600,
            margin: "0 0 12px",
            color: "var(--muted)",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
          }}
        >
          What you were working on
        </h2>

        {missions.loading ? (
          <p style={{ color: "var(--muted)", fontSize: 14 }}>Loading…</p>
        ) : activeMissions.length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {activeMissions.slice(0, 4).map((m) => (
              <Link
                key={m.id}
                href={`/work?mission=${m.id}`}
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <div
                  style={{
                    padding: "12px 14px",
                    border: "1px solid var(--panel-border)",
                    borderRadius: 6,
                    background: "var(--panel)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <div>
                    <p style={{ fontWeight: 600, margin: 0, fontSize: 15 }}>{m.name}</p>
                    {m.description && (
                      <p style={{ color: "var(--muted)", margin: "4px 0 0", fontSize: 13 }}>
                        {m.description.slice(0, 100)}
                      </p>
                    )}
                  </div>
                  <span
                    style={{
                      fontSize: 12,
                      color: m.status === "executing" ? "var(--accent)" : "var(--muted)",
                      fontWeight: 600,
                      textTransform: "capitalize",
                    }}
                  >
                    {m.status.replace("_", " ")}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <p style={{ color: "var(--muted)", fontSize: 14 }}>
            Nothing yet. Create a mission in{" "}
            <Link href="/work" style={{ color: "var(--accent)" }}>
              Work
            </Link>{" "}
            to get started.
          </p>
        )}
      </div>

      {/* What should I do today? */}
      {pendingTasks.length > 0 && (
        <div style={{ marginBottom: 32 }}>
          <h2
            style={{
              fontSize: 13,
              fontWeight: 600,
              margin: "0 0 12px",
              color: "var(--muted)",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            Needs attention
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {pendingTasks.slice(0, 4).map((t) => (
              <Link
                key={t.id}
                href="/work"
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <div
                  style={{
                    padding: "10px 14px",
                    border: "1px solid var(--panel-border)",
                    borderRadius: 6,
                    background: "var(--panel)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    fontSize: 14,
                  }}
                >
                  <span>{t.title}</span>
                  <span style={{ fontSize: 12, color: "var(--muted)", textTransform: "capitalize" }}>
                    {t.priority}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Recent conversations */}
      {conversations.length > 0 && (
        <div>
          <h2
            style={{
              fontSize: 13,
              fontWeight: 600,
              margin: "0 0 12px",
              color: "var(--muted)",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            Recent conversations
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {conversations.slice(0, 3).map((c) => (
              <Link
                key={c.id}
                href="/kai"
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <div
                  style={{
                    padding: "10px 14px",
                    border: "1px solid var(--panel-border)",
                    borderRadius: 6,
                    background: "var(--panel)",
                    fontSize: 14,
                  }}
                >
                  {c.title}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
