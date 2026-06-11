import Link from "next/link";

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
        About
      </h1>
      <p className="mt-4 text-zinc-600 dark:text-zinc-400">
        AI Document Q&A is a 30-day build challenge demonstrating production-grade
        RAG (Retrieval-Augmented Generation), vector search, and source citations.
      </p>

      <div className="mt-10 space-y-8">
        <section>
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            What it does
          </h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-zinc-600 dark:text-zinc-400">
            <li>Upload PDFs or paste URLs</li>
            <li>Documents are chunked, embedded, and indexed</li>
            <li>Ask questions in natural language</li>
            <li>Get grounded answers with source citations</li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            Tech Stack
          </h2>
          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
            {techStack.map((item) => (
              <div
                key={item.label}
                className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-4 py-3"
              >
                <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase">
                  {item.label}
                </p>
                <p className="mt-1 text-sm text-zinc-900 dark:text-zinc-100">
                  {item.value}
                </p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            30-Day Challenge
          </h2>
          <p className="mt-3 text-zinc-600 dark:text-zinc-400">
            One commit per day for 30 days. See the{" "}
            <Link
              href="https://github.com/rockymartinezproject/ai-document-qa"
              className="text-indigo-600 hover:underline dark:text-indigo-400"
              target="_blank"
            >
              GitHub repo
            </Link>{" "}
            for the full commit history.
          </p>
        </section>
      </div>
    </div>
  );
}

const techStack = [
  { label: "Frontend", value: "Next.js 14 + TypeScript + Tailwind" },
  { label: "Backend", value: "Python + FastAPI" },
  { label: "Vector DB", value: "Qdrant" },
  { label: "Embeddings", value: "OpenAI / sentence-transformers" },
  { label: "LLM", value: "GPT-4o / Claude 3.5 / Local via Ollama" },
  { label: "Orchestration", value: "LangChain" },
  { label: "Database", value: "SQLite + SQLAlchemy (async)" },
  { label: "Deployment", value: "Docker + Docker Compose" },
];
