/**
 * Kairos Shell — component barrel export.
 *
 * The Shell is Kairos's permanent application frame.
 * It wraps every route and provides:
 *
 *   ShellLayout       — root layout with sidebar + error/suspense boundaries
 *   Sidebar           — two-group navigation (Shell surfaces + legacy routes)
 *   NavItem           — single sidebar link with active-state highlighting
 *   SkipLink          — accessibility skip-to-content link (WCAG 2.1 AA)
 *   ErrorBoundary     — class component catching render errors
 *   LoadingShell      — Suspense fallback spinner
 *
 * Usage:
 *   import { ShellLayout } from "@/components/shell";
 *
 * Each surface under app/ renders inside ShellLayout via the root layout.
 */
export { default as ShellLayout } from "./ShellLayout";
export { default as Sidebar } from "./Sidebar";
export { default as NavItem } from "./NavItem";
export { default as SkipLink } from "./SkipLink";
export { default as ErrorBoundary } from "./ErrorBoundary";
export { default as LoadingShell } from "./LoadingShell";

export type { NavItemDef } from "./NavItem";
