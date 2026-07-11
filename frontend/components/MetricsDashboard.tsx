"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { evaluateChat } from "@/lib/api";
import type { ChatTurn, RagasScores } from "@/lib/types";

interface MetricsDashboardProps {
  turn: ChatTurn | null;
}

export function MetricsDashboard({ turn }: MetricsDashboardProps) {
  const [scores, setScores] = useState<RagasScores | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const evaluatedForId = useRef<string | null>(null);

  useEffect(() => {
    if (!turn || turn.streaming || !turn.done || turn.error) return;
    if (evaluatedForId.current === turn.id) return;
    evaluatedForId.current = turn.id;

    setScores(null);
    setError(null);
    setLoading(true);

    evaluateChat(
      turn.query,
      turn.done.response,
      turn.citations.map((c) => c.text)
    )
      .then(setScores)
      .catch((err) => setError(err instanceof Error ? err.message : "Evaluation failed."))
      .finally(() => setLoading(false));
  }, [turn]);

  if (!turn) {
    return (
      <Card className="flex h-full flex-col">
        <CardHeader>
          <CardTitle className="text-sm">Metrics</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Ask a question to see per-query metrics here.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="flex h-full flex-col overflow-hidden">
      <CardHeader>
        <CardTitle className="text-sm">Metrics</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4 overflow-y-auto text-sm">
        <div>
          <p className="mb-1 text-xs font-medium text-muted-foreground">Query</p>
          <p className="line-clamp-3 text-sm">{turn.query}</p>
        </div>

        <Separator />

        <div>
          <p className="mb-2 text-xs font-medium text-muted-foreground">Operational</p>
          {turn.streaming ? (
            <div className="flex flex-col gap-2">
              <Skeleton className="h-4 w-2/3" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          ) : turn.done ? (
            <dl className="grid grid-cols-2 gap-y-1.5 text-xs">
              <dt className="text-muted-foreground">Latency</dt>
              <dd className="text-right font-mono">{turn.done.latency_ms.toFixed(0)} ms</dd>
              <dt className="text-muted-foreground">Prompt tokens</dt>
              <dd className="text-right font-mono">{turn.done.prompt_tokens ?? "—"}</dd>
              <dt className="text-muted-foreground">Completion tokens</dt>
              <dd className="text-right font-mono">{turn.done.completion_tokens ?? "—"}</dd>
              <dt className="text-muted-foreground">Est. cost</dt>
              <dd className="text-right font-mono">
                {turn.done.estimated_cost_usd != null ? `$${turn.done.estimated_cost_usd.toFixed(6)}` : "—"}
              </dd>
            </dl>
          ) : turn.error ? (
            <p className="text-xs text-destructive">{turn.error}</p>
          ) : null}
        </div>

        <Separator />

        <div>
          <p className="mb-2 text-xs font-medium text-muted-foreground">RAGAS (quality)</p>
          {loading && (
            <div className="flex flex-col gap-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
            </div>
          )}
          {error && <p className="text-xs text-destructive">{error}</p>}
          {scores && <ScoreBars scores={scores} />}
          {!loading && !error && !scores && turn.streaming && (
            <p className="text-xs text-muted-foreground">Waiting for response to finish…</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function ScoreBars({ scores }: { scores: RagasScores }) {
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
