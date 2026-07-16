"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { User } from "@/lib/auth";
import { useAuth } from "@/components/AuthProvider";
import { LoadingCard, LoadingSpinner } from "@/components/Loading";
import { showToast } from "@/components/Toast";

function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleString();
}

export default function AdminPage() {
  const { user, isLoading: authLoading } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);

  const isAdmin = user?.is_superuser ?? false;

  useEffect(() => {
    if (!isAdmin) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function loadUsers() {
      setLoading(true);
      try {
        const res = await api.admin.listUsers();
        if (!cancelled) {
          setUsers(res.data || []);
        }
      } catch (err) {
        if (!cancelled) {
          console.error(err);
          showToast("Failed to load users", "error");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadUsers();
    return () => {
      cancelled = true;
    };
  }, [isAdmin]);

  async function toggleActive(target: User) {
    setUpdating(target.id);
    try {
      const res = await api.admin.updateUser(target.id, {
        is_active: !target.is_active,
      });
      if (res.data) {
        setUsers((prev) => prev.map((u) => (u.id === res.data!.id ? res.data! : u)));
        showToast(
          `${res.data.email} is now ${res.data.is_active ? "active" : "inactive"}`,
          "success"
        );
      }
    } catch (err) {
      console.error(err);
      showToast("Failed to update user", "error");
    } finally {
      setUpdating(null);
    }
  }

  async function toggleSuperuser(target: User) {
    setUpdating(target.id);
    try {
      const res = await api.admin.updateUser(target.id, {
        is_superuser: !target.is_superuser,
      });
      if (res.data) {
        setUsers((prev) => prev.map((u) => (u.id === res.data!.id ? res.data! : u)));
        showToast(
          `${res.data.email} admin status updated`,
          "success"
        );
      }
    } catch (err) {
      console.error(err);
      showToast("Failed to update user", "error");
    } finally {
      setUpdating(null);
    }
  }

  if (authLoading || loading) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-12">
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Admin</h2>
        <div className="mt-8 grid gap-4">
          <LoadingCard />
          <LoadingCard />
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-12 text-center">
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          Access denied
        </h2>
        <p className="mt-4 text-zinc-600 dark:text-zinc-400">
          You need administrator privileges to view this page.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          User Management
        </h2>
        <p className="mt-2 text-zinc-600 dark:text-zinc-400">
          Activate, deactivate, and manage administrator access.
        </p>
      </div>

      <div className="overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
        <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
          <thead className="bg-zinc-50 dark:bg-zinc-800/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                Active
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                Admin
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                Created
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
            {users.map((u) => (
              <tr key={u.id}>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-zinc-900 dark:text-zinc-100">
                  {u.email}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm">
                  <span
                    className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${
                      u.is_active
                        ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
                        : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
                    }`}
                  >
                    {u.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm">
                  <span
                    className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${
                      u.is_superuser
                        ? "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300"
                        : "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-300"
                    }`}
                  >
                    {u.is_superuser ? "Admin" : "User"}
                  </span>
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-zinc-600 dark:text-zinc-400">
                  {formatDate(u.created_at)}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => toggleActive(u)}
                      disabled={updating === u.id}
                      className="rounded-md border border-zinc-300 px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
                    >
                      {updating === u.id ? (
                        <LoadingSpinner size="sm" />
                      ) : u.is_active ? (
                        "Deactivate"
                      ) : (
                        "Activate"
                      )}
                    </button>
                    <button
                      onClick={() => toggleSuperuser(u)}
                      disabled={updating === u.id}
                      className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500 disabled:opacity-50 dark:bg-indigo-700 dark:hover:bg-indigo-600"
                    >
                      {updating === u.id ? (
                        <LoadingSpinner size="sm" />
                      ) : u.is_superuser ? (
                        "Remove admin"
                      ) : (
                        "Make admin"
                      )}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  className="px-6 py-8 text-center text-sm text-zinc-500 dark:text-zinc-400"
                >
                  No users found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
