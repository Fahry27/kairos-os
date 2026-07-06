"use client";

import React from "react";

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * ErrorBoundary — catches render errors and shows a recovery UI.
 * Placed around the main content area in ShellLayout.
 */
export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          role="alert"
          style={{
            padding: 32,
            textAlign: "center",
            color: "var(--muted)",
          }}
        >
          <p style={{ fontWeight: 700, color: "#a33131", marginBottom: 8 }}>Something went wrong.</p>
          <p style={{ fontSize: 13, margin: 0 }}>
            {this.state.error?.message ?? "An unexpected error occurred."}
          </p>
        </div>
      );
    }

    return this.props.children;
  }
}
