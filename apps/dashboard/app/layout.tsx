import type { Metadata } from "next";
import ShellLayout from "../components/shell/ShellLayout";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kairos",
  description: "Kairos — Your AI Operating System.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <ShellLayout>{children}</ShellLayout>
      </body>
    </html>
  );
}
