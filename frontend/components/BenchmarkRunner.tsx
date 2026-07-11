"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function BenchmarkRunner() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Benchmark Runner</CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">
        Coming soon: run 10 preset clinical queries, view aggregate RAGAS scores, and export
        results as JSON.
      </CardContent>
    </Card>
  );
}
