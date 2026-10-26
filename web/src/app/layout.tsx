import type { Metadata } from "next";
import { Archivo, DM_Mono, Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "latin-ext"], variable: "--font-inter", display: "swap" });
const archivo = Archivo({ subsets: ["latin", "latin-ext"], variable: "--font-archivo", display: "swap", axes: ["wdth"] });
const mono = DM_Mono({ subsets: ["latin", "latin-ext"], weight: ["400", "500"], variable: "--font-dm-mono", display: "swap" });

export const metadata: Metadata = {
  title: "Becuz",
  description: "Why profit moved this week, with a receipt for every claim.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} ${archivo.variable} ${mono.variable}`}>
      <body className="min-h-dvh antialiased">{children}</body>
    </html>
  );
}
