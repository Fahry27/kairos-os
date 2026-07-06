"use client";

import React, { type ReactNode } from "react";
import { KairosStateProvider } from "../../lib/state";

/**
 * KairosProvider — client boundary that wraps children with shared application state.
 * Placed in RootLayout between the server-rendered shell and route content.
 */
export default function KairosProvider({ children }: { children: ReactNode }) {
  return <KairosStateProvider>{children}</KairosStateProvider>;
}
