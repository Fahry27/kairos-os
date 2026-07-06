"use client";

import SurfacePageHeader from "../../components/shell/SurfacePageHeader";
import SurfaceCard from "../../components/shell/SurfaceCard";
import FoundationNotice from "../../components/shell/FoundationNotice";
import { useKairosState } from "../../lib/state";

const SUGGESTION_CHIPS = [
  "What's on my schedule today?",
  "Review my open decisions.",
  "Summarize this week's progress.",
  "Plan my next mission.",
  "What should I focus on right now?",
];

/**
 * Ask Kai — production chat architecture.
 *
 * Sections:
 *   - Context bar (active mission, workspace, recent context)
 *   - Message thread area
 *   - Empty state
 *   - Suggestion chips
 *   - Prompt input (sticky bottom)
 *
 * No API calls. No mock messages. Pure architecture.
 */
export default function AskKaiPage() {
  const state = useKairosState();
  const activeMission = state.missions.find((m) => m.id === state.assistant.activeMissionId);
  const activeWorkspace = state.workspaces.find((w) => w.id === state.assistant.activeWorkspaceId);

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", display: "flex", flexDirection: "column", minHeight: "calc(100vh - 64px)" }}>
      <FoundationNotice label="Ask Kai" />

      <SurfacePageHeader
        title="Ask Kai"
        description="Your conversational interface to the AI Operating System."
      />

      {/* Context bar */}
      {(activeMission || activeWorkspace) && (
        <SurfaceCard eyebrow="Active Context" badge="Session">
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            {activeMission && (
              <div>
                <span style={{ fontSize: 12, color: "var(--muted)", fontWeight: 700, textTransform: "uppercase" }}>
                  Mission
                </span>
                <p style={{ margin: "4px 0 0", fontWeight: 600 }}>{activeMission.name}</p>
              </div>
            )}
            {activeWorkspace && (
              <div>
                <span style={{ fontSize: 12, color: "var(--muted)", fontWeight: 700, textTransform: "uppercase" }}>
                  Workspace
                </span>
                <p style={{ margin: "4px 0 0", fontWeight: 600 }}>{activeWorkspace.goal}</p>
              </div>
            )}
          </div>
        </SurfaceCard>
      )}

      {/* Message area */}
      <div
        style={{
          flex: 1,
          marginTop: activeMission || activeWorkspace ? 16 : 0,
          background: "var(--panel)",
          border: "1px solid var(--panel-border)",
          borderRadius: "8px",
          padding: "32px 24px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          minHeight: 320,
        }}
      >
        {/* Empty state */}
        <div style={{ textAlign: "center", maxWidth: 480, marginBottom: 28 }}>
          <h2 style={{ fontSize: 22, fontWeight: 720, margin: "0 0 8px" }}>
            Ask Kai anything
          </h2>
          <p className="stateText" style={{ lineHeight: 1.6 }}>
            Your conversation with Kairos will appear here.
            Ask questions, give instructions, plan work, or reflect on what you&apos;ve accomplished.
          </p>
        </div>

        {/* Suggestion chips */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", maxWidth: 520 }}>
          {SUGGESTION_CHIPS.map((chip) => (
            <button
              key={chip}
              disabled
              className="btnOutline btnSmall"
              style={{
                color: "var(--muted)",
                borderColor: "var(--panel-border)",
                cursor: "default",
                fontSize: 13,
                fontWeight: 500,
              }}
            >
              {chip}
            </button>
          ))}
        </div>
      </div>

      {/* Prompt input */}
      <div style={{ marginTop: 16, marginBottom: 16 }}>
        <div
          style={{
            display: "flex",
            gap: 8,
            background: "var(--panel)",
            border: "1px solid var(--panel-border)",
            borderRadius: "8px",
            padding: "8px 12px",
          }}
        >
          <input
            type="text"
            placeholder="Ask Kai something..."
            disabled
            style={{
              flex: 1,
              border: "none",
              background: "transparent",
              outline: "none",
              fontSize: 15,
              color: "var(--muted)",
            }}
            aria-label="Ask Kai prompt"
          />
          <button disabled style={{ minWidth: 80 }}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
