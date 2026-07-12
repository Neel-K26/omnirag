import { Columns3, Gauge, Network, RefreshCw } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface Feature {
  icon: LucideIcon;
  title: string;
  description: string;
}

const FEATURES: Feature[] = [
  {
    icon: Network,
    title: "Hybrid Retrieval",
    description: "Dense + Sparse + RRF Fusion",
  },
  {
    icon: RefreshCw,
    title: "Adaptive Retrieval Loop",
    description: "Self-evaluating, multi-hop retrieval",
  },
  {
    icon: Gauge,
    title: "Live RAGAS Evaluation",
    description: "Faithfulness, Relevancy, Precision per query",
  },
  {
    icon: Columns3,
    title: "Strategy Comparison",
    description: "Side-by-side benchmark across 4 strategies",
  },
];

export function LandingFeatures() {
  return (
    <section className="border-t border-border px-6 py-20 sm:py-28">
      <div className="mx-auto grid max-w-5xl grid-cols-1 gap-4 sm:grid-cols-2">
        {FEATURES.map((feature) => (
          <Card key={feature.title} className="border-border/80 bg-card/50 transition-colors hover:border-cyan-500/40">
            <CardContent className="flex items-start gap-4">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-cyan-500/30 bg-cyan-500/10">
                <feature.icon className="size-5 text-cyan-400" />
              </div>
              <div>
                <h3 className="font-medium">{feature.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{feature.description}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
