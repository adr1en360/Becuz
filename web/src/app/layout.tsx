import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Becuz",
  description: "Why profit moved this week, with a receipt for every claim.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
