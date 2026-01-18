import type { Metadata } from "next";
import "ketcher-react/dist/index.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "Chem Editor",
  description: "Online chemical structure editor with Ketcher",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-Hans">
      <body>{children}</body>
    </html>
  );
}
