"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChatInterface } from "@/components/ChatInterface";
import { MetricsDashboard } from "@/components/MetricsDashboard";
import { DocumentUploader } from "@/components/DocumentUploader";
import { StrategyComparison } from "@/components/StrategyComparison";
import { BenchmarkRunner } from "@/components/BenchmarkRunner";
import type { ChatTurn } from "@/lib/types";

export default function Home() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const activeTurn = turns.length > 0 ? turns[turns.length - 1] : null;

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b px-6 py-3">
        <div className="flex items-baseline gap-2">
          <h1 className="text-lg font-semibold tracking-tight">OmniRAG</h1>
          <span className="text-xs text-muted-foreground">Multi-Strategy RAG Platform</span>
        </div>
      </header>

      <Tabs defaultValue="chat" className="flex flex-1 flex-col overflow-hidden gap-0">
        <div className="border-b px-6">
          <TabsList className="bg-transparent p-0 h-auto">
            <TabsTrigger value="chat" className="data-[state=active]:shadow-none">
              Chat
            </TabsTrigger>
            <TabsTrigger value="compare" className="data-[state=active]:shadow-none">
              Strategy Comparison
            </TabsTrigger>
            <TabsTrigger value="benchmark" className="data-[state=active]:shadow-none">
              Benchmark
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="chat" className="flex-1 overflow-hidden p-4 mt-0">
          <div className="grid h-full grid-cols-[280px_1fr_320px] gap-4">
            <DocumentUploader />
            <ChatInterface turns={turns} setTurns={setTurns} />
            <MetricsDashboard turn={activeTurn} />
          </div>
        </TabsContent>

        <TabsContent value="compare" className="flex-1 overflow-auto p-4 mt-0">
          <StrategyComparison />
        </TabsContent>

        <TabsContent value="benchmark" className="flex-1 overflow-auto p-4 mt-0">
          <BenchmarkRunner />
        </TabsContent>
      </Tabs>
    </div>
  );
}
