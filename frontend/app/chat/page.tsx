"use client";

import { useEffect, useRef, useState } from "react";
import { api, ChatMessage, Conversation } from "@/lib/api";
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

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const question = input.trim();
    const now = new Date().toISOString();
    setInput("");
    setError(null);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: question, created_at: now },
    ]);
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
          created_at: new Date().toISOString(),
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
          isLoading={isLoading}
          error={error}
          bottomRef={bottomRef}
        />

        <ChatInput
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
