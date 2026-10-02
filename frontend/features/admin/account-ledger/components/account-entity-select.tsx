"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getAccountEntityLabels } from "@/features/admin/account-movements/components/account-entity-labels";
import { formatCurrency } from "@/features/admin/account-movements/components/account-movement-helpers";
import { useClients } from "@/features/admin/clients/hooks/use-clients";
import { useSuppliers } from "@/features/admin/suppliers/hooks/use-suppliers";
import type {
  AccountMovementEntityType,
  AccountMovementSelectedEntity,
} from "@/features/admin/account-movements/types";

type Props = {
  entityType: AccountMovementEntityType;
  selectedEntity: AccountMovementSelectedEntity | null;
  onEntitySelect: (entity: AccountMovementSelectedEntity | null) => void;
};

const PAGE_SIZE = 100;

export function AccountEntitySelect({
  entityType,
  selectedEntity,
  onEntitySelect,
}: Props) {
  const labels = getAccountEntityLabels(entityType);

  const clientsQuery = useClients({
    page: 1,
    page_size: PAGE_SIZE,
    search: "",
    status: "active",
    sort: "name",
  });

  const suppliersQuery = useSuppliers({
    page: 1,
    page_size: PAGE_SIZE,
    search: "",
    status: "active",
  });

  const isLoading =
    entityType === "client" ? clientsQuery.isLoading : suppliersQuery.isLoading;

  const options: AccountMovementSelectedEntity[] =
    entityType === "client"
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

  function handleValueChange(value: string) {
    if (!value || value === "none") {
      onEntitySelect(null);
      return;
    }

    const entity = options.find((option) => String(option.id) === value);
    if (entity) {
      onEntitySelect(entity);
    }
  }

  return (
    <Select
      value={selectedEntity ? String(selectedEntity.id) : ""}
      onValueChange={handleValueChange}
      disabled={isLoading}
    >
      <SelectTrigger className="w-full sm:max-w-sm">
        <SelectValue placeholder={isLoading ? "Cargando..." : labels.selectPlaceholder} />
      </SelectTrigger>
      <SelectContent>
        {options.length === 0 ? (
          <div className="px-2 py-3 text-xs text-muted-foreground">
            {labels.selectEmptyMessage}
          </div>
        ) : (
          options.map((option) => (
            <SelectItem key={option.id} value={String(option.id)}>
              {option.name}
              <span className="ml-auto text-muted-foreground">
                {formatCurrency(option.current_balance)}
              </span>
            </SelectItem>
          ))
        )}
      </SelectContent>
    </Select>
  );
}