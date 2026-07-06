/**
 * LoadingShell — Suspense fallback for route segments.
 * Displays a minimal spinner while Next.js loads a route.
 */
export default function LoadingShell() {
  return (
    <div
      role="status"
      aria-label="Loading"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "60vh",
        color: "var(--muted)",
        fontSize: 14,
      }}
    >
      <span
        style={{
          display: "inline-block",
          width: 20,
          height: 20,
          border: "2px solid var(--panel-border)",
          borderTopColor: "var(--accent)",
          borderRadius: "50%",
          animation: "kairos-loading-spin 0.6s linear infinite",
          marginRight: 10,
        }}
      />
      Loading…
      <style jsx>{`
        @keyframes kairos-loading-spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
}
