"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export type NavItemDef = {
  label: string;
  href: string;
};

/**
 * NavItem — sidebar navigation link with active-state highlighting.
 */
export default function NavItem({ label, href }: NavItemDef) {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <li>
      <Link
        href={href}
        aria-current={isActive ? "page" : undefined}
        style={{
          display: "flex",
          alignItems: "center",
          padding: "8px 12px",
          borderRadius: "6px",
          fontSize: 14,
          fontWeight: isActive ? 700 : 500,
          color: isActive ? "var(--accent)" : "var(--text)",
          background: isActive ? "var(--accent-soft)" : "transparent",
          textDecoration: "none",
          outlineOffset: "2px",
          transition: "background 0.15s ease, color 0.15s ease",
        }}
      >
        {label}
      </Link>
    </li>
  );
}
