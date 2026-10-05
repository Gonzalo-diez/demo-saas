"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { PlatformShell } from "@/features/platform/components/platform-shell";
import { usePlatformSession } from "@/features/platform/hooks/use-platform-auth";

export default function PlatformPanelLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { data, isLoading, isError } = usePlatformSession();

  useEffect(() => {
    if (!isLoading && (isError || !data)) router.replace("/platform/login");
  }, [data, isError, isLoading, router]);

  if (isLoading || isError || !data) return null;

  return <PlatformShell>{children}</PlatformShell>;
}
