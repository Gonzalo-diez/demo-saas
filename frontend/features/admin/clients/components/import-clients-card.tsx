"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Download, FileSpreadsheet, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { useClientsImportPreview } from "@/features/admin/clients/hooks/use-clients-import-preview";
import { useClientsImportCommit } from "@/features/admin/clients/hooks/use-clients-import-commit";
import { useDownloadClientImportSample } from "@/features/admin/clients/hooks/use-download-client-import-sample";
import { triggerBlobDownload } from "@/lib/fetcher";
import type {
  ImportMode,
  ClientImportPreviewResponse,
  ClientImportRow,
  ClientImportCommitResponse,
} from "@/features/admin/clients/types";

type ImportClientsCardProps = {
  onSuccess: () => void;
};

export function ImportClientsCard({ onSuccess }: ImportClientsCardProps) {
  const previewMutation = useClientsImportPreview();
  const commitMutation = useClientsImportCommit();
  const downloadSampleMutation = useDownloadClientImportSample();

  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<ImportMode>("upsert");
  const [previewData, setPreviewData] =
    useState<ClientImportPreviewResponse | null>(null);
  const [commitResult, setCommitResult] =
    useState<ClientImportCommitResponse | null>(null);

  const hasValidRows = (previewData?.rows_valid.length ?? 0) > 0;
  const hasInvalidRows = (previewData?.rows_invalid.length ?? 0) > 0;

  const invalidPreview = useMemo(() => {
    return previewData?.rows_invalid.slice(0, 10) ?? [];
  }, [previewData]);

  async function handlePreview() {
    try {
      if (!file) return;

      const result = await previewMutation.mutateAsync(file);
      setPreviewData(result);
      setCommitResult(null);
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "No se pudo analizar el archivo",
        {
          position: "top-right",
          duration: 4000,
        },
      );
    }
  }

  async function handleCommit() {
    try {
      if (!previewData || previewData.rows_valid.length === 0) return;

      const result = await commitMutation.mutateAsync({
        rows: previewData.rows_valid as ClientImportRow[],
        mode,
      });

      toast.success("Importación completada", {
        position: "top-right",
        duration: 4000,
      });

      setCommitResult(result);
      setFile(null);
      setPreviewData(null);
      onSuccess();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Error al importar clientes",
        {
          position: "top-right",
          duration: 4000,
        },
      );
    }
  }

  async function handleDownloadSample() {
    try {
      const blob = await downloadSampleMutation.mutateAsync();
      triggerBlobDownload(blob, "clientes_ejemplo.xlsx");
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "No se pudo descargar el Excel de ejemplo",
        { position: "top-right", duration: 4000 },
      );
    }
  }

  return (
    <div className="space-y-5 rounded-2xl border bg-background p-4 shadow-sm sm:p-6">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="rounded-xl border bg-muted/40 p-2">
            <FileSpreadsheet className="h-4 w-4" />
          </div>

          <div className="space-y-1">
            <h2 className="text-lg font-semibold">
              Importar productos por Excel
            </h2>
            <p className="text-sm text-muted-foreground">
              Subí un archivo, revisá las filas válidas e inválidas, y después
              confirmá.
            </p>
            <p className="text-xs text-muted-foreground">
              El archivo debe incluir columnas como nombre de la empresa del
              cliente, cuit, tipo de cliente (compañia, kiosko, etc), si esta
              activo (VERDADERO O FALSO), nombre de sucursal, direccion de
              sucursal (calle), ciudad, latitud, longitud, nombre del contacto
              (persona, opcional), telefono de contacto (opcional), referencia
              (opcional), si es sucursal principal y si la sucursal esta activa.
            </p>
            <p className="text-xs text-muted-foreground">
              También podés incluir <strong>email</strong> y{" "}
              <strong>password</strong> (ambos opcionales) para que el
              cliente pueda loguearse en la tienda online. Si dejás la
              contraseña vacía al crear un cliente nuevo, el sistema genera
              una automáticamente y te la muestra al terminar de importar.
              Si estás actualizando un cliente que ya existe, dejarla vacía{" "}
              <strong>no le cambia la contraseña actual</strong>.
            </p>
          </div>
        </div>

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleDownloadSample}
          disabled={downloadSampleMutation.isPending}
          className="shrink-0"
        >
          <Download className="mr-2 h-4 w-4" />
          {downloadSampleMutation.isPending
            ? "Descargando..."
            : "Descargar ejemplo"}
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_220px_180px]">
        <div className="space-y-2">
          <label className="text-sm font-medium">Archivo Excel</label>
          <Input
            type="file"
            accept=".xlsx,.xls"
            onChange={(e) => {
              const selectedFile = e.target.files?.[0] ?? null;
              setFile(selectedFile);
              setPreviewData(null);
              setCommitResult(null);
            }}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Modo</label>
          <Select
            value={mode}
            onValueChange={(value) => setMode(value as ImportMode)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleccionar modo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="upsert">Upsert</SelectItem>
              <SelectItem value="create">Solo crear</SelectItem>
              <SelectItem value="update">Solo actualizar</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-end">
          <Button
            type="button"
            onClick={handlePreview}
            disabled={!file || previewMutation.isPending}
            className="w-full"
          >
            <Upload className="mr-2 h-4 w-4" />
            {previewMutation.isPending ? "Analizando..." : "Previsualizar"}
          </Button>
        </div>
      </div>

      {previewMutation.error && (
        <div className="rounded-md border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {previewMutation.error instanceof Error
            ? previewMutation.error.message
            : "No se pudo analizar el archivo"}
        </div>
      )}

      {previewData && (
        <div className="space-y-4 rounded-xl border p-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Total filas</p>
              <p className="text-xl font-semibold">{previewData.total_rows}</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Válidas</p>
              <p className="text-xl font-semibold">{previewData.valid_rows}</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Inválidas</p>
              <p className="text-xl font-semibold">
                {previewData.invalid_rows}
              </p>
            </div>
          </div>

          {hasInvalidRows && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold">Errores detectados</h3>

              <div className="grid gap-3 sm:hidden">
                {invalidPreview.map((row) => (
                  <div key={row.row_number} className="rounded-xl border p-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold">
                        Fila {row.row_number}
                      </p>
                    </div>

                    <div className="mt-3 grid gap-2 text-sm">
                      <div>
                        <p className="text-xs text-muted-foreground">
                          Nombre de empresa
                        </p>
                        <p>{String(row.data?.client_name ?? "-")}</p>
                      </div>
                      <div className="grid gap-2 xs:grid-cols-2 sm:grid-cols-2">
                        <div>
                          <p className="text-xs text-muted-foreground">Email</p>
                          <p>{String(row.data?.email ?? "-")}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Password
                          </p>
                          <p>{row.data?.password ? "••••••" : "-"}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">CUIT</p>
                          <p>{String(row.data?.tax_id ?? "-")}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Tipo de cliente
                          </p>
                          <p>{String(row.data?.client_type ?? "-")}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Activo/Inactivo
                          </p>
                          <p>{Boolean(row.data?.is_active ?? "-")}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Nombre de la sucursal
                          </p>
                          <p>{String(row.data?.branch_name ?? "-")}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Dirección
                          </p>
                          <p>{String(row.data?.address ?? "-")}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Ciudad
                          </p>
                          <p>{String(row.data?.city ?? "-")}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Latitud
                          </p>
                          <p>{String(row.data?.lat ?? "-")}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Longitud
                          </p>
                          <p>{String(row.data?.lng ?? "-")}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Nombre de contacto
                          </p>
                          <p>{String(row.data?.contact_name ?? "-")}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Telefono de contacto
                          </p>
                          <p>{String(row.data?.contact_phone ?? "-")}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Referencia
                          </p>
                          <p>{String(row.data?.reference ?? "-")}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Sucursal principal
                          </p>
                          <p>{Boolean(row.data?.is_main ?? "-")}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Sucursal activa/inactiva
                          </p>
                          <p>{Boolean(row.data?.branch_is_active ?? "-")}</p>
                        </div>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Errores</p>
                        <div className="mt-1 space-y-1">
                          {row.errors.map((error, index) => (
                            <p key={index} className="text-sm text-destructive">
                              {error}
                            </p>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="hidden overflow-hidden rounded-xl border sm:block">
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Fila</TableHead>
                        <TableHead>Nombre de la empresa</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>Password</TableHead>
                        <TableHead>CUIT</TableHead>
                        <TableHead>Tipo de cliente</TableHead>
                        <TableHead>Activo/Inactivo</TableHead>
                        <TableHead>Nombre de la sucursal</TableHead>
                        <TableHead>Dirección</TableHead>
                        <TableHead>Ciudad</TableHead>
                        <TableHead>Latitud</TableHead>
                        <TableHead>Longitud</TableHead>
                        <TableHead>Nombre de contacto</TableHead>
                        <TableHead>Telefono de contacto</TableHead>
                        <TableHead>Referencia</TableHead>
                        <TableHead>Sucursal principal</TableHead>
                        <TableHead>Sucursal activa/Inactiva</TableHead>
                        <TableHead>Errores</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {invalidPreview.map((row) => (
                        <TableRow key={row.row_number}>
                          <TableCell>{row.row_number}</TableCell>
                          <TableCell>
                            {String(row.data?.client_name ?? "-")}
                          </TableCell>
                          <TableCell>
                            {String(row.data?.email ?? "-")}
                          </TableCell>
                          <TableCell>
                            {row.data?.password ? "••••••" : "-"}
                          </TableCell>
                          <TableCell>
                            {String(row.data?.tax_id ?? "-")}
                          </TableCell>
                          <TableCell>
                            {String(row.data?.client_type ?? "-")}
                          </TableCell>
                          <TableCell>
                            {Boolean(row.data?.is_active ?? "-")}
                          </TableCell>
                          <TableCell>
                            {String(row.data?.branch_name ?? "-")}
                          </TableCell>
                          <TableCell>
                            {String(row.data?.address ?? "-")}
                          </TableCell>
                          <TableCell>{String(row.data?.city ?? "-")}</TableCell>
                          <TableCell>{Number(row.data?.lat ?? "-")}</TableCell>
                          <TableCell>{Number(row.data?.lng ?? "-")}</TableCell>
                          <TableCell>
                            {String(row.data?.contact_name ?? "-")}
                          </TableCell>
                          <TableCell>
                            {String(row.data?.contact_phone ?? "-")}
                          </TableCell>
                          <TableCell>
                            {String(row.data?.reference ?? "-")}
                          </TableCell>
                          <TableCell>
                            {Boolean(row.data?.is_main ?? "-")}
                          </TableCell>
                          <TableCell>
                            {Boolean(row.data?.branch_is_active ?? "-")}
                          </TableCell>
                          <TableCell>
                            <div className="space-y-1">
                              {row.errors.map((error, index) => (
                                <p key={index} className="text-destructive">
                                  {error}
                                </p>
                              ))}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>

              {previewData.rows_invalid.length > 10 && (
                <p className="text-xs text-muted-foreground">
                  Mostrando solo los primeros 10 errores.
                </p>
              )}
            </div>
          )}

          <div className="flex flex-col gap-2 border-t pt-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              {hasValidRows
                ? `${previewData.valid_rows} filas listas para importar.`
                : "No hay filas válidas para importar."}
            </p>

            <Button
              type="button"
              onClick={handleCommit}
              disabled={!hasValidRows || commitMutation.isPending}
              className="w-full sm:w-auto"
            >
              {commitMutation.isPending
                ? "Importando..."
                : "Confirmar importación"}
            </Button>
          </div>
        </div>
      )}

      {commitResult && commitResult.generated_passwords.length > 0 && (
        <div className="space-y-3 rounded-xl border border-brand/20 bg-brand/5 p-4">
          <h3 className="text-sm font-semibold">
            Contraseñas generadas automáticamente
          </h3>
          <p className="text-xs text-muted-foreground">
            Estos clientes se crearon sin contraseña en el archivo, así que
            se les generó una. Copiala y pasásela para que puedan entrar a
            la tienda online — no se va a volver a mostrar.
          </p>
          <div className="overflow-hidden rounded-lg border bg-background">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Cliente</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Contraseña</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {commitResult.generated_passwords.map((entry, index) => (
                    <TableRow key={`${entry.client_name}-${index}`}>
                      <TableCell>{entry.client_name}</TableCell>
                      <TableCell>{entry.email ?? "-"}</TableCell>
                      <TableCell className="font-mono">
                        {entry.password}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}