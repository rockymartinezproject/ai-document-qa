"use client";

import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect } from "react";
import { useAuth } from "./AuthProvider";

const PUBLIC_PATHS = new Set(["/", "/about", "/login", "/register"]);

export function AuthGuard({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (isLoading) return;
    if (!user && !PUBLIC_PATHS.has(pathname)) {
      router.replace("/login");
    }
  }, [isLoading, user, pathname, router]);

  // Allow public routes and auth routes to render while loading
  if (isLoading && !PUBLIC_PATHS.has(pathname)) {
    return (
      <div className="flex h-[calc(100vh-65px)] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
      </div>
    );
  }

  return <>{children}</>;
}
