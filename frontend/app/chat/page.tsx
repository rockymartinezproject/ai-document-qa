"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api, askStream, ChatMessage, Conversation, LLMProviderInfo } from "@/lib/api";
import {
  ChatInput,
  ChatSidebar,
  MessageThread,
  Message,
} from "@/components/chat";

export default function ChatPage() {
  const searchParams = useSearchParams();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<
    string | undefined
  >();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [providers, setProviders] = useState<LLMProviderInfo[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const restoredFromUrl = useRef(false);

  const loadConversations = useCallback(async () => {
    try {
      const res = await api.conversations.list();
      setConversations(res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingConversations(false);
    }
  }, []);

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
          ? { role: "user", content: m.content, created_at: m.created_at }
          : {
              role: "assistant",
              content: m.content,
              citations: m.citations || [],
              provider: m.provider || "unknown",
              created_at: m.created_at,
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

  const renameConversation = async (id: string, title: string) => {
    try {
      await api.conversations.update(id, title);
      setConversations((prev) =>
        prev.map((c) => (c.id === id ? { ...c, title } : c))
      );
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error ? err.message : "Failed to rename conversation"
      );
    }
  };

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    let cancelled = false;

    async function loadProviders() {
      try {
        const res = await api.providers.list();
        const list = res.data || [];
        if (cancelled) return;
        setProviders(list);
        const firstAvailable = list.find((p) => p.available);
        if (firstAvailable) {
          setSelectedProvider(firstAvailable.name);
          setSelectedModel(firstAvailable.default_model);
        }
      } catch (e) {
        if (!cancelled) {
          console.error(e);
        }
      }
    }

    loadProviders();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Restore active conversation from URL query param on mount
  useEffect(() => {
    if (restoredFromUrl.current) return;
    const idFromUrl = searchParams.get("conversationId");
    if (idFromUrl) {
      restoredFromUrl.current = true;
      selectConversation(idFromUrl);
    }
  }, [searchParams]);

  // Sync active conversation to URL for persistent sessions
  useEffect(() => {
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    if (activeConversationId) {
      url.searchParams.set("conversationId", activeConversationId);
    } else {
      url.searchParams.delete("conversationId");
    }
    window.history.replaceState({}, "", url.toString());
  }, [activeConversationId]);

  const handleStop = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setIsStreaming(false);
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isStreaming) return;

    const question = input.trim();
    const now = new Date().toISOString();
    setInput("");
    setError(null);

    const conversationIdBefore = activeConversationId;
    setMessages((prev) => [
      ...prev,
      { role: "user", content: question, created_at: now },
      {
        role: "assistant",
        content: "",
        citations: [],
        provider: "unknown",
        created_at: now,
      },
    ]);
    setIsStreaming(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const stream = askStream(
        question,
        activeConversationId,
        undefined,
        "hybrid",
        true,
        selectedProvider || undefined,
        selectedModel || undefined,
        controller.signal
      );

      for await (const event of stream) {
        if (event.type === "citations") {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last && last.role === "assistant") {
              next[next.length - 1] = {
                ...last,
                citations: event.citations,
              };
            }
            return next;
          });
        } else if (event.type === "token") {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last && last.role === "assistant") {
              next[next.length - 1] = {
                ...last,
                content: last.content + event.token,
              };
            }
            return next;
          });
        } else if (event.type === "done") {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last && last.role === "assistant") {
              next[next.length - 1] = {
                ...last,
                content: event.answer,
                citations: event.citations,
                provider: event.provider,
                created_at: new Date().toISOString(),
              };
            }
            return next;
          });
        } else if (event.type === "error") {
          setError(event.message);
        }
      }

      if (!conversationIdBefore) {
        const listRes = await api.conversations.list();
        const list = listRes.data || [];
        setConversations(list);
        if (list[0]) {
          setActiveConversationId(list[0].id);
        }
      }
    } catch (e) {
      if (e instanceof Error && e.name === "AbortError") {
        // User stopped the stream; partial answer is already rendered.
      } else {
        setError(e instanceof Error ? e.message : "Failed to get answer");
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="flex h-[calc(100vh-65px)]">
      <ChatSidebar
        conversations={conversations}
        activeId={activeConversationId}
        isLoading={isLoadingConversations}
        onNewChat={startNewChat}
        onSelect={selectConversation}
        onDelete={deleteConversation}
        onRename={renameConversation}
      />

      <div className="flex flex-1 flex-col">
        <div className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-4">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                Chat
              </h2>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                Ask questions about your indexed documents.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <label className="text-sm text-zinc-600 dark:text-zinc-400">
                Provider
              </label>
              <select
                value={selectedProvider}
                onChange={(e) => {
                  const name = e.target.value;
                  setSelectedProvider(name);
                  const info = providers.find((p) => p.name === name);
                  setSelectedModel(info?.default_model || "");
                }}
                disabled={isStreaming}
                className="rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-900 focus:border-indigo-500 focus:outline-none disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
              >
                {providers.map((p) => (
                  <option key={p.name} value={p.name} disabled={!p.available}>
                    {p.label} {p.requires_api_key && !p.available ? "(no key)" : ""}
                  </option>
                ))}
              </select>
              <label className="text-sm text-zinc-600 dark:text-zinc-400">
                Model
              </label>
              <input
                type="text"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                disabled={isStreaming}
                placeholder="model"
                className="w-40 rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-900 focus:border-indigo-500 focus:outline-none disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
              />
            </div>
          </div>
        </div>

        <MessageThread
          messages={messages}
          isLoading={false}
          isStreaming={isStreaming}
          error={error}
          bottomRef={bottomRef}
        />

        <ChatInput
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          isLoading={isStreaming}
          isStreaming={isStreaming}
          onStop={handleStop}
        />
      </div>
    </div>
  );
}
