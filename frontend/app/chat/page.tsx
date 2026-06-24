"use client";

import { useEffect, useRef, useState } from "react";
import { api, askStream, ChatMessage, Conversation } from "@/lib/api";
import {
  ChatInput,
  ChatSidebar,
  MessageThread,
  Message,
} from "@/components/chat";

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<
    string | undefined
  >();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

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
      />

      <div className="flex flex-1 flex-col">
        <div className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-4">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            Chat
          </h2>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Ask questions about your indexed documents.
          </p>
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
