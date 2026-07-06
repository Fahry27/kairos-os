/**
 * Kairos Shell — component barrel export.
 *
 * The Shell is Kairos's permanent application frame.
 * It wraps every route and provides:
 *
 *   KairosProvider      — React Context + useReducer state provider (client boundary)
 *   ShellLayout         — root layout with sidebar + error/suspense boundaries
 *   Sidebar             — two-group navigation (Shell surfaces + legacy routes)
 *   NavItem             — single sidebar link with active-state highlighting
 *   SkipLink            — accessibility skip-to-content link (WCAG 2.1 AA)
 *   ErrorBoundary       — class component catching render errors
 *   LoadingShell        — Suspense fallback spinner
 *   SurfacePageHeader   — consistent page header for shell surfaces
 *   SurfaceCard         — reusable card container
 *   SurfaceSection      — titled content block
 *   FoundationNotice    — honest badge for foundation-only surfaces
 *
 * Usage:
 *   import { ShellLayout, SurfacePageHeader } from "@/components/shell";
 *
 * Each surface under app/ renders inside ShellLayout via the root layout.
 */
export { default as KairosProvider } from "./KairosProvider";
export { default as ShellLayout } from "./ShellLayout";
export { default as Sidebar } from "./Sidebar";
export { default as NavItem } from "./NavItem";
export { default as SkipLink } from "./SkipLink";
export { default as ErrorBoundary } from "./ErrorBoundary";
export { default as LoadingShell } from "./LoadingShell";
export { default as SurfacePageHeader } from "./SurfacePageHeader";
export { default as SurfaceCard } from "./SurfaceCard";
export { default as SurfaceSection } from "./SurfaceSection";
export { default as FoundationNotice } from "./FoundationNotice";

export type { NavItemDef } from "./NavItem";
