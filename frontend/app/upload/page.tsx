"use client";

import { useCallback, useEffect, useState } from "react";
import { api, DocumentOut } from "@/lib/api";
import { LoadingCard, LoadingSpinner } from "@/components/Loading";
import { ToastContainer, showToast } from "@/components/Toast";

export default function UploadPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [urlInput, setUrlInput] = useState("");
  const [documents, setDocuments] = useState<DocumentOut[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);

  const fetchDocs = useCallback(async () => {
    try {
      const res = await api.documents.list();
      setDocuments(res.data || []);
    } catch (e) {
      console.error(e);
      showToast("Failed to load documents", "error");
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  const handleFile = async (file: File) => {
    if (file.type !== "application/pdf" && !file.name.endsWith(".pdf")) {
      showToast("Only PDF files are supported.", "error");
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      showToast("File size must be under 50MB.", "error");
      return;
    }

    setIsUploading(true);
    setUploadProgress(`Uploading ${file.name}...`);

    try {
      const res = await api.documents.upload(file);
      showToast(res.message || `Uploaded ${file.name}`, "success");
      await fetchDocs();
    } catch (e) {
      showToast(e instanceof Error ? e.message : "Upload failed", "error");
    } finally {
      setIsUploading(false);
      setUploadProgress(null);
    }
  };

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;

    setIsUploading(true);
    setUploadProgress("Ingesting URL...");

    try {
      const res = await api.documents.uploadUrl(urlInput.trim());
      showToast(res.message || `Ingested ${res.data?.title || urlInput}`, "success");
      setUrlInput("");
      await fetchDocs();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "URL ingestion failed", "error");
    } finally {
      setIsUploading(false);
      setUploadProgress(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this document?")) return;
    setActionId(id);
    try {
      const res = await api.documents.delete(id);
      showToast(res.data?.message || "Document deleted", "success");
      await fetchDocs();
    } catch (e) {
      showToast(e instanceof Error ? e.message : "Delete failed", "error");
    } finally {
      setActionId(null);
    }
  };

  const handleReindex = async (id: string) => {
    setActionId(id);
    try {
      const res = await api.documents.reindex(id);
      showToast(res.data?.message || "Document reindexed", "success");
      await fetchDocs();
    } catch (e) {
      showToast(e instanceof Error ? e.message : "Reindex failed", "error");
    } finally {
      setActionId(null);
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <ToastContainer />

      <div className="mb-8">
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          Upload Documents
        </h2>
        <p className="mt-2 text-zinc-600 dark:text-zinc-400">
          Add PDFs or paste URLs to index them for question answering.
        </p>
      </div>

      {uploadProgress && (
        <div className="mb-6 flex items-center gap-3 rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-800 dark:border-indigo-900/50 dark:bg-indigo-900/20 dark:text-indigo-200">
          <LoadingSpinner size="sm" />
          {uploadProgress}
        </div>
      )}

      <div className="grid gap-6 sm:grid-cols-2">
        {/* PDF Upload */}
        <label
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          className={`relative block cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition-all ${
            isDragging
              ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20 scale-[1.02]"
              : "border-zinc-300 bg-white hover:border-indigo-400 dark:border-zinc-700 dark:bg-zinc-900 dark:hover:border-indigo-600"
          }`}
        >
          <input
            type="file"
            accept=".pdf,application/pdf"
            className="sr-only"
            onChange={onInputChange}
            disabled={isUploading}
          />
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 dark:bg-indigo-900/20">
            {isUploading ? (
              <LoadingSpinner />
            ) : (
              <DocumentIcon className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            )}
          </div>
          <h3 className="mt-4 text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            {isUploading ? "Uploading..." : "Upload PDF"}
          </h3>
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            Drag & drop or click to browse
          </p>
          <p className="mt-4 text-xs text-zinc-400 dark:text-zinc-600">
            Max file size: 50MB
          </p>
        </label>

        {/* URL Input */}
        <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-8">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 dark:bg-indigo-900/20">
            {isUploading ? (
              <LoadingSpinner />
            ) : (
              <LinkIcon className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            )}
          </div>
          <h3 className="mt-4 text-center text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Add URL
          </h3>
          <p className="mt-1 text-center text-xs text-zinc-500 dark:text-zinc-400">
            Paste a web page link
          </p>
          <form onSubmit={handleUrlSubmit} className="mt-4">
            <input
              type="url"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="https://example.com/article"
              disabled={isUploading}
              className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-2 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isUploading || !urlInput.trim()}
              className="mt-3 w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600"
            >
              {isUploading ? "Ingesting..." : "Ingest URL"}
            </button>
          </form>
        </div>
      </div>

      {/* Indexed documents */}
      <div className="mt-12">
        <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          Indexed Documents
        </h3>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {loadingDocs ? (
            <>
              <LoadingCard />
              <LoadingCard />
            </>
          ) : documents.length === 0 ? (
            <p className="col-span-full text-sm text-zinc-500 dark:text-zinc-400">
              No documents uploaded yet.
            </p>
          ) : (
            documents.map((doc) => (
              <div
                key={doc.id}
                className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-100">
                    {doc.filename}
                  </p>
                  <StatusBadge status={doc.status} />
                </div>
                <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
                  {doc.content_type === "text/html"
                    ? "Web URL"
                    : `${(doc.file_size / 1024).toFixed(1)} KB`} ·{" "}
                  {new Date(doc.created_at).toLocaleDateString()}
                </p>
                <div className="mt-4 flex gap-2">
                  <button
                    onClick={() => handleReindex(doc.id)}
                    disabled={actionId === doc.id}
                    className="flex-1 rounded-md border border-zinc-300 dark:border-zinc-700 px-2 py-1 text-xs font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-50"
                  >
                    {actionId === doc.id ? "Working..." : "Reindex"}
                  </button>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    disabled={actionId === doc.id}
                    className="rounded-md border border-red-200 dark:border-red-900/50 px-2 py-1 text-xs font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "indexed"
      ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
      : status === "pending"
      ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
      : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";

  return (
    <span
      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${color}`}
    >
      {status}
    </span>
  );
}

function DocumentIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
      />
    </svg>
  );
}

function LinkIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244"
      />
    </svg>
  );
}
