import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-24 lg:px-8">
      <div className="mx-auto max-w-2xl text-center">
        <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 sm:text-6xl">
          AI Document Q&A
        </h1>
        <p className="mt-6 text-lg leading-8 text-zinc-600 dark:text-zinc-400">
          Upload documents (PDFs, URLs) and ask questions in natural language.
          Get grounded answers with source citations powered by RAG and vector
          search.
        </p>
        <div className="mt-10 flex items-center justify-center gap-x-6">
          <Link
            href="/chat"
            className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
          >
            Start Chatting
          </Link>
          <Link
            href="/upload"
            className="text-sm font-semibold leading-6 text-zinc-900 dark:text-zinc-100"
          >
            Upload Documents <span aria-hidden="true">&rarr;</span>
          </Link>
        </div>
      </div>

      <div className="mx-auto mt-16 grid max-w-5xl grid-cols-1 gap-8 sm:grid-cols-3">
        {features.map((feature) => (
          <div
            key={feature.name}
            className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6"
          >
            <div className="text-base font-semibold leading-7 text-zinc-900 dark:text-zinc-100">
              {feature.name}
            </div>
            <p className="mt-2 text-sm leading-6 text-zinc-600 dark:text-zinc-400">
              {feature.description}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

const features = [
  {
    name: "RAG Pipeline",
    description:
      "Retrieval-Augmented Generation with semantic chunking and vector search for accurate, grounded answers.",
  },
  {
    name: "Hybrid Search",
    description:
      "Combine vector similarity with BM25 keyword search for better recall across all types of queries.",
  },
  {
    name: "Source Citations",
    description:
      "Every answer includes citations back to the original document chunks so you can verify sources.",
  },
];
