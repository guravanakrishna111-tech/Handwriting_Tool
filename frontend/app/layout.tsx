import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Handwriting Studio",
  description: "Reference-driven AI handwriting synthesis workspace"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
