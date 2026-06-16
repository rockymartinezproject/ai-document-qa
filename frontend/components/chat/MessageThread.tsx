"use client";

import { RefObject } from "react";
import { Message } from "./types";
import { MessageBubble } from "./MessageBubble";
import { LoadingSpinner } from "@/components/Loading";

interface MessageThreadProps {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  bottomRef: RefObject<HTMLDivElement | null>;
}

export function MessageThread({
  messages,
  isLoading,
  error,
  bottomRef,
}: MessageThreadProps) {
  return (
    <div className="flex-1 overflow-y-auto px-6 py-8">
      <div className="mx-auto max-w-3xl space-y-6">
        {messages.length === 0 && !isLoading && (
          <div className="flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-900/30">
              <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400">
                AI
              </span>
            </div>
            <div className="rounded-2xl bg-zinc-100 dark:bg-zinc-800 px-4 py-3 text-sm text-zinc-700 dark:text-zinc-300">
              Hello! Upload some documents and ask me anything about them. I
              will cite the sources I used.
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {isLoading && (
          <div className="flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-900/30">
              <LoadingSpinner size="sm" />
            </div>
            <div className="rounded-2xl bg-zinc-100 dark:bg-zinc-800 px-4 py-3 text-sm text-zinc-500 dark:text-zinc-400">
              Thinking...
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-200">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
