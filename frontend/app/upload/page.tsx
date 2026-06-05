"use client";

import { LoadingCard } from "@/components/Loading";

export default function UploadPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          Upload Documents
        </h2>
        <p className="mt-2 text-zinc-600 dark:text-zinc-400">
          Add PDFs or paste URLs to index them for question answering.
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2">
        {/* PDF Upload */}
        <div className="rounded-2xl border-2 border-dashed border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-8 text-center hover:border-indigo-400 dark:hover:border-indigo-600 transition-colors">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 dark:bg-indigo-900/20">
            <DocumentIcon className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
          </div>
          <h3 className="mt-4 text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Upload PDF
          </h3>
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            Drag & drop or click to browse
          </p>
          <p className="mt-4 text-xs text-zinc-400 dark:text-zinc-600">
            Coming in Day 4-5
          </p>
        </div>

        {/* URL Input */}
        <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-8">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 dark:bg-indigo-900/20">
            <LinkIcon className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
          </div>
          <h3 className="mt-4 text-center text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Add URL
          </h3>
          <p className="mt-1 text-center text-xs text-zinc-500 dark:text-zinc-400">
            Paste a web page link
          </p>
          <div className="mt-4">
            <input
              type="url"
              disabled
              placeholder="https://example.com/article"
              className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-2 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
            />
          </div>
        </div>
      </div>

      {/* Indexed documents placeholder */}
      <div className="mt-12">
        <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          Indexed Documents
        </h3>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <LoadingCard />
          <LoadingCard />
        </div>
      </div>
    </div>
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
