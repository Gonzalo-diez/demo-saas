"use client";

import { useUpdateOrderStatus } from "@/features/admin/orders/hooks/use-update-order-status";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { OrderStatus } from "@/features/admin/orders/types";

interface Props {
  orderId: number;
  currentStatus: OrderStatus;
}

export function UpdateOrderStatusSelect({ orderId, currentStatus }: Props) {
  const { mutate, isPending } = useUpdateOrderStatus();

  return (
    <Select
      disabled={isPending}
      defaultValue={currentStatus}
      onValueChange={(value) => mutate({ orderId, status: value as OrderStatus })}
    >
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Cambiar estado" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">Todos los estados</SelectItem>
        <SelectItem value="pending_confirmation">Pendiente</SelectItem>
        <SelectItem value="confirmed">Confirmado</SelectItem>
        <SelectItem value="preparing">Preparando</SelectItem>
        <SelectItem value="shipped">Enviado</SelectItem>
        <SelectItem value="delivered">Entregado</SelectItem>
        <SelectItem value="cancelled">Cancelado</SelectItem>
      </SelectContent>
    </Select>
  );
}