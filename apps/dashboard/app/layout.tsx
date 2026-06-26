import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kairos Dashboard",
  description: "Read-only dashboard for Kairos Core API.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
