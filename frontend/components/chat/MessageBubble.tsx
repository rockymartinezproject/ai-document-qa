"use client";

import { useState } from "react";
import { Message } from "./types";

function formatTime(iso?: string) {
  if (!iso) return null;
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return null;
  }
}

function CopyIcon({ className }: { className?: string }) {
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
        d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 0 1-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 0 1 1.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 0 0-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 0 1-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 0 0-3.375-3.375h-1.5"
      />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
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
        d="m4.5 12.75 6 6 9-13.5"
      />
    </svg>
  );
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (isUser) return;
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore
    }
  };

  return (
    <div className="flex gap-3">
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser
            ? "bg-zinc-200 dark:bg-zinc-700"
            : "bg-indigo-100 dark:bg-indigo-900/30"
        }`}
      >
        <span
          className={`text-sm font-bold ${
            isUser
              ? "text-zinc-700 dark:text-zinc-300"
              : "text-indigo-600 dark:text-indigo-400"
          }`}
        >
          {isUser ? "You" : "AI"}
        </span>
      </div>
      <div className="flex-1 space-y-3 min-w-0">
        <div
          className={`rounded-2xl px-4 py-3 text-sm ${
            isUser
              ? "bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100"
              : "bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100"
          }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>

          {!isUser && (
            <div className="mt-2 flex items-center justify-end gap-2">
              <span className="text-[10px] text-zinc-400 dark:text-zinc-600">
                {formatTime(message.created_at)}
              </span>
              <button
                onClick={handleCopy}
                className="rounded p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-300"
                aria-label="Copy answer"
                title="Copy answer"
              >
                {copied ? (
                  <CheckIcon className="h-3.5 w-3.5 text-green-600" />
                ) : (
                  <CopyIcon className="h-3.5 w-3.5" />
                )}
              </button>
            </div>
          )}
        </div>

        {!isUser && message.citations.length > 0 && (
          <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50 px-3 py-2">
            <p className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">
              Sources
            </p>
            <ul className="mt-2 space-y-2">
              {message.citations.map((c, idx) => (
                <li
                  key={c.chunk_id}
                  className="text-xs text-zinc-600 dark:text-zinc-400"
                >
                  <span className="font-medium text-zinc-900 dark:text-zinc-200">
                    [{idx + 1}] {c.source} · chunk {c.index}
                  </span>
                  <span className="ml-2 text-zinc-400 dark:text-zinc-600">
                    score: {c.score.toFixed(3)}
                  </span>
                  <p className="mt-0.5 line-clamp-2">{c.text}</p>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-[10px] text-zinc-400 dark:text-zinc-600">
              Answered via {message.provider}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
