import NavItem, { type NavItemDef } from "./NavItem";

const SHELL_SURFACES: NavItemDef[] = [
  { label: "Good Morning", href: "/good-morning" },
  { label: "Continue Working", href: "/continue-working" },
  { label: "Ask Kai", href: "/ask-kai" },
  { label: "Today's Brief", href: "/todays-brief" },
  { label: "Workspace", href: "/workspace" },
];

const LEGACY_ROUTES: NavItemDef[] = [
  { label: "Decisions", href: "/decisions" },
  { label: "Missions", href: "/missions" },
  { label: "Settings", href: "/settings" },
  { label: "Home", href: "/" },
];

/**
 * Sidebar — permanent Kairos Shell navigation.
 *
 * Group 1 (top):   Shell surfaces — the primary Kairos interface.
 * Group 2 (bottom): Legacy dashboard routes, preserved during Shell rollout.
 */
export default function Sidebar() {
  return (
    <nav aria-label="Kairos Shell" style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ marginBottom: 16 }}>
        <span
          style={{
            display: "block",
            fontSize: 12,
            fontWeight: 700,
            color: "var(--muted)",
            textTransform: "uppercase",
            padding: "0 12px",
            marginBottom: 6,
          }}
        >
          Kairos
        </span>
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 2 }}>
          {SHELL_SURFACES.map((item) => (
            <NavItem key={item.href} {...item} />
          ))}
        </ul>
      </div>

      <div
        style={{
          marginTop: "auto",
          borderTop: "1px solid var(--panel-border)",
          paddingTop: 12,
        }}
      >
        <span
          style={{
            display: "block",
            fontSize: 11,
            fontWeight: 700,
            color: "var(--muted)",
            textTransform: "uppercase",
            padding: "0 12px",
            marginBottom: 4,
          }}
        >
          Legacy
        </span>
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 2 }}>
          {LEGACY_ROUTES.map((item) => (
            <NavItem key={item.href} {...item} />
          ))}
        </ul>
      </div>
    </nav>
  );
}
