"use client";

import { useEffect, useState } from "react";
import { Download, Loader2, Play } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { getBenchmarkQueries, runBenchmark } from "@/lib/api";
import type { BenchmarkRunResponse, RagasScores } from "@/lib/types";

export function BenchmarkRunner() {
  const [queries, setQueries] = useState<string[]>([]);
  const [loadingQueries, setLoadingQueries] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BenchmarkRunResponse | null>(null);

  useEffect(() => {
    getBenchmarkQueries()
      .then(setQueries)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load preset queries."))
      .finally(() => setLoadingQueries(false));
  }, []);

  async function handleRun() {
    setRunning(true);
    setError(null);
    try {
      const res = await runBenchmark();
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Benchmark run failed.");
    } finally {
      setRunning(false);
    }
  }

  function handleExport() {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `omnirag-benchmark-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Benchmark Runner</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div>
            <p className="mb-2 text-xs font-medium text-muted-foreground">
              {loadingQueries ? "Loading preset queries…" : `${queries.length} preset clinical queries`}
            </p>
            <ol className="flex flex-col gap-1 text-xs text-muted-foreground">
              {queries.map((q, i) => (
                <li key={q}>
                  {i + 1}. {q}
                </li>
              ))}
            </ol>
          </div>

          <div className="flex items-center gap-2">
            <Button onClick={handleRun} disabled={running || loadingQueries}>
              {running ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
              {running ? "Running benchmark…" : "Run Benchmark"}
            </Button>
            <Button variant="outline" onClick={handleExport} disabled={!result}>
              <Download className="size-4" />
              Export JSON
            </Button>
          </div>
          {running && (
            <p className="text-xs text-muted-foreground">
              Running {queries.length} queries through retrieval, generation, and RAGAS evaluation — this can take a
              minute or two.
            </p>
          )}
        </CardContent>
      </Card>

      {error && (
        <Card>
          <CardContent className="text-sm text-destructive">{error}</CardContent>
        </Card>
      )}

      {result && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Aggregate results</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <p className="text-xs text-muted-foreground">
                Avg. latency: <span className="font-mono">{result.aggregate_latency_ms.toFixed(0)} ms</span> across{" "}
                {result.results.length} queries
              </p>
              <AggregateScoreBars scores={result.aggregate} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Per-query results</CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b text-muted-foreground">
                    <th className="py-2 pr-4 font-medium">Query</th>
                    <th className="py-2 pr-4 font-medium">Intent</th>
                    <th className="py-2 pr-4 font-medium">Hops</th>
                    <th className="py-2 pr-4 font-medium">Latency</th>
                    <th className="py-2 pr-4 font-medium">Faithfulness</th>
                    <th className="py-2 pr-4 font-medium">Relevancy</th>
                    <th className="py-2 pr-4 font-medium">Precision</th>
                  </tr>
                </thead>
                <tbody>
                  {result.results.map((r) => (
                    <tr key={r.query} className="border-b last:border-0 align-top">
                      <td className="max-w-xs py-2 pr-4">{r.query}</td>
                      <td className="py-2 pr-4">
                        <Badge variant="outline" className="text-[10px]">
                          {r.routing.intent}
                        </Badge>
                      </td>
                      <td className="py-2 pr-4 font-mono">{r.num_hops}</td>
                      <td className="py-2 pr-4 font-mono">{r.latency_ms.toFixed(0)} ms</td>
                      <td className="py-2 pr-4 font-mono">{r.ragas.faithfulness.toFixed(2)}</td>
                      <td className="py-2 pr-4 font-mono">{r.ragas.answer_relevancy.toFixed(2)}</td>
                      <td className="py-2 pr-4 font-mono">{r.ragas.context_precision.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function AggregateScoreBars({ scores }: { scores: RagasScores }) {
  const rows: { label: string; value: number }[] = [
    { label: "Faithfulness", value: scores.faithfulness },
    { label: "Answer relevancy", value: scores.answer_relevancy },
    { label: "Context precision", value: scores.context_precision },
  ];
  return (
    <div className="flex flex-col gap-2.5">
      {rows.map((row) => (
        <div key={row.label}>
          <div className="mb-1 flex items-center justify-between text-xs">
            <span className="text-muted-foreground">{row.label}</span>
            <span className="font-mono">{row.value.toFixed(2)}</span>
          </div>
          <Progress value={Math.max(0, Math.min(1, row.value)) * 100} />
        </div>
      ))}
    </div>
  );
}
