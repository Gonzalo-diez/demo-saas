"use client";

import { useEffect, useRef, useState } from "react";
import { Search, X, Loader2 } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useClients } from "@/features/admin/clients/hooks/use-clients";
import { useSuppliers } from "@/features/admin/suppliers/hooks/use-suppliers";
import type { AccountMovementEntityType, AccountMovementSelectedEntity } from "@/features/admin/account-movements/types";

type AccountMovementsSearchBarProps = {
  entityType: AccountMovementEntityType;
  selectedEntity: AccountMovementSelectedEntity | null;
  onEntitySelect: (entity: AccountMovementSelectedEntity | null) => void;
};

const DEBOUNCE_MS = 300;

export function AccountMovementsSearchBar({
  entityType,
  selectedEntity,
  onEntitySelect,
}: AccountMovementsSearchBarProps) {
  const [inputValue, setInputValue] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timeout = setTimeout(() => {
      setDebouncedSearch(inputValue.trim());
    }, DEBOUNCE_MS);

    return () => clearTimeout(timeout);
  }, [inputValue]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const clientsQuery = useClients({
    page: 1,
    page_size: 8,
    search: debouncedSearch,
    status: "",
    sort: "name",
  });

  const suppliersQuery = useSuppliers({
    page: 1,
    page_size: 8,
    search: debouncedSearch,
    status: "",
  });

  const isClient = entityType === "client";
  const isFetching = isClient ? clientsQuery.isFetching : suppliersQuery.isFetching;

  const results: AccountMovementSelectedEntity[] = isClient
    ? (clientsQuery.data?.clients ?? []).map((client) => ({
        id: client.id,
        name: client.name,
        current_balance: client.current_balance,
      }))
    : (suppliersQuery.data?.suppliers ?? []).map((supplier) => ({
        id: supplier.id,
        name: supplier.name,
        current_balance: supplier.current_balance,
      }));

  const placeholder =
    isClient ? "Buscar cliente por nombre..." : "Buscar proveedor por nombre...";

  function handleSelect(entity: AccountMovementSelectedEntity) {
    onEntitySelect(entity);
    setInputValue(entity.name);
    setIsOpen(false);
  }

  function handleClear() {
    onEntitySelect(null);
    setInputValue("");
    setDebouncedSearch("");
    setIsOpen(false);
  }

  return (
    <div ref={containerRef} className="relative w-full sm:max-w-sm">
      <div className="relative">
        <Search className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={selectedEntity ? selectedEntity.name : inputValue}
          onChange={(e) => {
            onEntitySelect(null);
            setInputValue(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          className="pl-9 pr-9"
        />

        {selectedEntity || inputValue ? (
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="absolute top-1/2 right-1 -translate-y-1/2"
            onClick={handleClear}
          >
            <X className="h-4 w-4" />
          </Button>
        ) : null}
      </div>

      {isOpen && !selectedEntity && debouncedSearch.length > 0 && (
        <div className="absolute z-20 mt-1 w-full overflow-hidden rounded-xl border bg-background shadow-lg">
          {isFetching ? (
            <div className="flex items-center gap-2 p-3 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Buscando...
            </div>
          ) : results.length === 0 ? (
            <div className="p-3 text-sm text-muted-foreground">
              {isClient
                ? "No se encontraron clientes."
                : "No se encontraron proveedores."}
            </div>
          ) : (
            <ul className="max-h-64 overflow-y-auto py-1">
              {results.map((entity) => (
                <li key={entity.id}>
                  <button
                    type="button"
                    className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm hover:bg-muted"
                    onClick={() => handleSelect(entity)}
                  >
                    <span className="truncate">{entity.name}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
