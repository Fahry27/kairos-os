import React from "react";

interface SurfaceSectionProps {
  title: string;
  children: React.ReactNode;
}

/**
 * SurfaceSection — a titled content block with muted label.
 */
export default function SurfaceSection({ title, children }: SurfaceSectionProps) {
  return (
    <section style={{ marginBottom: 20 }}>
      <h3
        style={{
          fontSize: 13,
          fontWeight: 700,
          color: "var(--muted)",
          textTransform: "uppercase",
          margin: "0 0 10px",
          letterSpacing: "0.02em",
        }}
      >
        {title}
      </h3>
      {children}
    </section>
  );
}
