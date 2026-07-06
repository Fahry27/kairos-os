import NavItem, { type NavItemDef } from "./NavItem";

const NAV_ITEMS: NavItemDef[] = [
  { label: "Home", href: "/home" },
  { label: "Kai", href: "/kai" },
  { label: "Work", href: "/work" },
  { label: "Settings", href: "/settings" },
];

export default function Sidebar() {
  return (
    <nav aria-label="Kairos" style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div
        style={{
          fontSize: 22,
          fontWeight: 720,
          color: "var(--accent)",
          padding: "0 12px 20px",
          letterSpacing: "-0.5px",
        }}
      >
        Kairos
      </div>

      <ul
        style={{
          listStyle: "none",
          margin: 0,
          padding: 0,
          display: "flex",
          flexDirection: "column",
          gap: 4,
        }}
      >
        {NAV_ITEMS.map((item) => (
          <NavItem key={item.href} {...item} />
        ))}
      </ul>

      <div
        style={{
          marginTop: "auto",
          paddingTop: 16,
          borderTop: "1px solid var(--panel-border)",
          fontSize: 11,
          color: "var(--muted)",
          padding: "16px 12px 0",
        }}
      >
        v3.4
      </div>
    </nav>
  );
}
