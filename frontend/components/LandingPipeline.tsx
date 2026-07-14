import {
  Activity,
  Archive,
  Check,
  CornerDownLeft,
  Database,
  FileText,
  Gauge,
  GitMerge,
  ListFilter,
  MessageSquare,
  RefreshCw,
  Route,
  Search,
  Shield,
  Sparkles,
  Tags,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

function StepCard({
  icon: Icon,
  title,
  caption,
  children,
}: {
  icon: LucideIcon;
  title: string;
  caption: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-full w-60 shrink-0 flex-col gap-3 rounded-xl border border-border bg-card/50 p-4">
      <div className="flex items-start gap-2.5">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-lg border border-cyan-500/30 bg-cyan-500/10">
          <Icon className="size-4 text-cyan-400" />
        </div>
        <div>
          <p className="text-sm leading-tight font-medium">{title}</p>
          <p className="text-[11px] leading-tight text-muted-foreground">{caption}</p>
        </div>
      </div>
      <div className="flex flex-1 flex-col justify-center">{children}</div>
    </div>
  );
}

function Connector({ delay }: { delay: number }) {
  return (
    <div className="relative mx-1 h-px w-8 shrink-0 self-center overflow-hidden bg-border sm:w-10">
      <div
        className="animate-flow-sweep absolute inset-y-0 left-0 w-1/3 bg-gradient-to-r from-transparent via-cyan-400 to-transparent"
        style={{ animationDelay: `${delay}s` }}
      />
    </div>
  );
}

const RETRIEVAL_BARS = {
  dense: [90, 70, 50],
  sparse: [80, 60, 40],
};

const RERANK_ROWS = [
  { rank: 1, score: 0.94 },
  { rank: 2, score: 0.87 },
  { rank: 3, score: 0.81 },
];

const EVAL_METRICS = [
  { label: "Faithfulness", value: 96 },
  { label: "Answer Relevancy", value: 91 },
  { label: "Context Precision", value: 88 },
];

const SUPPORTING_LAYERS: { icon: LucideIcon; title: string; items: [string, string] }[] = [
  { icon: FileText, title: "Document Ingestion", items: ["PDF / URL / TXT", "Chunking + Metadata"] },
  { icon: Database, title: "Indexing Layer", items: ["FAISS Index (Dense)", "BM25 Index (Sparse)"] },
  { icon: Tags, title: "Metadata Store", items: ["Source, Page, Section", "Author, Date"] },
  { icon: Activity, title: "Observability", items: ["Latency, Logs", "Traces, Monitoring"] },
  { icon: Shield, title: "Security & Privacy", items: ["PII Redaction", "Access Control"] },
  { icon: Archive, title: "Evaluation Store", items: ["RAGAS Logs", "Historical Metrics"] },
];

const TECH_STACK = [
  "FastAPI",
  "Next.js 14",
  "FAISS",
  "BM25",
  "Cohere Rerank",
  "Gemini Flash",
  "RAGAS",
  "Docker",
  "Render",
  "Vercel",
];

export function LandingPipeline() {
  return (
    <section className="border-t border-border px-6 py-20 sm:py-28">
      <div className="mx-auto max-w-3xl text-center">
        <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">System Architecture</h2>
        <p className="mt-3 text-sm text-muted-foreground sm:text-base">
          Every query flows through the same auditable pipeline, backed by always-on supporting infrastructure.
        </p>
      </div>

      {/* Main pipeline */}
      <div className="relative mt-14">
        <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-10 bg-gradient-to-r from-background to-transparent sm:w-16" />
        <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-10 bg-gradient-to-l from-background to-transparent sm:w-16" />

        <div className="scrollbar-none flex items-stretch gap-1 overflow-x-auto px-8 py-4 sm:px-16">
          <StepCard icon={Search} title="Query" caption="User question">
            <div className="rounded-md border border-border bg-background/60 px-2.5 py-2 text-[11px] text-muted-foreground italic">
              &ldquo;What medications treat hypertension?&rdquo;
            </div>
          </StepCard>
          <Connector delay={0} />

          <StepCard icon={Route} title="Router" caption="Intent classification">
            <div className="flex flex-col gap-2 text-[11px]">
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Detected intent</span>
                <Badge variant="outline" className="px-1.5 py-0 text-[10px]">
                  Factual
                </Badge>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Chosen strategy</span>
                <Badge variant="outline" className="border-cyan-500/40 px-1.5 py-0 text-[10px] text-cyan-400">
                  Hybrid + Rerank
                </Badge>
              </div>
            </div>
          </StepCard>
          <Connector delay={0.25} />

          <StepCard icon={GitMerge} title="Hybrid Retrieval" caption="FAISS (dense) + BM25 (sparse)">
            <div className="flex flex-col items-center gap-2">
              <div className="flex w-full items-start justify-center gap-4">
                <div className="flex flex-col items-center gap-1">
                  <span className="text-[10px] text-muted-foreground">Dense</span>
                  {RETRIEVAL_BARS.dense.map((w, i) => (
                    <div key={i} className="h-1.5 rounded-full bg-cyan-500/70" style={{ width: `${w * 0.4}px` }} />
                  ))}
                </div>
                <div className="flex flex-col items-center gap-1">
                  <span className="text-[10px] text-muted-foreground">Sparse</span>
                  {RETRIEVAL_BARS.sparse.map((w, i) => (
                    <div key={i} className="h-1.5 rounded-full bg-teal-400/70" style={{ width: `${w * 0.4}px` }} />
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                <GitMerge className="size-3 text-cyan-400" />
                RRF Fusion
              </div>
            </div>
          </StepCard>
          <Connector delay={0.5} />

          <StepCard icon={ListFilter} title="Cohere Reranker" caption="Top-K reranking">
            <div className="flex flex-col gap-1.5">
              {RERANK_ROWS.map(({ rank, score }) => (
                <div key={rank} className="flex items-center gap-1.5 text-[10px]">
                  <span className="w-4 text-muted-foreground">#{rank}</span>
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full bg-cyan-500" style={{ width: `${score * 100}%` }} />
                  </div>
                  <span className="w-8 text-right font-mono text-muted-foreground">{score.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </StepCard>
          <Connector delay={0.75} />

          <StepCard icon={RefreshCw} title="Adaptive Loop" caption="Self-evaluating hops">
            <div className="flex flex-col items-center gap-2">
              <div
                className="flex size-16 shrink-0 items-center justify-center border border-cyan-500/40 bg-cyan-500/5 px-2 text-center text-[9px] leading-tight font-medium"
                style={{ clipPath: "polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)" }}
              >
                Sufficient context?
              </div>
              <div className="flex flex-col items-center gap-1 text-[10px] text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Check className="size-3 text-cyan-400" /> Yes — continue
                </span>
                <span className="flex items-center gap-1">
                  <CornerDownLeft className="size-3" /> No — retry retrieval
                </span>
              </div>
              <span className="text-[10px] text-muted-foreground">Max 2 hops</span>
            </div>
          </StepCard>
          <Connector delay={1} />

          <StepCard icon={Sparkles} title="Gemini Flash" caption="Grounded generation">
            <div className="flex flex-col gap-1.5">
              <div className="h-1.5 w-full rounded-full bg-muted" />
              <div className="h-1.5 w-4/5 rounded-full bg-muted" />
              <div className="flex items-center gap-1">
                <div className="h-1.5 w-2/5 rounded-full bg-muted" />
                <span className="h-3 w-[2px] animate-pulse bg-cyan-400" />
              </div>
            </div>
          </StepCard>
          <Connector delay={1.25} />

          <StepCard icon={Gauge} title="RAGAS Evaluation" caption="Automatic evaluation">
            <div className="flex flex-col gap-2">
              {EVAL_METRICS.map((m) => (
                <div key={m.label}>
                  <div className="mb-0.5 flex items-center justify-between text-[10px]">
                    <span className="text-muted-foreground">{m.label}</span>
                    <span className="font-mono">{m.value}%</span>
                  </div>
                  <Progress value={m.value} />
                </div>
              ))}
            </div>
          </StepCard>
          <Connector delay={1.5} />

          <StepCard icon={MessageSquare} title="Response" caption="Cited answer">
            <div className="flex flex-col gap-2">
              <p className="text-[10px] leading-relaxed text-muted-foreground">
                ACE inhibitors and thiazide diuretics are first-line treatments
                <span className="text-cyan-400"> [1][2]</span>.
              </p>
              <div className="flex gap-1">
                <Badge variant="outline" className="px-1.5 text-[9px]">
                  1
                </Badge>
                <Badge variant="outline" className="px-1.5 text-[9px]">
                  2
                </Badge>
              </div>
            </div>
          </StepCard>
        </div>
      </div>

      {/* Supporting layers */}
      <div className="mx-auto mt-16 max-w-5xl">
        <h3 className="text-center text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">
          Supporting Layers (Always On)
        </h3>
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {SUPPORTING_LAYERS.map((layer) => (
            <div
              key={layer.title}
              className={cn(
                "flex flex-col items-center gap-2 rounded-xl border border-border/80 bg-card/50 px-3 py-4 text-center transition-colors hover:border-cyan-500/40"
              )}
            >
              <div className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-cyan-500/30 bg-cyan-500/10">
                <layer.icon className="size-4 text-cyan-400" />
              </div>
              <p className="text-xs font-medium">{layer.title}</p>
              <div className="text-[10px] leading-tight text-muted-foreground">
                {layer.items.map((item) => (
                  <p key={item}>{item}</p>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tech stack */}
      <div className="mx-auto mt-16 max-w-3xl">
        <p className="mb-6 text-center text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">
          Built with
        </p>
        <div className="flex flex-wrap items-center justify-center gap-2.5">
          {TECH_STACK.map((item) => (
            <Badge
              key={item}
              variant="outline"
              className="rounded-full border-border/80 px-3.5 py-1.5 text-sm font-normal text-foreground/80 transition-colors hover:border-cyan-500/50 hover:text-cyan-400"
            >
              {item}
            </Badge>
          ))}
        </div>
      </div>
    </section>
  );
}
