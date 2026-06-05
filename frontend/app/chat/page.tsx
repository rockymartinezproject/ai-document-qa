"use client";

import { LoadingSpinner } from "@/components/Loading";

export default function ChatPage() {
  return (
    <div className="flex h-[calc(100vh-129px)] flex-col">
      {/* Chat header */}
      <div className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-4">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Chat
        </h2>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Ask questions about your documents. Coming in Day 10-12.
        </p>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="mx-auto max-w-3xl space-y-6">
          {/* AI welcome */}
          <div className="flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-900/30">
              <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400">
                AI
              </span>
            </div>
            <div className="rounded-2xl bg-zinc-100 dark:bg-zinc-800 px-4 py-3 text-sm text-zinc-700 dark:text-zinc-300">
              Hello! Upload some documents and I will answer your questions with
              source citations.
            </div>
          </div>
        </div>
      </div>

      {/* Input area */}
      <div className="border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-4">
        <div className="mx-auto flex max-w-3xl items-center gap-3">
          <input
            type="text"
            disabled
            placeholder="Type a message..."
            className="flex-1 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-4 py-2.5 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
          />
          <button
            disabled
            className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
