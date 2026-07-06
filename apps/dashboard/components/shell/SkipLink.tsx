"use client";

/**
 * Accessibility: skip-to-content link. Visually hidden until focused.
 * Must be the first focusable element on every Shell page.
 */
export default function SkipLink() {
  return (
    <a
      href="#kairos-main"
      style={{
        position: "absolute",
        top: "-1000px",
        left: "8px",
        zIndex: 9999,
        padding: "8px 16px",
        background: "var(--accent)",
        color: "#ffffff",
        borderRadius: "6px",
        fontWeight: 700,
        fontSize: 14,
        textDecoration: "none",
      }}
      onFocus={(e) => {
        e.currentTarget.style.top = "8px";
      }}
      onBlur={(e) => {
        e.currentTarget.style.top = "-1000px";
      }}
    >
      Skip to main content
    </a>
  );
}
