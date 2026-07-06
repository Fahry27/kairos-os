import React from "react";

/**
 * FoundationNotice — an honest, visible badge shown on surfaces
 * that haven't yet been wired to live backend data.
 * Not hidden or subtle. Users should know what's ready and what's coming.
 */
export default function FoundationNotice({ label }: { label: string }) {
  return (
    <div
      style={{
        background: "var(--amber-soft)",
        border: "1px solid rgba(138, 90, 0, 0.28)",
        borderRadius: "6px",
        color: "var(--amber)",
        fontSize: 13,
        fontWeight: 600,
        lineHeight: 1.5,
        padding: "10px 14px",
        marginBottom: 24,
      }}
    >
      🏗️ <strong>{label}</strong> — this surface is foundation-only. Live data and AI integration
      are coming in Sprint 1.
    </div>
  );
}
