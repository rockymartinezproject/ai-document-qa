"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, Chunk, DocumentOut } from "@/lib/api";
import { LoadingCard, LoadingSpinner } from "@/components/Loading";
import { showToast } from "@/components/Toast";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);

  const [viewingDoc, setViewingDoc] = useState<DocumentOut | null>(null);
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [chunksLoading, setChunksLoading] = useState(false);

  const fetchDocs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.documents.list();
      setDocuments(res.data || []);
    } catch (err) {
      console.error(err);
      showToast("Failed to load documents", "error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  const handleDelete = async (doc: DocumentOut) => {
    if (!confirm(`Delete "${doc.filename}"? This cannot be undone.`)) return;
    setActionId(doc.id);
    try {
      const res = await api.documents.delete(doc.id);
      showToast(res.data?.message || "Document deleted", "success");
      await fetchDocs();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Delete failed", "error");
    } finally {
      setActionId(null);
    }
  };

  const handleReindex = async (doc: DocumentOut) => {
    setActionId(doc.id);
    try {
      const res = await api.documents.reindex(doc.id);
      showToast(res.data?.message || "Document reindexed", "success");
      await fetchDocs();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Reindex failed", "error");
    } finally {
      setActionId(null);
    }
  };

  const handleSync = async (doc: DocumentOut) => {
    setActionId(doc.id);
    try {
      const res = await api.search.syncDocument(doc.id);
      showToast(res.data?.message || "Synced to vector store", "success");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Sync failed", "error");
    } finally {
      setActionId(null);
    }
  };

  const handleEmbed = async (doc: DocumentOut) => {
    setActionId(doc.id);
    try {
      const res = await api.embeddings.embedDocument(doc.id);
      showToast(res.data?.message || "Embeddings generated", "success");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Embedding failed", "error");
    } finally {
      setActionId(null);
    }
  };

  const openChunks = async (doc: DocumentOut) => {
    setViewingDoc(doc);
    setChunksLoading(true);
    try {
      const res = await api.chunks.list(doc.id);
      setChunks(res.data || []);
    } catch (err) {
      console.error(err);
      showToast("Failed to load chunks", "error");
      setChunks([]);
    } finally {
      setChunksLoading(false);
    }
  };

  const formatSize = (doc: DocumentOut) => {
    if (doc.content_type === "text/html") return "Web URL";
    if (doc.file_size < 1024) return `${doc.file_size} B`;
    return `${(doc.file_size / 1024).toFixed(1)} KB`;
  };

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            Documents
          </h1>
          <p className="mt-2 text-zinc-600 dark:text-zinc-400">
            Manage uploaded files, generate embeddings, and sync to the vector store.
          </p>
        </div>
        <Link
          href="/upload"
          className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
        >
          Upload new document
        </Link>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <LoadingCard />
          <LoadingCard />
          <LoadingCard />
        </div>
      ) : documents.length === 0 ? (
        <div className="rounded-2xl border border-zinc-200 bg-white p-12 text-center dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-zinc-600 dark:text-zinc-400">
            No documents yet. Upload your first PDF or URL to get started.
          </p>
          <Link
            href="/upload"
            className="mt-4 inline-block text-sm font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
          >
            Go to upload
          </Link>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-50 text-zinc-600 dark:bg-zinc-900/50 dark:text-zinc-400">
                <tr>
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Size</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Created</th>
                  <th className="px-4 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {documents.map((doc) => (
                  <tr
                    key={doc.id}
                    className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
                  >
                    <td className="px-4 py-3">
                      <p className="font-medium text-zinc-900 dark:text-zinc-100">
                        {doc.filename}
                      </p>
                    </td>
                    <td className="px-4 py-3 text-zinc-600 dark:text-zinc-400">
                      {doc.content_type}
                    </td>
                    <td className="px-4 py-3 text-zinc-600 dark:text-zinc-400">
                      {formatSize(doc)}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={doc.status} />
                    </td>
                    <td className="px-4 py-3 text-zinc-600 dark:text-zinc-400">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => openChunks(doc)}
                          disabled={actionId === doc.id}
                          className="rounded-md border border-zinc-300 px-2 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
                        >
                          Chunks
                        </button>
                        <button
                          onClick={() => handleEmbed(doc)}
                          disabled={actionId === doc.id}
                          className="rounded-md border border-zinc-300 px-2 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
                        >
                          Embed
                        </button>
                        <button
                          onClick={() => handleSync(doc)}
                          disabled={actionId === doc.id}
                          className="rounded-md border border-zinc-300 px-2 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
                        >
                          Sync
                        </button>
                        <button
                          onClick={() => handleReindex(doc)}
                          disabled={actionId === doc.id}
                          className="rounded-md border border-zinc-300 px-2 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
                        >
                          Reindex
                        </button>
                        <button
                          onClick={() => handleDelete(doc)}
                          disabled={actionId === doc.id}
                          className="rounded-md border border-red-200 px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-900/50 dark:text-red-400 dark:hover:bg-red-900/20"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {viewingDoc && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) setViewingDoc(null);
          }}
        >
          <div className="max-h-[80vh] w-full max-w-3xl overflow-hidden rounded-2xl bg-white shadow-xl dark:bg-zinc-900">
            <div className="flex items-center justify-between border-b border-zinc-200 px-6 py-4 dark:border-zinc-800">
              <div>
                <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  Chunks: {viewingDoc.filename}
                </h2>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  {chunksLoading
                    ? "Loading chunks..."
                    : `${chunks.length} chunk${chunks.length === 1 ? "" : "s"} found`}
                </p>
              </div>
              <button
                onClick={() => setViewingDoc(null)}
                className="rounded-md p-1 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
              >
                <CloseIcon className="h-5 w-5" />
              </button>
            </div>
            <div className="overflow-y-auto p-6" style={{ maxHeight: "60vh" }}>
              {chunksLoading ? (
                <div className="flex justify-center py-12">
                  <LoadingSpinner />
                </div>
              ) : chunks.length === 0 ? (
                <p className="text-center text-sm text-zinc-500 dark:text-zinc-400">
                  No chunks found for this document.
                </p>
              ) : (
                <div className="space-y-4">
                  {chunks.map((chunk, i) => (
                    <div
                      key={chunk.id}
                      className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800"
                    >
                      <div className="mb-2 flex items-center justify-between">
                        <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                          #{i + 1}
                        </span>
                        <span className="text-xs text-zinc-500 dark:text-zinc-400">
                          {chunk.start_char}–{chunk.end_char}
                        </span>
                      </div>
                      <p className="whitespace-pre-wrap text-sm text-zinc-800 dark:text-zinc-200">
                        {chunk.text}
                      </p>
                      {chunk.metadata_json && Object.keys(chunk.metadata_json).length > 0 && (
                        <pre className="mt-3 max-h-32 overflow-auto rounded-md bg-zinc-50 p-2 text-xs text-zinc-600 dark:bg-zinc-950 dark:text-zinc-400">
                          {JSON.stringify(chunk.metadata_json, null, 2)}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
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
      className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${color}`}
    >
      {status}
    </span>
  );
}

function CloseIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
    </svg>
  );
}
