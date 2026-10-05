import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "GrowthGrid | 100% Pure Instagram Lead Engine",
  description: "Real-time Instagram lead generation and autonomous GrowthGrid outreach system. 100% genuine live data.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} min-h-screen text-slate-100 antialiased`}>
        {children}
      </body>
    </html>
  );
}
