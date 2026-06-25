"use client";

import { useState } from "react";
import { Conversation } from "@/lib/api";
import { LoadingSpinner } from "@/components/Loading";

interface ChatSidebarProps {
  conversations: Conversation[];
  activeId?: string;
  isLoading: boolean;
  onNewChat: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
  onRename: (id: string, title: string) => void;
}

function PencilIcon({ className }: { className?: string }) {
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
        d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125"
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
      <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
    </svg>
  );
}

function XIcon({ className }: { className?: string }) {
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

export function ChatSidebar({
  conversations,
  activeId,
  isLoading,
  onNewChat,
  onSelect,
  onDelete,
  onRename,
}: ChatSidebarProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const startEdit = (conv: Conversation, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditValue(conv.title || "New Chat");
  };

  const saveEdit = (id: string) => {
    const title = editValue.trim();
    if (title) {
      onRename(id, title);
    }
    setEditingId(null);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditValue("");
  };

  const handleKeyDown = (e: React.KeyboardEvent, id: string) => {
    if (e.key === "Enter") {
      e.preventDefault();
      saveEdit(id);
    } else if (e.key === "Escape") {
      cancelEdit();
    }
  };

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
            {conversations.map((conv) => {
              const isEditing = editingId === conv.id;
              const isActive = activeId === conv.id;

              return (
                <li key={conv.id}>
                  <button
                    onClick={() => onSelect(conv.id)}
                    className={`group flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm ${
                      isActive
                        ? "bg-zinc-200 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100"
                        : "text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-800"
                    }`}
                  >
                    {isEditing ? (
                      <input
                        autoFocus
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        onKeyDown={(e) => handleKeyDown(e, conv.id)}
                        onBlur={() => saveEdit(conv.id)}
                        onClick={(e) => e.stopPropagation()}
                        className="flex-1 rounded border border-zinc-300 dark:border-zinc-600 bg-white dark:bg-zinc-900 px-1.5 py-0.5 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      />
                    ) : (
                      <span className="truncate pr-2">
                        {conv.title || "New Chat"}
                      </span>
                    )}

                    <span className="flex items-center gap-1">
                      {isEditing ? (
                        <>
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              saveEdit(conv.id);
                            }}
                            className="rounded p-0.5 text-zinc-500 hover:bg-zinc-200 dark:hover:bg-zinc-700 hover:text-green-600"
                            aria-label="Save"
                          >
                            <CheckIcon className="h-3.5 w-3.5" />
                          </span>
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              cancelEdit();
                            }}
                            className="rounded p-0.5 text-zinc-500 hover:bg-zinc-200 dark:hover:bg-zinc-700 hover:text-red-600"
                            aria-label="Cancel"
                          >
                            <XIcon className="h-3.5 w-3.5" />
                          </span>
                        </>
                      ) : (
                        <>
                          <span
                            onClick={(e) => startEdit(conv, e)}
                            className="rounded p-0.5 text-zinc-400 opacity-0 group-hover:opacity-100 hover:bg-zinc-200 dark:hover:bg-zinc-700 hover:text-zinc-600 dark:hover:text-zinc-300"
                            aria-label="Rename conversation"
                          >
                            <PencilIcon className="h-3.5 w-3.5" />
                          </span>
                          <span
                            onClick={(e) => onDelete(conv.id, e)}
                            className="rounded p-0.5 text-zinc-400 opacity-0 group-hover:opacity-100 hover:bg-zinc-200 dark:hover:bg-zinc-700 hover:text-red-500"
                            aria-label="Delete conversation"
                          >
                            ×
                          </span>
                        </>
                      )}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </aside>
  );
}
