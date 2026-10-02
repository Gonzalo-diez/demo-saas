"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { useSession } from "@/features/admin/auth/hooks/use-session";

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { data, isLoading, isError } = useSession();

  useEffect(() => {
    if (!isLoading && (isError || !data)) {
      router.replace("/login");
    }
  }, [data, isError, isLoading, router]);

  if (isError || !data) {
    return null;
  }

  return <AppShell>{children}</AppShell>;
}