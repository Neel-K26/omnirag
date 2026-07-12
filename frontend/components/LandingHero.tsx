import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GithubIcon } from "@/components/GithubIcon";

export function LandingHero() {
  return (
    <section className="relative isolate overflow-hidden px-6 pt-28 pb-24 text-center sm:pt-36 sm:pb-32">
      {/* Ambient glow behind the title */}
      <div
        aria-hidden="true"
        className="animate-glow-pulse pointer-events-none absolute top-1/2 left-1/2 -z-10 h-[36rem] w-[36rem] -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-500/20 blur-[120px]"
      />

      <p className="mb-5 text-xs font-medium tracking-[0.2em] text-cyan-400 uppercase">OmniRAG</p>

      <h1 className="mx-auto max-w-4xl text-4xl font-bold tracking-tight text-balance sm:text-6xl">
        Production Multi-Strategy{" "}
        <span className="bg-gradient-to-r from-cyan-400 to-teal-300 bg-clip-text text-transparent">
          RAG Platform
        </span>
      </h1>

      <p className="mx-auto mt-6 max-w-2xl text-base text-muted-foreground sm:text-lg">
        Validated on Clinical Literature · Extensible to Legal, Enterprise &amp; Financial Domains
      </p>

      <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
        <Button
          size="lg"
          className="bg-cyan-500 text-black hover:bg-cyan-400"
          render={
            <Link href="/app">
              Try Live Demo
              <ArrowRight className="size-4" />
            </Link>
          }
        />
        <Button
          size="lg"
          variant="outline"
          render={
            <a href="https://github.com/Neel-K26/omnirag" target="_blank" rel="noopener noreferrer">
              <GithubIcon className="size-4" />
              View on GitHub
            </a>
          }
        />
      </div>
    </section>
  );
}
