import type {
  BenchmarkRunResponse,
  Chunk,
  ChatStreamEvent,
  CompareResponse,
  DocumentItem,
  RagasScores,
} from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://omnirag-87oc.onrender.com";

// Render's free tier spins the backend down after inactivity; the first request after that
// hits a cold start and the proxy returns 502 before the app is even up to attach CORS
// headers, which the browser then reports as a CORS error rather than a 502. One automatic
// retry after a short wait covers the common case where the instance finishes booting
// (backend/warmup.py) in that window. `init` is safe to reuse across both attempts — neither
// a JSON string body nor FormData is consumed by being passed to fetch.
async function fetchWithRetry(input: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(input, init);
  if (res.status === 502) {
    await new Promise((resolve) => setTimeout(resolve, 3000));
    return fetch(input, init);
  }
  return res;
}

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
  const res = await fetchWithRetry(`${API_URL}/documents`);
  return handleJsonResponse<DocumentItem[]>(res);
}

export async function uploadText(text: string, title: string): Promise<IngestResponse> {
  const res = await fetchWithRetry(`${API_URL}/documents/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, title }),
  });
  return handleJsonResponse<IngestResponse>(res);
}

export async function uploadUrl(url: string): Promise<IngestResponse> {
  const res = await fetchWithRetry(`${API_URL}/documents/url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  return handleJsonResponse<IngestResponse>(res);
}

export async function uploadPdf(file: File): Promise<IngestResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetchWithRetry(`${API_URL}/documents/pdf`, {
    method: "POST",
    body: formData,
  });
  return handleJsonResponse<IngestResponse>(res);
}

export async function* streamChat(query: string, signal?: AbortSignal): AsyncGenerator<ChatStreamEvent> {
  const res = await fetchWithRetry(`${API_URL}/chat/stream`, {
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
  const res = await fetchWithRetry(`${API_URL}/chat/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, response, contexts }),
  });
  return handleJsonResponse<RagasScores>(res);
}

export async function compareStrategies(query: string): Promise<CompareResponse> {
  const res = await fetchWithRetry(`${API_URL}/retrieval/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  return handleJsonResponse<CompareResponse>(res);
}

export async function getBenchmarkQueries(): Promise<string[]> {
  const res = await fetchWithRetry(`${API_URL}/benchmark/queries`);
  return handleJsonResponse<string[]>(res);
}

export async function runBenchmark(): Promise<BenchmarkRunResponse> {
  const res = await fetchWithRetry(`${API_URL}/benchmark/run`, { method: "POST" });
  return handleJsonResponse<BenchmarkRunResponse>(res);
}
