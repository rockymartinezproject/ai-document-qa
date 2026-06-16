"use client";

import { useEffect, useRef, useState } from "react";
import { api, ChatMessage, Citation, Conversation } from "@/lib/api";
import { LoadingSpinner } from "@/components/Loading";

type Message =
  | { role: "user"; content: string }
  | {
      role: "assistant";
      content: string;
      citations: Citation[];
      provider: string;
    };

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | undefined>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadConversations = async () => {
    try {
      const res = await api.conversations.list();
      setConversations(res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingConversations(false);
    }
  };

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startNewChat = async () => {
    try {
      const res = await api.conversations.create();
      const conversation = res.data!;
      setConversations((prev) => [conversation, ...prev]);
      setActiveConversationId(conversation.id);
      setMessages([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create conversation");
    }
  };

  const selectConversation = async (id: string) => {
    setActiveConversationId(id);
    setMessages([]);
    setError(null);

    try {
      const res = await api.conversations.get(id);
      const data = res.data!;
      const loaded: Message[] = data.messages.map((m: ChatMessage) =>
        m.role === "user"
          ? { role: "user", content: m.content }
          : {
              role: "assistant",
              content: m.content,
              citations: m.citations || [],
              provider: m.provider || "unknown",
            }
      );
      setMessages(loaded);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load conversation");
    }
  };

  const deleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.conversations.delete(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConversationId === id) {
        setActiveConversationId(undefined);
        setMessages([]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const question = input.trim();
    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setIsLoading(true);

    try {
      const res = await api.chat.ask(question, activeConversationId);
      const data = res.data!;

      if (!activeConversationId) {
        setActiveConversationId(data.conversation_id);
        await loadConversations();
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          citations: data.citations,
          provider: data.provider,
        },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to get answer");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-65px)]">
      {/* Sidebar */}
      <aside className="hidden w-64 flex-col border-r border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50 md:flex">
        <div className="border-b border-zinc-200 dark:border-zinc-800 p-4">
          <button
            onClick={startNewChat}
            className="w-full rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
          >
            New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-3">
          {isLoadingConversations ? (
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
                    onClick={() => selectConversation(conv.id)}
                    className={`group flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm ${
                      activeConversationId === conv.id
                        ? "bg-zinc-200 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100"
                        : "text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-800"
                    }`}
                  >
                    <span className="truncate pr-2">
                      {conv.title || "New Chat"}
                    </span>
                    <span
                      onClick={(e) => deleteConversation(conv.id, e)}
                      className="opacity-0 group-hover:opacity-100 text-zinc-400 hover:text-red-500"
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

      {/* Main chat */}
      <div className="flex flex-1 flex-col">
        {/* Chat header */}
        <div className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-4">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            Chat
          </h2>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Ask questions about your indexed documents.
          </p>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-6 py-8">
          <div className="mx-auto max-w-3xl space-y-6">
            {messages.length === 0 && (
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
              <div key={i} className="flex gap-3">
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                    msg.role === "user"
                      ? "bg-zinc-200 dark:bg-zinc-700"
                      : "bg-indigo-100 dark:bg-indigo-900/30"
                  }`}
                >
                  <span
                    className={`text-sm font-bold ${
                      msg.role === "user"
                        ? "text-zinc-700 dark:text-zinc-300"
                        : "text-indigo-600 dark:text-indigo-400"
                    }`}
                  >
                    {msg.role === "user" ? "You" : "AI"}
                  </span>
                </div>
                <div className="flex-1 space-y-3">
                  <div
                    className={`rounded-2xl px-4 py-3 text-sm ${
                      msg.role === "user"
                        ? "bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100"
                        : "bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100"
                    }`}
                  >
                    {msg.content}
                  </div>

                  {msg.role === "assistant" && msg.citations.length > 0 && (
                    <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50 px-3 py-2">
                      <p className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">
                        Sources
                      </p>
                      <ul className="mt-2 space-y-2">
                        {msg.citations.map((c, idx) => (
                          <li
                            key={c.chunk_id}
                            className="text-xs text-zinc-600 dark:text-zinc-400"
                          >
                            <span className="font-medium text-zinc-900 dark:text-zinc-200">
                              [{idx + 1}] {c.source}
                            </span>
                            <span className="ml-2 text-zinc-400 dark:text-zinc-600">
                              score: {c.score.toFixed(3)}
                            </span>
                            <p className="mt-0.5 line-clamp-2">{c.text}</p>
                          </li>
                        ))}
                      </ul>
                      <p className="mt-2 text-[10px] text-zinc-400 dark:text-zinc-600">
                        Answered via {msg.provider}
                      </p>
                    </div>
                  )}
                </div>
              </div>
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

        {/* Input area */}
        <div className="border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-4">
          <form
            onSubmit={handleSubmit}
            className="mx-auto flex max-w-3xl items-center gap-3"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              disabled={isLoading}
              className="flex-1 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-4 py-2.5 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
