"use client";

import { useConversation } from "../../lib/runtime";

const SUGGESTION_CHIPS = [
  "What's on my schedule today?",
  "Review my open tasks.",
  "Summarize this week's progress.",
  "Plan my next mission.",
  "What should I focus on right now?",
];

export default function KaiPage() {
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
    <div style={{ maxWidth: 760, margin: "0 auto", display: "flex", flexDirection: "column", minHeight: "calc(100vh - 64px)" }}>
      {/* Message area */}
      <div
        style={{
          flex: 1,
          background: "var(--panel)",
          border: "1px solid var(--panel-border)",
          borderRadius: 8,
          padding: 24,
          minHeight: 360,
          overflow: "auto",
          marginBottom: 16,
        }}
      >
        {activeConversation && activeConversation.messages.length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {activeConversation.messages.map((msg) => (
              <div
                key={msg.id}
                style={{
                  alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                  maxWidth: "75%",
                  background: msg.role === "user" ? "var(--accent-soft)" : "var(--bg)",
                  border: "1px solid var(--panel-border)",
                  borderRadius: 8,
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
                  {msg.status === "error" || msg.status === "failed" ? (
                    <span style={{ fontSize: 11, color: "#a33131" }}>failed</span>
                  ) : null}
                </div>
                <p style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{msg.content}</p>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: "center", maxWidth: 480, margin: "0 auto", paddingTop: 80 }}>
            <h2 style={{ fontSize: 24, fontWeight: 720, margin: "0 0 8px" }}>
              Ask Kai
            </h2>
            <p style={{ color: "var(--muted)", lineHeight: 1.6, margin: "0 0 28px", fontSize: 15 }}>
              Your conversation with Kairos will appear here. Ask questions, plan
              work, or reflect on what you&apos;ve accomplished.
            </p>

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

      {/* Conversation list */}
      {conversations.length > 1 && (
        <div style={{ marginBottom: 12, display: "flex", gap: 8, overflowX: "auto", paddingBottom: 4 }}>
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
      <div
        style={{
          display: "flex",
          gap: 8,
          background: "var(--panel)",
          border: "1px solid var(--panel-border)",
          borderRadius: 8,
          padding: "8px 12px",
          marginBottom: 16,
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
        <button className="btnOutline btnSmall" onClick={newConversation} style={{ minWidth: 90 }}>
          New Chat
        </button>
      </div>
    </div>
  );
}
