export type DocumentSourceType = "pdf" | "url" | "text";

export interface ChunkMetadata {
  document_id: string;
  document_title: string;
  source_type: DocumentSourceType;
  page: number | null;
  chunk_index: number;
}

export interface Chunk {
  id: string;
  text: string;
  metadata: ChunkMetadata;
}

export interface DocumentItem {
  id: string;
  title: string;
  source_type: DocumentSourceType;
  source: string;
  num_chunks: number;
}

export type RetrievalStrategy = "dense" | "sparse" | "hybrid" | "hybrid_rerank";

export type QueryIntent = "factual" | "analytical" | "comparative";

export interface RoutingDecision {
  intent: QueryIntent;
  strategy: RetrievalStrategy;
  method: "rule" | "prompt_fallback";
}

export interface SufficiencyResult {
  sufficient: boolean;
  reasoning: string;
  reformulated_query: string | null;
}

export interface RetrievalHop {
  hop_number: number;
  query: string;
  strategy: RetrievalStrategy;
  chunks: Chunk[];
  sufficiency: SufficiencyResult;
}

export interface Citation {
  index: number;
  document_title: string;
  page: number | null;
  text: string;
}

export interface RagasScores {
  faithfulness: number;
  answer_relevancy: number;
  context_precision: number;
}

export interface ChatDoneData {
  response: string;
  latency_ms: number;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  estimated_cost_usd: number | null;
}

export type ChatStreamEvent =
  | { type: "routing"; data: RoutingDecision }
  | { type: "hop"; data: RetrievalHop }
  | { type: "citations"; data: Citation[] }
  | { type: "token"; data: string }
  | { type: "done"; data: ChatDoneData }
  | { type: "error"; data: string };

// UI-level state for one chat turn, shared between ChatInterface (owns streaming)
// and MetricsDashboard (reacts once a turn finishes streaming).
export interface ChatTurn {
  id: string;
  query: string;
  answer: string;
  routing: RoutingDecision | null;
  hops: RetrievalHop[];
  citations: Citation[];
  done: ChatDoneData | null;
  streaming: boolean;
  error: string | null;
}

export interface StrategyResult {
  strategy: RetrievalStrategy;
  latency_ms: number;
  answer: string;
  chunks: Chunk[];
  ragas: RagasScores;
}

export interface CompareResponse {
  query: string;
  results: StrategyResult[];
}

export interface BenchmarkQueryResult {
  query: string;
  answer: string;
  routing: RoutingDecision;
  num_hops: number;
  latency_ms: number;
  ragas: RagasScores;
}

export interface BenchmarkRunResponse {
  results: BenchmarkQueryResult[];
  aggregate: RagasScores;
  aggregate_latency_ms: number;
}
