import SurfacePageHeader from "../../components/shell/SurfacePageHeader";
import SurfaceCard from "../../components/shell/SurfaceCard";
import FoundationNotice from "../../components/shell/FoundationNotice";

/**
 * Ask Kai — your conversational interface to the AI Operating System.
 *
 * Architecture:
 *   - Message thread area (top)
 *   - Context / session info bar
 *   - Prompt input area (bottom, sticky)
 *
 * Foundation state: static layout showing the chat structure.
 * AI backend and message state are not yet wired.
 */
export default function AskKaiPage() {
  return (
    <div style={{ maxWidth: 900, margin: "0 auto", display: "flex", flexDirection: "column", minHeight: "calc(100vh - 64px)" }}>
      <FoundationNotice label="Ask Kai" />

      <SurfacePageHeader
        title="Ask Kai"
        description="Your conversational interface to the AI Operating System."
      />

      {/* Context bar */}
      <SurfaceCard eyebrow="Session" badge="Foundation">
        <p className="stateText">
          Ask Kai lets you talk to your AI Operating System in natural language.
          Ask questions, give instructions, plan work, or reflect on your week.
          The conversation will be saved and searchable in your Timeline.
        </p>
      </SurfaceCard>

      {/* Message area — flex-grow to push prompt to bottom */}
      <div
        style={{
          flex: 1,
          marginTop: 24,
          background: "var(--panel)",
          border: "1px solid var(--panel-border)",
          borderRadius: "8px",
          padding: "24px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          minHeight: 300,
        }}
      >
        <p className="stateText" style={{ textAlign: "center", maxWidth: 400 }}>
          Your conversation with Kairos will appear here.
          <br />
          Ask anything — plan a project, review decisions,
          <br />
          or reflect on what you&apos;ve accomplished.
        </p>
      </div>

      {/* Prompt input — sticky at bottom */}
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
