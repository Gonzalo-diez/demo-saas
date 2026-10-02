"use client";

import { useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ledgerDateRangeFilterSchema } from "@/features/admin/account-ledger/schemas/account-ledger-schema";

type LedgerDateRangeFilterProps = {
  dateFrom: string;
  dateTo: string;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
};

export function LedgerDateRangeFilter({
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
}: LedgerDateRangeFilterProps) {
  const validation = useMemo(
    () =>
      ledgerDateRangeFilterSchema.safeParse({
        date_from: dateFrom,
        date_to: dateTo,
      }),
    [dateFrom, dateTo]
  );

  const errorMessage = validation.success
    ? null
    : validation.error.issues[0]?.message;

  return (
    <div className="flex flex-col gap-1">
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="ledger-date-from" className="text-xs">
            Desde
          </Label>
          <Input
            id="ledger-date-from"
            type="date"
            value={dateFrom}
            onChange={(event) => onDateFromChange(event.target.value)}
            className="h-8 w-[150px]"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="ledger-date-to" className="text-xs">
            Hasta
          </Label>
          <Input
            id="ledger-date-to"
            type="date"
            value={dateTo}
            onChange={(event) => onDateToChange(event.target.value)}
            className="h-8 w-[150px]"
          />
        </div>
        {(dateFrom || dateTo) && (
          <button
            type="button"
            onClick={() => {
              onDateFromChange("");
              onDateToChange("");
            }}
            className="h-8 px-2 text-xs text-muted-foreground underline underline-offset-2 hover:text-foreground"
          >
            Limpiar fechas
          </button>
        )}
      </div>
      {errorMessage && (
        <p className="text-xs text-destructive">{errorMessage}</p>
      )}
    </div>
  );
}