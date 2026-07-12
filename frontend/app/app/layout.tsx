import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "OmniRAG — Live Demo",
};

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return children;
}
