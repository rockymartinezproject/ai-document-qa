"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  { name: "Home", href: "/" },
  { name: "Chat", href: "/chat" },
  { name: "Upload", href: "/upload" },
  { name: "Dashboard", href: "/dashboard" },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800">
      <nav
        className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-8"
        aria-label="Global"
      >
        <div className="flex items-center gap-x-2">
          <Link href="/" className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
            DocQA
          </Link>
        </div>
        <div className="flex gap-x-6">
          {navigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className={`text-sm font-semibold leading-6 ${
                pathname === item.href
                  ? "text-indigo-600 dark:text-indigo-400"
                  : "text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100"
              }`}
            >
              {item.name}
            </Link>
          ))}
        </div>
      </nav>
    </header>
  );
}
