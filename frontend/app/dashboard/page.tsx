"use client";

import { LoadingCard } from "@/components/Loading";

export default function DashboardPage() {
  const stats = [
    { label: "Total Queries", value: "—", sub: "Coming Day 20" },
    { label: "Tokens Used", value: "—", sub: "Coming Day 20" },
    { label: "Est. Cost", value: "—", sub: "Coming Day 20" },
    { label: "Documents", value: "—", sub: "Coming Day 4-5" },
  ];

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          Cost Dashboard
        </h2>
        <p className="mt-2 text-zinc-600 dark:text-zinc-400">
          Track token usage and costs across conversations.
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6"
          >
            <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
              {stat.label}
            </p>
            <p className="mt-2 text-3xl font-bold text-zinc-900 dark:text-zinc-100">
              {stat.value}
            </p>
            <p className="mt-1 text-xs text-zinc-400 dark:text-zinc-600">
              {stat.sub}
            </p>
          </div>
        ))}
      </div>

      {/* Placeholder charts */}
      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Daily Usage
          </h3>
          <div className="mt-4 flex h-48 items-end justify-between gap-2">
            {Array.from({ length: 7 }).map((_, i) => (
              <div
                key={i}
                className="w-full rounded bg-zinc-200 dark:bg-zinc-800"
                style={{ height: `${20 + Math.random() * 60}%` }}
              />
            ))}
          </div>
          <p className="mt-4 text-center text-xs text-zinc-400 dark:text-zinc-600">
            Real charts coming in Day 20-21
          </p>
        </div>

        <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Model Breakdown
          </h3>
          <div className="mt-4 space-y-3">
            {["GPT-4o", "Claude 3.5", "Local LLM"].map((model) => (
              <div key={model} className="flex items-center gap-3">
                <div className="h-2 w-2 rounded-full bg-zinc-300 dark:bg-zinc-700" />
                <span className="flex-1 text-sm text-zinc-600 dark:text-zinc-400">
                  {model}
                </span>
                <span className="text-xs text-zinc-400 dark:text-zinc-600">
                  —
                </span>
              </div>
            ))}
          </div>
          <p className="mt-4 text-center text-xs text-zinc-400 dark:text-zinc-600">
            Real data coming in Day 20-21
          </p>
        </div>
      </div>
    </div>
  );
}
