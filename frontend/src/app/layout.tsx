import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LegacyLens — Agentic Code Modernization",
  description:
    "AI-powered modernization engine that transforms legacy enterprise code into modern Python microservices.",
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
