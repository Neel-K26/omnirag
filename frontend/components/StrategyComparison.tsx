"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function StrategyComparison() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Strategy Comparison</CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">
        Coming soon: run one query across Dense / Sparse / Hybrid / Hybrid+Rerank and compare
        latency, faithfulness, context precision, and answer relevancy side by side.
      </CardContent>
    </Card>
  );
}
