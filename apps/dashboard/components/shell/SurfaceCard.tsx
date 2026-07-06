import React from "react";

interface SurfaceCardProps {
  title?: string;
  /** Optional eyebrow text above the title. */
  eyebrow?: string;
  /** Optional badge shown to the right. */
  badge?: string;
  children: React.ReactNode;
}

/**
 * SurfaceCard — reusable card container with panel background and shadow.
 * Used across Shell surfaces for structured content blocks.
 */
export default function SurfaceCard({ title, eyebrow, badge, children }: SurfaceCardProps) {
  return (
    <section className="card" style={{ minWidth: 0 }}>
      {(eyebrow || title || badge) && (
        <div className="sectionHeader" style={{ marginBottom: title ? 16 : 8 }}>
          <div>
            {eyebrow && (
              <p className="eyebrow" style={{ margin: "0 0 4px", fontSize: 11 }}>
                {eyebrow}
              </p>
            )}
            {title && <h2 style={{ margin: 0 }}>{title}</h2>}
          </div>
          {badge && <span className="pill">{badge}</span>}
        </div>
      )}
      {children}
    </section>
  );
}
