"use client";

import { useEffect, useState } from "react";
import { Check, Copy, Pencil, Power, RotateCcw } from "lucide-react";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { TenantFormDialog } from "@/features/platform/components/tenant-form-dialog";
import { useSetTenantActive, useTenants } from "@/features/platform/hooks/use-tenants";
import type { Tenant } from "@/features/platform/types";
import { TenantMark } from "@/features/tenant/components/tenant-brand";

type StatusFilter = "all" | "active" | "inactive";

const PAGE_SIZE = 10;

function initialsOf(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  return (parts.length > 1 ? parts[0][0] + parts[1][0] : name.slice(0, 2)).toUpperCase();
}

/** Link a la tienda/panel de la distribuidora: en SU dominio (el que se cargó al crearla). */
function CopyLinkButton({ label, path, domain }: { label: string; path: string; domain: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    const { protocol, port } = window.location;
    // En desarrollo (*.localhost) se conserva el puerto del dev server; en producción
    // el dominio va solo.
    const isLocal = domain === "localhost" || domain.endsWith(".localhost");
    const url = `${protocol}//${domain}${isLocal && port ? `:${port}` : ""}${path}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      toast.success("Link copiado");
      setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error("No se pudo copiar el link");
    }
  };

  return (
    <Button type="button" variant="ghost" size="sm" onClick={copy} title={`Copiar link de ${label.toLowerCase()}`}>
      {copied ? <Check className="mr-1.5 h-4 w-4" /> : <Copy className="mr-1.5 h-4 w-4" />}
      {label}
    </Button>
  );
}

export function TenantsList() {
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<Tenant | null>(null);
  const [deactivating, setDeactivating] = useState<Tenant | null>(null);

  // Debounce de la búsqueda
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 350);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const { data, isLoading, isError, error } = useTenants({
    page,
    page_size: PAGE_SIZE,
    search: search || undefined,
    is_active: status === "all" ? undefined : status === "active",
    sort: "created_at",
  });
  const setActive = useSetTenantActive();

  const tenants = data?.items ?? [];
  const totalPages = data?.total_pages ?? 1;

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row">
        <Input
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          placeholder="Buscar por nombre, código o dominio..."
          className="sm:max-w-sm"
        />
        <select
          value={status}
          onChange={(event) => {
            setStatus(event.target.value as StatusFilter);
            setPage(1);
          }}
          className="h-9 rounded-xl border border-input bg-card px-3 text-sm outline-none focus:ring-2 focus:ring-ring/50"
          aria-label="Filtrar por estado"
        >
          <option value="all">Todas</option>
          <option value="active">Activas</option>
          <option value="inactive">Inactivas</option>
        </select>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Cargando distribuidoras...</p>
      ) : isError ? (
        <p className="text-sm text-destructive">
          {error instanceof Error ? error.message : "No pudimos cargar las distribuidoras"}
        </p>
      ) : tenants.length === 0 ? (
        <div className="rounded-3xl border border-dashed bg-card px-4 py-12 text-center">
          <h3 className="text-lg font-semibold">
            {search || status !== "all" ? "No hay distribuidoras con ese filtro" : "Todavía no hay distribuidoras"}
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {search || status !== "all"
              ? "Probá con otra búsqueda."
              : "Creá la primera con su administrador para que pueda empezar a cargar su negocio."}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-3xl bg-card ring-[1.5px] ring-border">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="min-w-[220px]">Distribuidora</TableHead>
                  <TableHead>Dominio</TableHead>
                  <TableHead>Contacto</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {tenants.map((tenant) => {
                  const isToggling =
                    setActive.isPending && setActive.variables?.tenantId === tenant.id;

                  return (
                    <TableRow key={tenant.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <TenantMark
                            name={tenant.name}
                            initials={initialsOf(tenant.name)}
                            logoUrl={tenant.logo_url}
                            className="h-9 w-9 text-xs"
                          />
                          <span className="font-semibold">{tenant.name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <code className="rounded-md bg-muted px-1.5 py-0.5 text-xs">{tenant.domain}</code>
                        <p className="mt-1 text-[11px] text-muted-foreground">código: {tenant.slug}</p>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{tenant.email ?? "-"}</TableCell>
                      <TableCell>
                        <Badge variant={tenant.is_active ? "default" : "secondary"}>
                          {tenant.is_active ? "Activa" : "Inactiva"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap justify-end gap-1">
                          <CopyLinkButton label="Panel" path="/login" domain={tenant.domain} />
                          <CopyLinkButton label="Tienda" path="/catalogo" domain={tenant.domain} />
                          <Button type="button" variant="outline" size="sm" onClick={() => setEditing(tenant)}>
                            <Pencil className="mr-2 h-4 w-4" />
                            Editar
                          </Button>
                          {tenant.is_active ? (
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              disabled={isToggling}
                              className="border-destructive/20 text-destructive hover:bg-destructive/10 hover:text-destructive"
                              onClick={() => setDeactivating(tenant)}
                            >
                              <Power className="mr-2 h-4 w-4" />
                              Desactivar
                            </Button>
                          ) : (
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              disabled={isToggling}
                              className="border-brand/20 text-brand hover:bg-brand/10 hover:text-brand"
                              onClick={() => setActive.mutate({ tenantId: tenant.id, active: true })}
                            >
                              <RotateCcw className="mr-2 h-4 w-4" />
                              {isToggling ? "Guardando..." : "Activar"}
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            Página {data?.page ?? page} de {totalPages} · {data?.total ?? 0} distribuidoras
          </span>
          <div className="flex gap-2">
            <Button type="button" variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Anterior
            </Button>
            <Button type="button" variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              Siguiente
            </Button>
          </div>
        </div>
      )}

      <TenantFormDialog
        key={editing?.id ?? "none"}
        tenant={editing}
        open={!!editing}
        onOpenChange={(open) => {
          if (!open) setEditing(null);
        }}
      />

      <AlertDialog open={!!deactivating} onOpenChange={(open) => !open && setDeactivating(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Desactivar distribuidora?</AlertDialogTitle>
            <AlertDialogDescription>
              <strong>{deactivating?.name}</strong> y todos sus usuarios (vendedores y clientes) dejan de
              poder ingresar hasta que la vuelvas a activar. No se borra ningún dato.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive hover:bg-destructive/90"
              onClick={() => deactivating && setActive.mutate({ tenantId: deactivating.id, active: false })}
            >
              Desactivar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
