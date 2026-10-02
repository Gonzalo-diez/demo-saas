import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { OrderStatusBadge } from "@/features/admin/orders/components/order-status-badge";
import { UpdateOrderStatusSelect } from "@/features/admin/orders/components/update-order-status-select";
import { EditOrderDialog } from "@/features/admin/orders/components/edit-order-dialog";
import { ScheduleDeliveryDialog } from "@/features/admin/orders/components/schedule-delivery-dialog";
import type { AdminOrder } from "@/features/admin/orders/types";

type OrdersTableProps = {
  orders: AdminOrder[];
};

const IVA_CONDITION_LABELS: Record<string, string> = {
  consumidor_final: "Consumidor Final",
  responsable_inscripto: "Resp. Inscripto",
  monotributista: "Monotributista",
  exento: "Exento",
};

function formatCurrency(value: number) {
  const numericValue = Number(value);

  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  }).format(Number.isNaN(numericValue) ? 0 : numericValue);
}

function formatDate(dateStr: string | null | undefined) {
  if (!dateStr) return null;
  return new Date(dateStr + "T00:00:00").toLocaleDateString("es-AR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function OrdersTable({ orders }: OrdersTableProps) {
  if (orders.length === 0) {
    return (
      <div className="rounded-2xl border bg-background px-4 py-8 text-center text-sm text-muted-foreground shadow-sm">
        No hay órdenes para mostrar.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Mobile cards */}
      <div className="space-y-3 md:hidden">
        {orders.map((order) => (
          <div
            key={order.id}
            className="space-y-4 rounded-2xl border bg-background p-4 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <p className="font-semibold">Orden #{order.id}</p>
                  <span
                    className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${
                      order.sales_type === "B2B"
                        ? "bg-chart-4/15 text-chart-4"
                        : "bg-chart-3/15 text-chart-3"
                    }`}
                  >
                    {order.sales_type === "B2B" ? "B2B" : "Online"}
                  </span>
                  <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground">
                    {order.delivery_type === "delivery" ? "Envío" : "Retiro"}
                  </span>
                </div>
                <p className="text-sm font-medium">
                  {order.client?.name ?? order.customer_name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {order.customer_email}
                </p>
              </div>
              <OrderStatusBadge status={order.status} />
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="col-span-2 rounded-xl border p-3">
                <p className="text-xs text-muted-foreground">
                  Dirección de Entrega
                </p>
                <p className="font-medium text-xs">
                  {order.client_branch?.address ??
                    order.delivery_address ??
                    "No especificada"}
                </p>
                <p className="text-xs text-muted-foreground uppercase">
                  {order.client_branch?.city ?? order.delivery_city ?? "-"}
                </p>
              </div>

              {/* Fechas mobile */}
              <div className="rounded-xl border p-3">
                <p className="text-xs text-muted-foreground">Fecha preferida</p>
                <p className="font-medium text-xs">
                  {formatDate(order.preferred_delivery_date) ?? "—"}
                </p>
              </div>
              <div className="rounded-xl border p-3">
                <p className="text-xs text-muted-foreground">
                  Entrega programada
                </p>
                <p
                  className={`font-medium text-xs ${order.scheduled_delivery_date ? "text-brand" : "text-muted-foreground"}`}
                >
                  {formatDate(order.scheduled_delivery_date) ?? "Sin programar"}
                </p>
              </div>

              <div className="rounded-xl border p-3">
                <p className="text-xs text-muted-foreground">Vendedor</p>
                <p className="font-medium">
                  {order.sales_rep?.name ?? "Dueño"}
                </p>
              </div>
              <div className="rounded-xl border p-3">
                <p className="text-xs text-muted-foreground">Venta</p>
                <p className="font-medium">
                  {formatCurrency(order.total_amount)}
                </p>
              </div>
              <div className="rounded-xl border p-3">
                <p className="text-xs text-muted-foreground">Documento</p>
                <p className="font-medium">
                  {order.document_type === "sales_invoice"
                    ? "Remito"
                    : "Presupuesto"}
                </p>
              </div>
            </div>

            {(order.customer_dni || order.customer_tax_id) && (
              <div className="rounded-xl border p-3 text-xs space-y-1">
                <p className="text-muted-foreground font-medium">
                  Datos declarados
                </p>
                {order.customer_dni && (
                  <p>
                    DNI:{" "}
                    <span className="font-medium">{order.customer_dni}</span>
                    {order.age_confirmed && (
                      <span className="ml-2 rounded-full bg-chart-3/15 px-2 py-0.5 text-[10px] font-bold uppercase text-chart-3">
                        Mayoría de edad confirmada
                      </span>
                    )}
                  </p>
                )}
                {order.customer_tax_id && (
                  <p>
                    CUIT:{" "}
                    <span className="font-medium">{order.customer_tax_id}</span>
                    {order.customer_person_type && (
                      <span className="text-muted-foreground">
                        {" "}
                        (
                        {order.customer_person_type === "empresa"
                          ? "Empresa"
                          : "Individual"}
                        )
                      </span>
                    )}
                  </p>
                )}
                {order.customer_iva_condition && (
                  <p>
                    Condición IVA:{" "}
                    <span className="font-medium">
                      {IVA_CONDITION_LABELS[order.customer_iva_condition] ??
                        order.customer_iva_condition}
                    </span>
                  </p>
                )}
              </div>
            )}

            <div className="space-y-2">
              <p className="text-sm font-medium">Actualizar estado</p>
              <UpdateOrderStatusSelect
                orderId={order.id}
                currentStatus={order.status}
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <ScheduleDeliveryDialog order={order} />
              <EditOrderDialog order={order} />
            </div>
          </div>
        ))}
      </div>

      {/* Desktop table */}
      <div className="hidden overflow-hidden rounded-2xl border bg-background shadow-sm md:block">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[80px]">ID</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Documento</TableHead>
                <TableHead>Cliente / Email</TableHead>
                <TableHead>Datos fiscales</TableHead>
                <TableHead>Ubicación (Dirección/Ciudad)</TableHead>
                <TableHead>Vendedor</TableHead>
                <TableHead>Fecha preferida</TableHead>
                <TableHead>Entrega programada</TableHead>
                <TableHead className="text-right">Venta</TableHead>
                <TableHead className="text-right">Margen</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {orders.map((order) => {
                const displayAddress =
                  order.client_branch?.address ?? order.delivery_address ?? "-";
                const displayCity =
                  order.client_branch?.city ?? order.delivery_city ?? "-";

                return (
                  <TableRow key={order.id}>
                    <TableCell className="font-medium">#{order.id}</TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        <span
                          className={`w-fit text-[10px] font-bold uppercase px-2 py-0.5 rounded-md ${
                            order.sales_type === "B2B"
                              ? "bg-chart-4/15 text-chart-4"
                              : "bg-chart-3/15 text-chart-3"
                          }`}
                        >
                          {order.sales_type === "B2B" ? "B2B" : "Online"}
                        </span>
                        <span
                          className={`w-fit text-[10px] font-bold uppercase px-2 py-0.5 rounded-md ${
                            order.delivery_type === "delivery"
                              ? "bg-chart-3/15 text-chart-3"
                              : "bg-kraft/15 text-kraft"
                          }`}
                        >
                          {order.delivery_type === "delivery"
                            ? "Envío"
                            : "Retiro"}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span
                        className={`w-fit rounded-md px-2 py-0.5 text-[10px] font-bold uppercase ${
                          order.document_type === "sales_invoice"
                            ? "bg-chart-4/15 text-chart-4"
                            : "bg-chart-3/15 text-chart-3"
                        }`}
                      >
                        {order.document_type === "sales_invoice"
                          ? "Remito"
                          : "Presupuesto"}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium text-sm">
                          {order.client?.name ?? order.customer_name}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {order.customer_email ?? "-"}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {order.customer_dni || order.customer_tax_id ? (
                        <div className="flex flex-col gap-0.5 text-xs">
                          {order.customer_dni && (
                            <span>
                              DNI:{" "}
                              <span className="font-medium">
                                {order.customer_dni}
                              </span>
                            </span>
                          )}
                          {order.customer_tax_id && (
                            <span>
                              CUIT:{" "}
                              <span className="font-medium">
                                {order.customer_tax_id}
                              </span>
                            </span>
                          )}
                          {order.customer_iva_condition && (
                            <span className="text-muted-foreground">
                              {IVA_CONDITION_LABELS[
                                order.customer_iva_condition
                              ] ?? order.customer_iva_condition}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col max-w-[200px]">
                        <span className="truncate text-sm">
                          {displayAddress}
                        </span>
                        <span className="text-xs text-muted-foreground uppercase">
                          {displayCity}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">
                      {order.sales_rep?.name ?? "Dueño"}
                    </TableCell>

                    {/* Fecha preferida por el cliente */}
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(order.preferred_delivery_date) ?? "—"}
                    </TableCell>

                    {/* Fecha programada por el admin */}
                    <TableCell className="text-sm">
                      {order.scheduled_delivery_date ? (
                        <span className="font-medium text-brand">
                          {formatDate(order.scheduled_delivery_date)}
                        </span>
                      ) : (
                        <span className="text-muted-foreground italic">
                          Sin programar
                        </span>
                      )}
                    </TableCell>

                    <TableCell className="text-right font-medium">
                      {formatCurrency(order.total_amount)}
                    </TableCell>
                    <TableCell className="text-right text-brand font-medium">
                      {formatCurrency(order.margin_amount)}
                    </TableCell>
                    <TableCell>
                      <OrderStatusBadge status={order.status} />
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <UpdateOrderStatusSelect
                          orderId={order.id}
                          currentStatus={order.status}
                        />
                        <ScheduleDeliveryDialog order={order} />
                        <EditOrderDialog order={order} />
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}
