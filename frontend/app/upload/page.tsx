"use client";

import { useCallback, useEffect, useState } from "react";
import { api, DocumentOut } from "@/lib/api";
import { LoadingCard, LoadingSpinner } from "@/components/Loading";

export default function UploadPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [documents, setDocuments] = useState<DocumentOut[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const fetchDocs = useCallback(async () => {
    try {
      const res = await api.documents.list();
      setDocuments(res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  const handleFile = async (file: File) => {
    if (file.type !== "application/pdf" && !file.name.endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      setError("File size must be under 50MB.");
      return;
    }

    setIsUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const res = await api.documents.upload(file);
      setSuccess(res.message || `Uploaded ${file.name}`);
      await fetchDocs();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setIsUploading(false);
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
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          Upload Documents
        </h2>
        <p className="mt-2 text-zinc-600 dark:text-zinc-400">
          Add PDFs to index them for question answering.
        </p>
      </div>

      {/* Alerts */}
      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-200">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-6 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800 dark:border-green-900/50 dark:bg-green-900/20 dark:text-green-200">
          {success}
        </div>
      )}

      {/* PDF Upload */}
      <label
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={`relative block cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition-colors ${
          isDragging
            ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20"
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
                  {(doc.file_size / 1024).toFixed(1)} KB ·{" "}
                  {new Date(doc.created_at).toLocaleDateString()}
                </p>
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
