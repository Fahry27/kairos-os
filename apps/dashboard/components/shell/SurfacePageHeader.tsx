import React from "react";

interface SurfacePageHeaderProps {
  title: string;
  description: string;
  /** Optional action area rendered to the right of the header. */
  children?: React.ReactNode;
}

/**
 * SurfacePageHeader — consistent page header for every Shell surface.
 */
export default function SurfacePageHeader({ title, description, children }: SurfacePageHeaderProps) {
  return (
    <header
      className="topBar"
      style={{ borderBottom: "none", paddingBottom: "0", marginBottom: "28px" }}
    >
      <div>
        <p className="eyebrow">Kairos</p>
        <h1 style={{ fontSize: 32, fontWeight: 720, margin: "0 0 8px" }}>{title}</h1>
        <p className="subtitle" style={{ margin: 0 }}>{description}</p>
      </div>
      {children && <div className="topBarActions">{children}</div>}
    </header>
  );
}
