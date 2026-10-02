"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

type Props = {
  currentPage: number;
  totalPages: number;
};

function buildHref(
  pathname: string,
  currentSearchParams: URLSearchParams,
  page: number,
) {
  const params = new URLSearchParams(currentSearchParams.toString());
  if (page <= 1) {
    params.delete("page");
  } else {
    params.set("page", String(page));
  }
  const query = params.toString();
  return query ? `${pathname}?${query}` : pathname;
}

function getPageRange(current: number, total: number): (number | "...")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages: (number | "...")[] = [1];
  if (current > 3) pages.push("...");
  for (
    let p = Math.max(2, current - 1);
    p <= Math.min(total - 1, current + 1);
    p++
  ) {
    pages.push(p);
  }
  if (current < total - 2) pages.push("...");
  pages.push(total);
  return pages;
}

export function CatalogPagination({ currentPage, totalPages }: Props) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  if (totalPages <= 1) return null;

  const pages = getPageRange(currentPage, totalPages);
  const sp = new URLSearchParams(searchParams.toString());

  const baseCls = "rounded-lg border px-3 py-2 text-sm transition-colors";
  const activeCls = "bg-foreground text-background border-foreground";
  const inactiveCls = "hover:bg-muted";

  return (
    <nav
      aria-label="Paginación"
      className="flex flex-wrap items-center justify-center gap-2"
    >
      {currentPage > 1 && (
        <Link
          href={buildHref(pathname, sp, currentPage - 1)}
          className={`${baseCls} ${inactiveCls}`}
        >
          Anterior
        </Link>
      )}

      {pages.map((page, i) =>
        page === "..." ? (
          <span
            key={`ellipsis-${i}`}
            className="px-1 text-sm text-muted-foreground"
          >
            …
          </span>
        ) : (
          <Link
            key={page}
            href={buildHref(pathname, sp, page)}
            aria-current={page === currentPage ? "page" : undefined}
            className={`${baseCls} ${page === currentPage ? activeCls : inactiveCls}`}
          >
            {page}
          </Link>
        ),
      )}

      {currentPage < totalPages && (
        <Link
          href={buildHref(pathname, sp, currentPage + 1)}
          className={`${baseCls} ${inactiveCls}`}
        >
          Siguiente
        </Link>
      )}
    </nav>
  );
}