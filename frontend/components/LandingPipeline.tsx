import { Cpu, Gauge, Layers, ListFilter, MessageSquare, RefreshCw, Route, Search } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface PipelineStep {
  icon: LucideIcon;
  label: string;
  caption: string;
}

const STEPS: PipelineStep[] = [
  { icon: Search, label: "Query", caption: "User question" },
  { icon: Route, label: "Router", caption: "Intent classification" },
  { icon: Layers, label: "Hybrid Retrieval", caption: "FAISS + BM25" },
  { icon: ListFilter, label: "Cohere Reranker", caption: "Top-K reranking" },
  { icon: RefreshCw, label: "Adaptive Loop", caption: "Self-evaluating hops" },
  { icon: Cpu, label: "Groq LLM", caption: "Grounded generation" },
  { icon: Gauge, label: "RAGAS Evaluation", caption: "Faithfulness · Relevancy · Precision" },
  { icon: MessageSquare, label: "Response", caption: "Cited answer" },
];

export function LandingPipeline() {
  return (
    <section className="border-t border-border px-6 py-20 sm:py-28">
      <div className="mx-auto max-w-3xl text-center">
        <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">How a query becomes an answer</h2>
        <p className="mt-3 text-sm text-muted-foreground sm:text-base">
          Every request flows through the same auditable pipeline — routed, retrieved, reranked, evaluated.
        </p>
      </div>

      <div className="relative mt-14">
        <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-10 bg-gradient-to-r from-background to-transparent sm:w-16" />
        <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-10 bg-gradient-to-l from-background to-transparent sm:w-16" />

        <div className="scrollbar-none flex items-center gap-1 overflow-x-auto px-8 py-4 sm:justify-center sm:px-16">
          {STEPS.map((step, i) => (
            <div key={step.label} className="flex shrink-0 items-center">
              <div className="flex w-32 flex-col items-center gap-2.5 text-center sm:w-36">
                <div className="flex size-12 shrink-0 items-center justify-center rounded-xl border border-cyan-500/30 bg-cyan-500/10">
                  <step.icon className="size-5 text-cyan-400" />
                </div>
                <div>
                  <p className="text-sm font-medium">{step.label}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{step.caption}</p>
                </div>
              </div>

              {i < STEPS.length - 1 && (
                <div className="relative mx-1 h-px w-8 shrink-0 self-start overflow-hidden bg-border mt-6 sm:w-10">
                  <div
                    className="animate-flow-sweep absolute inset-y-0 left-0 w-1/3 bg-gradient-to-r from-transparent via-cyan-400 to-transparent"
                    style={{ animationDelay: `${i * 0.25}s` }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
