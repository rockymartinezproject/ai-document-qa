import { Citation } from "@/lib/api";

export type Message =
  | { role: "user"; content: string; created_at?: string }
  | {
      role: "assistant";
      content: string;
      citations: Citation[];
      provider: string;
      created_at?: string;
    };
