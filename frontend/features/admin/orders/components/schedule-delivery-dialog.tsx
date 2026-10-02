"use client";

import { useState, Fragment } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { CalendarClock } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import {
  scheduleDeliveryDateSchema,
  type ScheduleDeliveryDateFormValues,
} from "@/features/admin/orders/schemas/order-schema";
import { useScheduleDeliveryDate } from "@/features/admin/orders/hooks/use-schedule-date-order";
import type { AdminOrder } from "@/features/admin/orders/types";

type ScheduleDeliveryDialogProps = {
  order: AdminOrder;
};

export function ScheduleDeliveryDialog({ order }: ScheduleDeliveryDialogProps) {
  const [open, setOpen] = useState(false);
  const scheduleMutation = useScheduleDeliveryDate();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ScheduleDeliveryDateFormValues>({
    resolver: zodResolver(scheduleDeliveryDateSchema),
    defaultValues: {
      scheduled_delivery_date: order.scheduled_delivery_date ?? "",
    },
  });

  function onSubmit(values: ScheduleDeliveryDateFormValues) {
    scheduleMutation.mutate(
      { orderId: order.id, scheduled_delivery_date: values.scheduled_delivery_date },
      { onSuccess: () => setOpen(false) }
    );
  }

  const today = new Date().toISOString().split("T")[0];

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <CalendarClock className="mr-2 h-3.5 w-3.5" />
          Programar entrega
        </Button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Programar fecha de entrega</DialogTitle>
          <DialogDescription>
            Orden #{order.id} ·{" "}
            {order.preferred_delivery_date ? (
              <Fragment>
                El cliente pidió recibir el{" "}
                <span className="font-medium text-foreground">
                  {new Date(order.preferred_delivery_date + "T00:00:00").toLocaleDateString(
                    "es-AR",
                    { day: "numeric", month: "long", year: "numeric" }
                  )}
                </span>
              </Fragment>
            ) : (
              "Sin fecha preferida del cliente"
            )}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="scheduled_delivery_date">Fecha de entrega programada</Label>
            <Input
              id="scheduled_delivery_date"
              type="date"
              min={today}
              {...register("scheduled_delivery_date")}
            />
            {errors.scheduled_delivery_date && (
              <p className="text-xs text-destructive">{errors.scheduled_delivery_date.message}</p>
            )}
          </div>

          {order.scheduled_delivery_date && (
            <p className="text-xs text-muted-foreground">
              Fecha actual:{" "}
              <span className="font-medium text-foreground">
                {new Date(order.scheduled_delivery_date + "T00:00:00").toLocaleDateString("es-AR", {
                  day: "numeric",
                  month: "long",
                  year: "numeric",
                })}
              </span>
            </p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={scheduleMutation.isPending}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={scheduleMutation.isPending}>
              {scheduleMutation.isPending ? "Guardando..." : "Confirmar fecha"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}