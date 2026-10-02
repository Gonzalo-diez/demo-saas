"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { FileText, Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { useClients } from "@/features/admin/clients/hooks/use-clients";
import type { ClientBranch } from "@/features/admin/clients/types";
import { useSalesInvoiceImportPreview } from "@/features/admin/sales-invoices/hooks/use-sales-invoice-import-preview";
import { useSalesInvoiceImportCommitFile } from "@/features/admin/sales-invoices/hooks/use-sales-invoice-import-commit-file";
import { SalesInvoiceImportPreview } from "@/features/admin/sales-invoices/components/sales-invoice-import-preview";
import type { SalesInvoiceImportPreviewResponse } from "@/features/admin/sales-invoices/types";

type ImportSalesInvoiceCardProps = {
  onSuccess: () => void;
}

export function SalesInvoiceImportCard({ onSuccess }: ImportSalesInvoiceCardProps) {
  const clientsQuery = useClients({
    page: 1,
    page_size: 20,
    search: "",
    status: "active",
    sort: "name",
  });

  const previewMutation = useSalesInvoiceImportPreview();
  const commitFileMutation = useSalesInvoiceImportCommitFile();

  const [file, setFile] = useState<File | null>(null);
  const [clientId, setClientId] = useState<number | null>(null);
  const [clientBranchId, setClientBranchId] = useState<number | null>(null);
  const [notes, setNotes] = useState("");
  const [previewData, setPreviewData] =
    useState<SalesInvoiceImportPreviewResponse | null>(null);

  const clients = clientsQuery.data?.clients ?? [];
  const selectedClient = clients.find((client) => client.id === clientId) ?? null;

  const availableBranches = useMemo<ClientBranch[]>(() => {
    return (selectedClient?.branches ?? []).filter((branch) => branch.is_active);
  }, [selectedClient]);

  // Cuando cambia el cliente seleccionado (o su lista de sucursales),
  // reasignamos la sucursal si la actual ya no es válida. Ajustamos el
  // estado durante el render en vez de en un efecto para evitar un
  // render en cascada: https://react.dev/learn/you-might-not-need-an-effect
  const availableBranchIds = availableBranches.map((branch) => branch.id).join(",");
  const resetKey = `${selectedClient?.id ?? "none"}|${availableBranchIds}`;
  const [prevResetKey, setPrevResetKey] = useState(resetKey);
  if (resetKey !== prevResetKey) {
    setPrevResetKey(resetKey);

    if (!selectedClient) {
      setClientBranchId(null);
    } else {
      const branchStillExists = availableBranches.some(
        (branch) => branch.id === clientBranchId
      );

      if (!branchStillExists) {
        if (availableBranches.length === 1) {
          setClientBranchId(availableBranches[0].id);
        } else {
          const mainBranch = availableBranches.find((branch) => branch.is_main);
          setClientBranchId(mainBranch?.id ?? null);
        }
      }
    }
  }

  async function handlePreview() {
    try {
      if (!file) return;

      const result = await previewMutation.mutateAsync(file);
      setPreviewData(result);
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "No se pudo analizar el archivo",
        {
          position: "top-right",
          duration: 4000,
        }
      );
    }
  }

  async function handleCommitFile() {
    try {
      if (!file) return;

      if (!clientId) {
        toast.error("Seleccioná un cliente antes de importar el remito", {
          position: "top-right",
          duration: 4000,
        });
        return;
      }

      await commitFileMutation.mutateAsync({
        file,
        client_id: clientId,
        client_branch_id: clientBranchId,
        notes: notes || null,
      });

      toast.success("Remito importado correctamente", {
        position: "top-right",
        duration: 4000,
      });

      setFile(null);
      setClientId(null);
      setClientBranchId(null);
      onSuccess();
      setNotes("");
      setPreviewData(null);
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "No se pudo importar el remito",
        {
          position: "top-right",
          duration: 4000,
        }
      );
    }
  }

  return (
    <div className="space-y-5 rounded-2xl border bg-background p-4 shadow-sm sm:p-6">
      <div className="flex items-start gap-3">
        <div className="rounded-xl border bg-muted/40 p-2">
          <FileText className="h-4 w-4" />
        </div>

        <div className="space-y-1">
          <h2 className="text-lg font-semibold">Importar remito por archivo</h2>
          <p className="text-sm text-muted-foreground">
            Subí un remito, revisá el preview y después confirmá la importación.
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium">Archivo</label>
          <Input
            type="file"
            accept=".pdf"
            onChange={(e) => {
              const selectedFile = e.target.files?.[0] ?? null;
              setFile(selectedFile);
              setPreviewData(null);
            }}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Cliente opcional para vincular</label>
          <Select
            value={clientId ? String(clientId) : "__empty__"}
            onValueChange={(value) =>
              setClientId(value === "__empty__" ? null : Number(value))
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleccionar cliente" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__empty__">Sin seleccionar</SelectItem>
              {clients.map((client) => (
                <SelectItem key={client.id} value={String(client.id)}>
                  {client.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium">Sucursal opcional</label>
          <Select
            value={clientBranchId ? String(clientBranchId) : "__empty__"}
            onValueChange={(value) =>
              setClientBranchId(value === "__empty__" ? null : Number(value))
            }
            disabled={!selectedClient}
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleccionar sucursal" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__empty__">Sin seleccionar</SelectItem>
              {availableBranches.map((branch) => (
                <SelectItem key={branch.id} value={String(branch.id)}>
                  {branch.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Notas</label>
          <Input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Opcional"
          />
        </div>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
        <Button
          type="button"
          variant="outline"
          className="w-full sm:w-auto"
          onClick={handlePreview}
          disabled={!file || previewMutation.isPending}
        >
          <Upload className="mr-2 h-4 w-4" />
          {previewMutation.isPending ? "Analizando..." : "Previsualizar"}
        </Button>

        <Button
          type="button"
          className="w-full sm:w-auto"
          onClick={handleCommitFile}
          disabled={!file || !clientId || commitFileMutation.isPending}
        >
          {commitFileMutation.isPending ? "Importando..." : "Importar archivo"}
        </Button>
      </div>

      <SalesInvoiceImportPreview preview={previewData} />
    </div>
  );
}