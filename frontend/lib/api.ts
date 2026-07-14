import type {
  BenchmarkRunResponse,
  Chunk,
  ChatStreamEvent,
  CompareResponse,
  DocumentItem,
  RagasScores,
} from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://omnirag-87oc.onrender.com";

async function handleJsonResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? res.statusText;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return res.json() as Promise<T>;
}

export interface IngestResponse {
  document: DocumentItem;
  chunks: Chunk[];
}

export async function listDocuments(): Promise<DocumentItem[]> {
  const res = await fetch(`${API_URL}/documents`);
  return handleJsonResponse<DocumentItem[]>(res);
}

export async function uploadText(text: string, title: string): Promise<IngestResponse> {
  const res = await fetch(`${API_URL}/documents/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, title }),
  });
  return handleJsonResponse<IngestResponse>(res);
}

export async function uploadUrl(url: string): Promise<IngestResponse> {
  const res = await fetch(`${API_URL}/documents/url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  return handleJsonResponse<IngestResponse>(res);
}

export async function uploadPdf(file: File): Promise<IngestResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_URL}/documents/pdf`, {
    method: "POST",
    body: formData,
  });
  return handleJsonResponse<IngestResponse>(res);
}

export async function* streamChat(query: string, signal?: AbortSignal): AsyncGenerator<ChatStreamEvent> {
  const res = await fetch(`${API_URL}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
    signal,
  });

  if (!res.ok || !res.body) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Chat stream failed (${res.status})`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let newlineIndex: number;
    while ((newlineIndex = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, newlineIndex).trim();
      buffer = buffer.slice(newlineIndex + 1);
      if (line) yield JSON.parse(line) as ChatStreamEvent;
    }
  }

  const trailing = buffer.trim();
  if (trailing) yield JSON.parse(trailing) as ChatStreamEvent;
}

export async function evaluateChat(query: string, response: string, contexts: string[]): Promise<RagasScores> {
  const res = await fetch(`${API_URL}/chat/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, response, contexts }),
  });
  return handleJsonResponse<RagasScores>(res);
}

export async function compareStrategies(query: string): Promise<CompareResponse> {
  const res = await fetch(`${API_URL}/retrieval/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  return handleJsonResponse<CompareResponse>(res);
}

export async function getBenchmarkQueries(): Promise<string[]> {
  const res = await fetch(`${API_URL}/benchmark/queries`);
  return handleJsonResponse<string[]>(res);
}

export async function runBenchmark(): Promise<BenchmarkRunResponse> {
  const res = await fetch(`${API_URL}/benchmark/run`, { method: "POST" });
  return handleJsonResponse<BenchmarkRunResponse>(res);
}
