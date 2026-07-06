"use client";

import SurfacePageHeader from "../../components/shell/SurfacePageHeader";
import SurfaceCard from "../../components/shell/SurfaceCard";
import FoundationNotice from "../../components/shell/FoundationNotice";
import { useKairosState } from "../../lib/state";
import { useConversation, useKnowledgeForMission, useAIRouter, useAIProviderHealth } from "../../lib/runtime";

const SUGGESTION_CHIPS = [
  "What's on my schedule today?",
  "Review my open decisions.",
  "Summarize this week's progress.",
  "Plan my next mission.",
  "What should I focus on right now?",
];

/**
 * Ask Kai — production chat architecture with full conversation runtime.
 *
 * Runtime features:
 *   - useConversation() hook: message list, draft, send, abort
 *   - Active context bar (mission + workspace)
 *   - Suggestion chips (no mock responses)
 *   - Sticky prompt input
 *
 * Ready for real API wiring without structural changes.
 */
export default function AskKaiPage() {
  const state = useKairosState();
  const activeMission = state.missions.find((m) => m.id === state.assistant.activeMissionId);
  const activeWorkspace = state.workspaces.find((w) => w.id === state.assistant.activeWorkspaceId);

  const {
    conversations,
    activeConversation,
    newConversation,
    selectConversation,
    draft,
    setDraft,
    sendMessage,
    isSending,
    sendError,
    abortSending,
  } = useConversation();

  const missionKnowledge = useKnowledgeForMission(state.assistant.activeMissionId);
  const router = useAIRouter();
  const health = useAIProviderHealth();

  const handleSend = () => {
    sendMessage(draft);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", display: "flex", flexDirection: "column", minHeight: "calc(100vh - 64px)" }}>
      <SurfacePageHeader
        title="Ask Kai"
        description="Your conversational interface to the AI Operating System."
      />

      {/* Context bar */}
      {(activeMission || activeWorkspace || health.total > 0) && (
        <SurfaceCard eyebrow="Active Context" badge={health.total > 0 ? `${health.healthy}/${health.total} healthy` : undefined}>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            {activeMission && (
              <div>
                <span style={{ fontSize: 12, color: "var(--muted)", fontWeight: 700, textTransform: "uppercase" }}>
                  Mission
                </span>
                <p style={{ margin: "4px 0 0", fontWeight: 600 }}>{activeMission.name}</p>
              </div>
            )}
            {health.total > 0 && (
              <div>
                <span style={{ fontSize: 12, color: "var(--muted)", fontWeight: 700, textTransform: "uppercase" }}>
                  Providers
                </span>
                <p style={{ margin: "4px 0 0", fontWeight: 600 }}>
                  {health.healthy} healthy · {router.routePolicy.budgetTier} tier
                  {router.routePolicy.offlineOnly && " · offline"}
                </p>
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
          padding: "24px",
          minHeight: 320,
          overflow: "auto",
        }}
      >
        {activeConversation && activeConversation.messages.length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {activeConversation.messages.map((msg) => (
              <div
                key={msg.id}
                style={{
                  alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                  maxWidth: "70%",
                  background: msg.role === "user" ? "var(--accent-soft)" : "var(--bg)",
                  border: "1px solid var(--panel-border)",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  fontSize: 14,
                  lineHeight: 1.5,
                  color: "var(--text)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: "var(--muted)", textTransform: "uppercase" }}>
                    {msg.role === "user" ? "You" : "Kairos"}
                  </span>
                  {msg.status === "pending" && (
                    <span style={{ fontSize: 11, color: "var(--amber)" }}>sending…</span>
                  )}
                  {msg.status === "error" && (
                    <span style={{ fontSize: 11, color: "#a33131" }}>failed</span>
                  )}
                </div>
                <p style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{msg.content}</p>
              </div>
            ))}
          </div>
        ) : (
          /* Empty state */
          <div style={{ textAlign: "center", maxWidth: 480, margin: "0 auto", paddingTop: 60 }}>
            <h2 style={{ fontSize: 22, fontWeight: 720, margin: "0 0 8px" }}>
              Ask Kai anything
            </h2>
            <p className="stateText" style={{ lineHeight: 1.6, marginBottom: 28 }}>
              Your conversation with Kairos will appear here.
              Start a new conversation to ask questions, plan work,
              or reflect on what you&apos;ve accomplished.
            </p>

            {/* Suggestion chips */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", maxWidth: 520 }}>
              {SUGGESTION_CHIPS.map((chip) => (
                <button
                  key={chip}
                  onClick={() => sendMessage(chip)}
                  className="btnOutline btnSmall"
                  style={{
                    borderColor: "var(--panel-border)",
                    fontSize: 13,
                    fontWeight: 500,
                  }}
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>
        )}

        {sendError && (
          <p className="errorText" style={{ textAlign: "center", marginTop: 16 }}>
            {sendError}
          </p>
        )}
      </div>

      {/* Conversation list strip (if multiple conversations exist) */}
      {conversations.length > 1 && (
        <div style={{ marginTop: 12, display: "flex", gap: 8, overflowX: "auto", paddingBottom: 4 }}>
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => selectConversation(conv.id)}
              className="btnOutline btnSmall"
              style={{
                borderColor: conv.id === (activeConversation?.id ?? null) ? "var(--accent)" : "var(--panel-border)",
                fontWeight: conv.id === (activeConversation?.id ?? null) ? 700 : 500,
                whiteSpace: "nowrap",
              }}
            >
              {conv.title}
            </button>
          ))}
        </div>
      )}

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
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSending}
            style={{
              flex: 1,
              border: "none",
              background: "transparent",
              outline: "none",
              fontSize: 15,
            }}
            aria-label="Ask Kai prompt"
          />
          <button
            onClick={handleSend}
            disabled={!draft.trim() || isSending}
            style={{ minWidth: 80 }}
          >
            {isSending ? "Sending…" : "Send"}
          </button>
          {isSending && (
            <button className="btnOutline btnSmall" onClick={abortSending}>
              Stop
            </button>
          )}
          {!activeConversation && (
            <button className="btnOutline btnSmall" onClick={newConversation} style={{ minWidth: 90 }}>
              New Chat
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
