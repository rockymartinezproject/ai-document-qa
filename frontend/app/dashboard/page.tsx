"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  api,
  Conversation,
  DocumentOut,
  TotalUsageResponse,
  UsageBreakdownResponse,
  UsageTimeRange,
} from "@/lib/api";
import { LoadingCard } from "@/components/Loading";
import { showToast } from "@/components/Toast";

function formatNumber(n: number): string {
  return n.toLocaleString();
}

function formatCost(cost: number): string {
  if (cost === 0) return "$0.0000";
  if (cost < 0.0001) return "<$0.0001";
  return `$${cost.toFixed(4)}`;
}

function formatShortDate(isoDate: string): string {
  const date = new Date(isoDate + "T00:00:00");
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

type DashboardData = {
  total: TotalUsageResponse;
  documents: DocumentOut[];
  conversations: Conversation[];
  dayBreakdown: UsageBreakdownResponse;
  modelBreakdown: UsageBreakdownResponse;
  conversationBreakdown: UsageBreakdownResponse;
};

export default function DashboardPage() {
  const [timeRange, setTimeRange] = useState<UsageTimeRange>(7);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<DashboardData | null>(null);

  const daysParam = timeRange === "all" ? "all" : timeRange;

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const [
          totalRes,
          documentsRes,
          conversationsRes,
          dayRes,
          modelRes,
          conversationRes,
        ] = await Promise.all([
          api.usage.total(),
          api.documents.list(),
          api.conversations.list(),
          api.usage.breakdown("day", daysParam),
          api.usage.breakdown("model", daysParam),
          api.usage.breakdown("conversation", daysParam),
        ]);

        if (cancelled) return;

        setData({
          total: totalRes.data || {
            total_input_tokens: 0,
            total_output_tokens: 0,
            total_cost: 0,
          },
          documents: documentsRes.data || [],
          conversations: conversationsRes.data || [],
          dayBreakdown: dayRes.data || { group_by: "day", items: [] },
          modelBreakdown: modelRes.data || { group_by: "model", items: [] },
          conversationBreakdown: conversationRes.data || {
            group_by: "conversation",
            items: [],
          },
        });
      } catch (err) {
        if (!cancelled) {
          console.error(err);
          showToast("Failed to load usage data", "error");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [daysParam]);

  const totalQueries = useMemo(
    () => (data?.dayBreakdown.items || []).reduce((sum, item) => sum + item.count, 0),
    [data]
  );

  const totalTokens = useMemo(
    () =>
      (data?.total.total_input_tokens || 0) + (data?.total.total_output_tokens || 0),
    [data]
  );

  const conversationTitles = useMemo(() => {
    const map = new Map<string, string>();
    data?.conversations.forEach((conv) => {
      map.set(conv.id, conv.title || "Untitled");
    });
    return map;
  }, [data]);

  const maxDayTokens = useMemo(() => {
    const totals = data?.dayBreakdown.items.map((i) => i.input_tokens + i.output_tokens) || [];
    return Math.max(1, ...totals);
  }, [data]);

  const maxModelCost = useMemo(() => {
    const costs = data?.modelBreakdown.items.map((i) => i.cost) || [];
    return Math.max(0.0001, ...costs);
  }, [data]);

  const timeRangeButtons: { label: string; value: UsageTimeRange }[] = [
    { label: "7 days", value: 7 },
    { label: "30 days", value: 30 },
    { label: "All time", value: "all" },
  ];

  if (loading || !data) {
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
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <LoadingCard key={i} />
          ))}
        </div>
        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <LoadingCard />
          <LoadingCard />
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            Cost Dashboard
          </h2>
          <p className="mt-2 text-zinc-600 dark:text-zinc-400">
            Track token usage and costs across conversations.
          </p>
        </div>
        <div className="flex rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-1">
          {timeRangeButtons.map((btn) => (
            <button
              key={btn.label}
              onClick={() => setTimeRange(btn.value)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                timeRange === btn.value
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Queries" value={formatNumber(totalQueries)} />
        <StatCard label="Tokens Used" value={formatNumber(totalTokens)} />
        <StatCard label="Est. Cost" value={formatCost(data.total.total_cost)} />
        <StatCard label="Documents" value={formatNumber(data.documents.length)} />
      </div>

      {/* Charts */}
      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        {/* Daily usage */}
        <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Daily Usage
          </h3>
          {data.dayBreakdown.items.length === 0 ? (
            <EmptyState message="No usage data for this period." />
          ) : (
            <div className="mt-6">
              <div className="flex h-48 items-end justify-between gap-2">
                {data.dayBreakdown.items.map((item) => {
                  const total = item.input_tokens + item.output_tokens;
                  const height = `${Math.round((total / maxDayTokens) * 100)}%`;
                  return (
                    <div
                      key={item.label}
                      className="flex flex-1 flex-col items-center gap-2"
                    >
                      <div
                        className="w-full rounded-t bg-indigo-500 hover:bg-indigo-600 dark:bg-indigo-500 dark:hover:bg-indigo-400"
                        style={{ height }}
                        title={`${item.label}: ${formatNumber(total)} tokens, ${formatCost(
                          item.cost
                        )}`}
                      />
                    </div>
                  );
                })}
              </div>
              <div className="mt-2 flex justify-between gap-2 border-t border-zinc-200 pt-2 dark:border-zinc-800">
                {data.dayBreakdown.items.map((item) => (
                  <div
                    key={item.label}
                    className="flex-1 text-center text-[10px] text-zinc-500 dark:text-zinc-400"
                  >
                    {formatShortDate(item.label)}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Model breakdown */}
        <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Model Breakdown
          </h3>
          {data.modelBreakdown.items.length === 0 ? (
            <EmptyState message="No model usage data for this period." />
          ) : (
            <div className="mt-4 space-y-4">
              {data.modelBreakdown.items.map((item) => {
                const total = item.input_tokens + item.output_tokens;
                const width = `${Math.min(
                  100,
                  Math.round((item.cost / maxModelCost) * 100) || 1
                )}%`;
                return (
                  <div key={item.label} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-zinc-700 dark:text-zinc-300">
                        {item.label}
                      </span>
                      <span className="text-zinc-500 dark:text-zinc-400">
                        {formatCost(item.cost)} · {formatNumber(total)} tokens
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-zinc-100 dark:bg-zinc-800">
                      <div
                        className="h-2 rounded-full bg-emerald-500 dark:bg-emerald-400"
                        style={{ width }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Conversation table */}
      <div className="mt-8 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
        <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          Usage by Conversation
        </h3>
        {data.conversationBreakdown.items.length === 0 ? (
          <EmptyState message="No conversation usage data for this period." />
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800">
                  <th className="py-2 font-medium text-zinc-600 dark:text-zinc-400">
                    Conversation
                  </th>
                  <th className="py-2 text-right font-medium text-zinc-600 dark:text-zinc-400">
                    Requests
                  </th>
                  <th className="py-2 text-right font-medium text-zinc-600 dark:text-zinc-400">
                    Input Tokens
                  </th>
                  <th className="py-2 text-right font-medium text-zinc-600 dark:text-zinc-400">
                    Output Tokens
                  </th>
                  <th className="py-2 text-right font-medium text-zinc-600 dark:text-zinc-400">
                    Total Tokens
                  </th>
                  <th className="py-2 text-right font-medium text-zinc-600 dark:text-zinc-400">
                    Cost
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.conversationBreakdown.items.map((item) => {
                  const total = item.input_tokens + item.output_tokens;
                  const title =
                    conversationTitles.get(item.label) || item.label || "Untitled";
                  return (
                    <tr
                      key={item.label}
                      className="border-b border-zinc-100 last:border-0 dark:border-zinc-800/50"
                    >
                      <td className="py-3">
                        <Link
                          href={`/chat?conversation=${item.label}`}
                          className="truncate font-medium text-indigo-600 hover:underline dark:text-indigo-400"
                          title={title}
                        >
                          {title}
                        </Link>
                      </td>
                      <td className="py-3 text-right text-zinc-600 dark:text-zinc-400">
                        {formatNumber(item.count)}
                      </td>
                      <td className="py-3 text-right text-zinc-600 dark:text-zinc-400">
                        {formatNumber(item.input_tokens)}
                      </td>
                      <td className="py-3 text-right text-zinc-600 dark:text-zinc-400">
                        {formatNumber(item.output_tokens)}
                      </td>
                      <td className="py-3 text-right font-medium text-zinc-900 dark:text-zinc-100">
                        {formatNumber(total)}
                      </td>
                      <td className="py-3 text-right text-zinc-600 dark:text-zinc-400">
                        {formatCost(item.cost)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
      <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">{label}</p>
      <p className="mt-2 text-3xl font-bold text-zinc-900 dark:text-zinc-100">{value}</p>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex h-48 items-center justify-center">
      <p className="text-sm text-zinc-400 dark:text-zinc-600">{message}</p>
    </div>
  );
}
