import type { Metadata } from "next";
import { LandingHero } from "@/components/LandingHero";
import { LandingPipeline } from "@/components/LandingPipeline";
import { LandingFeatures } from "@/components/LandingFeatures";
import { LandingTechStack } from "@/components/LandingTechStack";
import { LandingFooter } from "@/components/LandingFooter";

export const metadata: Metadata = {
  title: "OmniRAG — Production Multi-Strategy RAG Platform",
  description:
    "Hybrid retrieval, adaptive multi-hop RAG, and live RAGAS evaluation — validated on clinical literature, extensible to legal, enterprise, and financial domains.",
};

export default function LandingPage() {
  return (
    <div className="flex flex-1 flex-col">
      <LandingHero />
      <LandingPipeline />
      <LandingFeatures />
      <LandingTechStack />
      <LandingFooter />
    </div>
  );
}
