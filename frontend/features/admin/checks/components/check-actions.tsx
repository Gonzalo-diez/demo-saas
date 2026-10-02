"use client";

import { useState } from "react";
import { toast } from "sonner";
import { CheckCheck, Landmark, Loader2, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import {
  useCreditCheck,
  useDepositCheck,
  useRejectCheck,
} from "@/features/admin/checks/hooks/use-check-actions";
import type { Check } from "@/features/admin/checks/types";

type CheckActionsProps = {
  check: Check;
};

export function CheckActions({ check }: CheckActionsProps) {
  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectNotes, setRejectNotes] = useState("");

  const depositCheck = useDepositCheck();
  const creditCheck = useCreditCheck();
  const rejectCheck = useRejectCheck();

  async function handleDeposit() {
    try {
      await depositCheck.mutateAsync(check.id);
      toast.success("Cheque marcado como depositado", { position: "top-right", duration: 4000 });
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "No se pudo depositar el cheque",
        { position: "top-right", duration: 4000 }
      );
    }
  }

  async function handleCredit() {
    try {
      await creditCheck.mutateAsync(check.id);
      toast.success("Cheque acreditado. Se generó el movimiento de cuenta corriente.", {
        position: "top-right",
        duration: 4000,
      });
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "No se pudo acreditar el cheque",
        { position: "top-right", duration: 4000 }
      );
    }
  }

  async function handleReject() {
    try {
      await rejectCheck.mutateAsync({ checkId: check.id, data: { notes: rejectNotes || null } });
      toast.success("Cheque rechazado", { position: "top-right", duration: 4000 });
      setRejectOpen(false);
      setRejectNotes("");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "No se pudo rechazar el cheque",
        { position: "top-right", duration: 4000 }
      );
    }
  }

  if (check.status === "acreditado" || check.status === "rechazado") {
    return <span className="text-xs text-muted-foreground">Sin acciones</span>;
  }

  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      {check.status === "pendiente" && (
        <Button
          variant="outline"
          size="sm"
          onClick={handleDeposit}
          disabled={depositCheck.isPending}
        >
          {depositCheck.isPending ? (
            <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
          ) : (
            <Landmark className="mr-1.5 h-3.5 w-3.5" />
          )}
          Depositar
        </Button>
      )}

      <Button
        variant="default"
        size="sm"
        onClick={handleCredit}
        disabled={creditCheck.isPending}
      >
        {creditCheck.isPending ? (
          <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
        ) : (
          <CheckCheck className="mr-1.5 h-3.5 w-3.5" />
        )}
        Acreditar
      </Button>

      <Button
        variant="ghost"
        size="sm"
        className="text-destructive hover:text-destructive"
        onClick={() => setRejectOpen(true)}
      >
        <XCircle className="mr-1.5 h-3.5 w-3.5" />
        Rechazar
      </Button>

      <Dialog open={rejectOpen} onOpenChange={setRejectOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Rechazar cheque</DialogTitle>
            <DialogDescription>
              El cheque #{check.check_number} se marcará como rechazado (rebotó). Como nunca se
              tocó el saldo, no hay nada que revertir.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Notas (opcional)</label>
            <Textarea
              value={rejectNotes}
              onChange={(event) => setRejectNotes(event.target.value)}
              placeholder="Motivo del rechazo"
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setRejectOpen(false)}>
              Cancelar
            </Button>
            <Button variant="destructive" onClick={handleReject} disabled={rejectCheck.isPending}>
              {rejectCheck.isPending ? "Rechazando..." : "Confirmar rechazo"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
