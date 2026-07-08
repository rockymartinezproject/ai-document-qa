"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "./ThemeToggle";
import { useAuth } from "./AuthProvider";

const navigation = [
  { name: "Home", href: "/" },
  { name: "Chat", href: "/chat" },
  { name: "Upload", href: "/upload" },
  { name: "Dashboard", href: "/dashboard" },
  { name: "Evaluate", href: "/evaluate" },
  { name: "About", href: "/about" },
];

export function Navbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 bg-white/80 dark:bg-zinc-900/80 backdrop-blur border-b border-zinc-200 dark:border-zinc-800">
      <nav
        className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-8"
        aria-label="Global"
      >
        <div className="flex items-center gap-x-2">
          <Link
            href="/"
            className="text-lg font-bold text-indigo-600 dark:text-indigo-400"
          >
            DocQA
          </Link>
        </div>
        <div className="flex items-center gap-x-6">
          {navigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className={`text-sm font-semibold leading-6 transition-colors ${
                pathname === item.href
                  ? "text-indigo-600 dark:text-indigo-400"
                  : "text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100"
              }`}
            >
              {item.name}
            </Link>
          ))}
          {user ? (
            <div className="flex items-center gap-x-3">
              <span className="hidden text-sm text-zinc-600 dark:text-zinc-400 sm:inline">
                {user.email}
              </span>
              <button
                onClick={logout}
                className="text-sm font-semibold text-zinc-700 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-zinc-100"
              >
                Log out
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="text-sm font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
            >
              Log in
            </Link>
          )}
          <ThemeToggle />
        </div>
      </nav>
    </header>
  );
}
