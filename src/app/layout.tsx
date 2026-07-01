import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Human-Centred AI Driving Coach",
  description: "Post-drive AI coaching demo for connected-vehicle telemetry.",
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
