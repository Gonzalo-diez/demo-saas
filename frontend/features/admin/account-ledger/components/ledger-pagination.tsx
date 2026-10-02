"use client";

import { Button } from "@/components/ui/button";

type LedgerPaginationProps = {
  page: number;
  totalPages: number;
  isLoading?: boolean;
  onPageChange: (page: number) => void;
};

export function LedgerPagination({
  page,
  totalPages,
  isLoading,
  onPageChange,
}: LedgerPaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-end gap-3 pt-2">
      <span className="text-xs text-muted-foreground">
        Página {page} de {totalPages}
      </span>
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(Math.max(1, page - 1))}
        disabled={page === 1 || isLoading}
      >
        Anterior
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(Math.min(totalPages, page + 1))}
        disabled={page === totalPages || isLoading}
      >
        Siguiente
      </Button>
    </div>
  );
}
