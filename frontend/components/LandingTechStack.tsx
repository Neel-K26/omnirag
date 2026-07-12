import { Badge } from "@/components/ui/badge";

const STACK = ["FastAPI", "FAISS", "BM25", "Cohere Rerank", "Groq LLaMA 3.3", "RAGAS", "Next.js", "Docker"];

export function LandingTechStack() {
  return (
    <section className="border-t border-border px-6 py-16 sm:py-20">
      <p className="mb-6 text-center text-xs font-medium tracking-[0.2em] text-muted-foreground uppercase">
        Built with
      </p>
      <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-center gap-2.5">
        {STACK.map((item) => (
          <Badge
            key={item}
            variant="outline"
            className="rounded-full border-border/80 px-3.5 py-1.5 text-sm font-normal text-foreground/80 transition-colors hover:border-cyan-500/50 hover:text-cyan-400"
          >
            {item}
          </Badge>
        ))}
      </div>
    </section>
  );
}
