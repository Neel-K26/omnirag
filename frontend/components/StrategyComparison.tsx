"use client";

import { useState } from "react";
import { Loader2, Play } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { compareStrategies } from "@/lib/api";
import type { RagasScores, StrategyResult } from "@/lib/types";

const STRATEGY_LABELS: Record<StrategyResult["strategy"], string> = {
  dense: "Dense",
  sparse: "Sparse",
  hybrid: "Hybrid",
  hybrid_rerank: "Hybrid + Rerank",
};

// Fixed categorical order — validated (light/dark) against the dataviz palette. Never reorder or cycle.
// Colors come from --viz-series-{1,2,3} in globals.css, which swap with the app's .dark class.
const METRICS: { key: keyof RagasScores; label: string; cssVar: string }[] = [
  { key: "faithfulness", label: "Faithfulness", cssVar: "var(--viz-series-1)" },
  { key: "answer_relevancy", label: "Answer relevancy", cssVar: "var(--viz-series-2)" },
  { key: "context_precision", label: "Context precision", cssVar: "var(--viz-series-3)" },
];

const CHART_HEIGHT = 140;

export function StrategyComparison() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<StrategyResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRun() {
    const q = query.trim();
    if (!q || loading) return;
    setLoading(true);
    setError(null);
    try {
      const res = await compareStrategies(q);
      setResults(res.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed.");
      setResults(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Strategy Comparison</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2">
          <Input
            placeholder="Ask a question to compare across all 4 retrieval strategies..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleRun();
            }}
            disabled={loading}
          />
          <Button onClick={handleRun} disabled={loading || !query.trim()}>
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
            Run
          </Button>
        </CardContent>
      </Card>

      {error && (
        <Card>
          <CardContent className="text-sm text-destructive">{error}</CardContent>
        </Card>
      )}

      {results && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Quality metrics by strategy</CardTitle>
            </CardHeader>
            <CardContent>
              <RagasBarChart results={results} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Results</CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <ResultsTable results={results} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function RagasBarChart({ results }: { results: StrategyResult[] }) {
  const ticks = [0, 0.25, 0.5, 0.75, 1];

  return (
    <div className="flex flex-col gap-4">
      {/* Legend — always present for >= 2 series; text carries the label, swatch carries identity */}
      <div className="flex flex-wrap gap-4">
        {METRICS.map((m) => (
          <div key={m.key} className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="size-2.5 rounded-full" style={{ backgroundColor: m.cssVar }} />
            {m.label}
          </div>
        ))}
      </div>

      <div className="flex gap-6">
        {/* Y-axis ticks */}
        <div className="flex flex-col justify-between text-[10px] text-muted-foreground" style={{ height: CHART_HEIGHT }}>
          {[...ticks].reverse().map((t) => (
            <span key={t}>{t}</span>
          ))}
        </div>

        <div className="flex flex-1 items-end justify-around border-l border-border pl-4">
          {results.map((r) => (
            <div key={r.strategy} className="flex flex-col items-center gap-2">
              <div className="relative flex items-end gap-[2px]" style={{ height: CHART_HEIGHT }}>
                {/* gridlines */}
                <div className="pointer-events-none absolute inset-0 flex flex-col justify-between">
                  {[...ticks].reverse().map((t) => (
                    <div key={t} className="w-full border-t border-border/60" />
                  ))}
                </div>
                {METRICS.map((m) => {
                  const value = r.ragas[m.key];
                  const clamped = Math.max(0, Math.min(1, value));
                  return (
                    <Tooltip key={m.key}>
                      <TooltipTrigger
                        className="relative w-4 rounded-t-[4px] outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        style={{
                          height: `${clamped * CHART_HEIGHT}px`,
                          backgroundColor: m.cssVar,
                        }}
                      />
                      <TooltipContent>
                        <span className="font-semibold">{value.toFixed(2)}</span> — {m.label} ({STRATEGY_LABELS[r.strategy]})
                      </TooltipContent>
                    </Tooltip>
                  );
                })}
              </div>
              <span className="text-center text-[11px] text-muted-foreground">{STRATEGY_LABELS[r.strategy]}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ResultsTable({ results }: { results: StrategyResult[] }) {
  return (
    <table className="w-full text-left text-xs">
      <thead>
        <tr className="border-b text-muted-foreground">
          <th className="py-2 pr-4 font-medium">Strategy</th>
          <th className="py-2 pr-4 font-medium">Latency</th>
          <th className="py-2 pr-4 font-medium">Faithfulness</th>
          <th className="py-2 pr-4 font-medium">Answer relevancy</th>
          <th className="py-2 pr-4 font-medium">Context precision</th>
        </tr>
      </thead>
      <tbody className="font-mono">
        {results.map((r) => (
          <tr key={r.strategy} className="border-b last:border-0">
            <td className="py-2 pr-4 font-sans font-medium">
              <Badge variant="outline">{STRATEGY_LABELS[r.strategy]}</Badge>
            </td>
            <td className="py-2 pr-4">{r.latency_ms.toFixed(0)} ms</td>
            <td className="py-2 pr-4">{r.ragas.faithfulness.toFixed(2)}</td>
            <td className="py-2 pr-4">{r.ragas.answer_relevancy.toFixed(2)}</td>
            <td className="py-2 pr-4">{r.ragas.context_precision.toFixed(2)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
