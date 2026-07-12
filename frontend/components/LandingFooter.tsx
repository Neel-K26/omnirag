import { GithubIcon } from "@/components/GithubIcon";

export function LandingFooter() {
  return (
    <footer className="border-t border-border px-6 py-8">
      <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-4 text-sm text-muted-foreground sm:flex-row">
        <p>
          Built by <span className="text-foreground/80">Neel Khairnar</span>
        </p>
        <a
          href="https://github.com/Neel-K26/omnirag"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 transition-colors hover:text-cyan-400"
        >
          <GithubIcon className="size-4" />
          github.com/Neel-K26/omnirag
        </a>
      </div>
    </footer>
  );
}
