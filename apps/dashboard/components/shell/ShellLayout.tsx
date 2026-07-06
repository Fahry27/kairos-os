import React, { Suspense } from "react";
import SkipLink from "./SkipLink";
import Sidebar from "./Sidebar";
import ErrorBoundary from "./ErrorBoundary";
import LoadingShell from "./LoadingShell";

/**
 * ShellLayout — permanent Kairos application frame.
 *
 * Every page in Kairos is rendered inside this layout.
 * Provides:
 *   - Skip-to-content link (a11y)
 *   - Left sidebar with Shell surfaces + legacy routes
 *   - Error boundary around the main content area
 *   - Suspense loading boundary
 */
export default function ShellLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <SkipLink />

      <aside
        style={{
          width: 240,
          flexShrink: 0,
          background: "var(--panel)",
          borderRight: "1px solid var(--panel-border)",
          padding: "16px 8px",
        }}
      >
        <Sidebar />
      </aside>

      <main
        id="kairos-main"
        style={{
          flex: 1,
          minWidth: 0,
          padding: "32px 40px",
          background: "var(--bg)",
          overflow: "auto",
        }}
      >
        <ErrorBoundary>
          <Suspense fallback={<LoadingShell />}>{children}</Suspense>
        </ErrorBoundary>
      </main>
    </div>
  );
}
