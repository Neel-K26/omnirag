"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { FileText, Link as LinkIcon, Loader2, Type, Upload } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { listDocuments, uploadPdf, uploadText, uploadUrl } from "@/lib/api";
import type { Chunk, DocumentItem } from "@/lib/types";

export function DocumentUploader() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [busy, setBusy] = useState(false);
  const [previewChunks, setPreviewChunks] = useState<Chunk[] | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const [textValue, setTextValue] = useState("");
  const [titleValue, setTitleValue] = useState("");
  const [urlValue, setUrlValue] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const refreshDocuments = useCallback(async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load documents.");
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    // Initial fetch on mount; refreshDocuments is also reused after each upload.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refreshDocuments();
  }, [refreshDocuments]);

  async function handlePdfFile(file: File) {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      toast.error("Only PDF files are supported.");
      return;
    }
    setBusy(true);
    try {
      const { document, chunks } = await uploadPdf(file);
      toast.success(`Ingested "${document.title}" — ${document.num_chunks} chunks`);
      setPreviewChunks(chunks);
      await refreshDocuments();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "PDF ingestion failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleTextSubmit() {
    if (!textValue.trim()) return;
    setBusy(true);
    try {
      const { document, chunks } = await uploadText(textValue, titleValue.trim() || "Untitled");
      toast.success(`Ingested "${document.title}" — ${document.num_chunks} chunks`);
      setPreviewChunks(chunks);
      setTextValue("");
      setTitleValue("");
      await refreshDocuments();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Text ingestion failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleUrlSubmit() {
    if (!urlValue.trim()) return;
    setBusy(true);
    try {
      const { document, chunks } = await uploadUrl(urlValue.trim());
      toast.success(`Ingested "${document.title}" — ${document.num_chunks} chunks`);
      setPreviewChunks(chunks);
      setUrlValue("");
      await refreshDocuments();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "URL ingestion failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="flex h-full flex-col gap-0 overflow-hidden py-0">
      <CardHeader className="py-3">
        <CardTitle className="text-sm">Documents</CardTitle>
      </CardHeader>
      <Separator />
      <ScrollArea className="flex-1">
        <CardContent className="flex flex-col gap-4 py-4">
          <Tabs defaultValue="pdf">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="pdf" title="PDF">
                <FileText className="size-3.5" />
              </TabsTrigger>
              <TabsTrigger value="url" title="URL">
                <LinkIcon className="size-3.5" />
              </TabsTrigger>
              <TabsTrigger value="text" title="Text">
                <Type className="size-3.5" />
              </TabsTrigger>
            </TabsList>

            <TabsContent value="pdf" className="mt-3">
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragOver(true);
                }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setIsDragOver(false);
                  const file = e.dataTransfer.files?.[0];
                  if (file) handlePdfFile(file);
                }}
                onClick={() => fileInputRef.current?.click()}
                className={`flex cursor-pointer flex-col items-center gap-2 rounded-md border border-dashed px-3 py-6 text-center text-xs transition-colors ${
                  isDragOver ? "border-primary bg-accent" : "border-border"
                }`}
              >
                <Upload className="size-4 text-muted-foreground" />
                <p className="text-muted-foreground">Drag &amp; drop a PDF, or click to browse</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handlePdfFile(file);
                    e.target.value = "";
                  }}
                />
              </div>
            </TabsContent>

            <TabsContent value="url" className="mt-3 flex flex-col gap-2">
              <Label htmlFor="url-input" className="text-xs">
                Page URL
              </Label>
              <Input
                id="url-input"
                placeholder="https://example.com/article"
                value={urlValue}
                onChange={(e) => setUrlValue(e.target.value)}
              />
              <Button size="sm" onClick={handleUrlSubmit} disabled={busy || !urlValue.trim()}>
                {busy ? <Loader2 className="size-3.5 animate-spin" /> : "Ingest URL"}
              </Button>
            </TabsContent>

            <TabsContent value="text" className="mt-3 flex flex-col gap-2">
              <Label htmlFor="title-input" className="text-xs">
                Title
              </Label>
              <Input
                id="title-input"
                placeholder="Untitled"
                value={titleValue}
                onChange={(e) => setTitleValue(e.target.value)}
              />
              <Label htmlFor="text-input" className="text-xs">
                Text
              </Label>
              <Textarea
                id="text-input"
                placeholder="Paste plain text..."
                value={textValue}
                onChange={(e) => setTextValue(e.target.value)}
                rows={5}
              />
              <Button size="sm" onClick={handleTextSubmit} disabled={busy || !textValue.trim()}>
                {busy ? <Loader2 className="size-3.5 animate-spin" /> : "Ingest Text"}
              </Button>
            </TabsContent>
          </Tabs>

          {previewChunks && previewChunks.length > 0 && (
            <div>
              <Separator className="mb-3" />
              <p className="mb-2 text-xs font-medium text-muted-foreground">
                Chunk preview ({previewChunks.length})
              </p>
              <div className="flex flex-col gap-1.5">
                {previewChunks.slice(0, 3).map((chunk) => (
                  <div key={chunk.id} className="rounded-md border px-2 py-1.5 text-xs">
                    <p className="line-clamp-2 text-muted-foreground">{chunk.text}</p>
                  </div>
                ))}
                {previewChunks.length > 3 && (
                  <p className="text-xs text-muted-foreground">+{previewChunks.length - 3} more</p>
                )}
              </div>
            </div>
          )}

          <Separator />

          <div>
            <p className="mb-2 text-xs font-medium text-muted-foreground">
              Ingested documents ({documents.length})
            </p>
            {loadingDocs ? (
              <p className="text-xs text-muted-foreground">Loading…</p>
            ) : documents.length === 0 ? (
              <p className="text-xs text-muted-foreground">No documents yet.</p>
            ) : (
              <div className="flex flex-col gap-1.5">
                {documents.map((doc) => (
                  <div key={doc.id} className="rounded-md border px-2 py-1.5 text-xs">
                    <p className="line-clamp-1 font-medium">{doc.title}</p>
                    <div className="mt-1 flex items-center gap-1.5">
                      <Badge variant="outline" className="px-1 text-[10px]">
                        {doc.source_type}
                      </Badge>
                      <span className="text-muted-foreground">{doc.num_chunks} chunks</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </ScrollArea>
    </Card>
  );
}
