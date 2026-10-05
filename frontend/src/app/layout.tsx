import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ApexLead AI | Web Agency Lead Generation System",
  description: "AI-Powered Lead Generation, Website Analysis, Personalized Demos, and Outreach for Web Agencies.",
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
