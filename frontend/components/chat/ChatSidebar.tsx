"use client";

import { Conversation } from "@/lib/api";
import { LoadingSpinner } from "@/components/Loading";

interface ChatSidebarProps {
  conversations: Conversation[];
  activeId?: string;
  isLoading: boolean;
  onNewChat: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
}

export function ChatSidebar({
  conversations,
  activeId,
  isLoading,
  onNewChat,
  onSelect,
  onDelete,
}: ChatSidebarProps) {
  return (
    <aside className="hidden w-64 flex-col border-r border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50 md:flex">
      <div className="border-b border-zinc-200 dark:border-zinc-800 p-4">
        <button
          onClick={onNewChat}
          className="w-full rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
        >
          New Chat
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-3">
        {isLoading ? (
          <div className="flex justify-center py-4">
            <LoadingSpinner size="sm" />
          </div>
        ) : conversations.length === 0 ? (
          <p className="px-2 text-xs text-zinc-500 dark:text-zinc-400">
            No conversations yet.
          </p>
        ) : (
          <ul className="space-y-1">
            {conversations.map((conv) => (
              <li key={conv.id}>
                <button
                  onClick={() => onSelect(conv.id)}
                  className={`group flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm ${
                    activeId === conv.id
                      ? "bg-zinc-200 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100"
                      : "text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-800"
                  }`}
                >
                  <span className="truncate pr-2">
                    {conv.title || "New Chat"}
                  </span>
                  <span
                    onClick={(e) => onDelete(conv.id, e)}
                    className="opacity-0 group-hover:opacity-100 text-zinc-400 hover:text-red-500"
                    aria-label="Delete conversation"
                  >
                    ×
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
