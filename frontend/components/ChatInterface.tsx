"use client";

import { useEffect, useRef, useState } from "react";
import type { Dispatch, FormEvent, SetStateAction } from "react";
import { Loader2, Send } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { streamChat } from "@/lib/api";
import type { ChatStreamEvent, ChatTurn } from "@/lib/types";

interface ChatInterfaceProps {
  turns: ChatTurn[];
  setTurns: Dispatch<SetStateAction<ChatTurn[]>>;
}

function newTurn(query: string): ChatTurn {
  return {
    id: crypto.randomUUID(),
    query,
    answer: "",
    routing: null,
    hops: [],
    citations: [],
    done: null,
    streaming: true,
    error: null,
  };
}

export function ChatInterface({ turns, setTurns }: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const isStreaming = turns.length > 0 && turns[turns.length - 1].streaming;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  function updateTurn(id: string, updater: (turn: ChatTurn) => ChatTurn) {
    setTurns((prev) => prev.map((t) => (t.id === id ? updater(t) : t)));
  }

  function applyEvent(id: string, event: ChatStreamEvent) {
    switch (event.type) {
      case "routing":
        updateTurn(id, (t) => ({ ...t, routing: event.data }));
        break;
      case "hop":
        updateTurn(id, (t) => ({ ...t, hops: [...t.hops, event.data] }));
        break;
      case "citations":
        updateTurn(id, (t) => ({ ...t, citations: event.data }));
        break;
      case "token":
        updateTurn(id, (t) => ({ ...t, answer: t.answer + event.data }));
        break;
      case "done":
        updateTurn(id, (t) => ({ ...t, done: event.data, streaming: false }));
        break;
      case "error":
        updateTurn(id, (t) => ({ ...t, streaming: false, error: event.data }));
        break;
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const query = input.trim();
    if (!query || isStreaming) return;
    setInput("");

    const turn = newTurn(query);
    setTurns((prev) => [...prev, turn]);

    try {
      for await (const event of streamChat(query)) {
        applyEvent(turn.id, event);
      }
    } catch (err) {
      updateTurn(turn.id, (t) => ({
        ...t,
        streaming: false,
        error: err instanceof Error ? err.message : "Something went wrong.",
      }));
    }
  }

  return (
    <Card className="flex h-full flex-col overflow-hidden py-0 gap-0">
      <ScrollArea className="flex-1 px-4 py-4">
        <div className="flex flex-col gap-6">
          {turns.length === 0 && (
            <p className="py-8 text-center text-sm text-muted-foreground">
              Ask a question about the ingested clinical literature to get started.
            </p>
          )}
          {turns.map((turn) => (
            <ChatTurnView key={turn.id} turn={turn} />
          ))}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>
      <Separator />
      <form onSubmit={handleSubmit} className="flex items-end gap-2 p-3">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          placeholder="Ask a question..."
          disabled={isStreaming}
          className="min-h-[44px] resize-none"
          rows={1}
        />
        <Button type="submit" disabled={isStreaming || !input.trim()} size="icon">
          {isStreaming ? <Loader2 className="animate-spin" /> : <Send />}
        </Button>
      </form>
    </Card>
  );
}

function ChatTurnView({ turn }: { turn: ChatTurn }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="ml-auto max-w-[85%] rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground">
        {turn.query}
      </div>

      <div className="flex flex-col gap-2">
        {turn.routing && (
          <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
            <Badge variant="secondary" className="text-xs">
              {turn.routing.intent}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {turn.routing.strategy}
            </Badge>
            <span>via {turn.routing.method === "rule" ? "keyword rule" : "LLM fallback"}</span>
          </div>
        )}

        {turn.hops.length > 0 && <HopTrace hops={turn.hops} />}

        <div className="max-w-[95%] rounded-lg bg-muted px-3 py-2 text-sm whitespace-pre-wrap">
          {turn.answer || (turn.streaming ? "…" : "")}
          {turn.error && <p className="mt-1 text-destructive">{turn.error}</p>}
        </div>

        {turn.citations.length > 0 && <SourceCards citations={turn.citations} />}
      </div>
    </div>
  );
}

function HopTrace({ hops }: { hops: ChatTurn["hops"] }) {
  return (
    <details className="rounded-md border px-2 py-1.5 text-xs text-muted-foreground">
      <summary className="cursor-pointer select-none font-medium">
        Retrieval reasoning ({hops.length} hop{hops.length > 1 ? "s" : ""})
      </summary>
      <div className="mt-2 flex flex-col gap-2">
        {hops.map((hop) => (
          <div key={hop.hop_number} className="border-l-2 pl-2">
            <p className="font-medium text-foreground">
              Hop {hop.hop_number}: {hop.strategy}
            </p>
            <p className="italic">&ldquo;{hop.query}&rdquo;</p>
            <p>
              {hop.sufficiency.sufficient ? "Sufficient" : "Insufficient"} — {hop.sufficiency.reasoning}
            </p>
          </div>
        ))}
      </div>
    </details>
  );
}

function SourceCards({ citations }: { citations: ChatTurn["citations"] }) {
  return (
    <div className="flex flex-col gap-1.5">
      <p className="text-xs font-medium text-muted-foreground">Sources</p>
      <div className="flex flex-col gap-1.5">
        {citations.map((c) => (
          <div key={c.index} className="rounded-md border px-2 py-1.5 text-xs">
            <div className="flex items-center gap-1.5 font-medium">
              <Badge variant="outline" className="px-1 text-[10px]">
                {c.index}
              </Badge>
              <span>{c.document_title}</span>
              {c.page != null && <span className="text-muted-foreground">p.{c.page}</span>}
            </div>
            <p className="mt-1 line-clamp-2 text-muted-foreground">{c.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
