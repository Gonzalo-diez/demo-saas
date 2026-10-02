import { ChecksList } from "@/features/admin/checks/components/checks-list";
import { RegisterIssuedCheckDialog } from "@/features/admin/checks/components/register-issued-check-dialog";
import { RegisterReceivedCheckDialog } from "@/features/admin/checks/components/register-received-check-dialog";

export default function ChecksPage() {
  return (
    <div className="space-y-6 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">Cheques</h2>
          <p className="text-sm text-muted-foreground">
            Cheques recibidos de clientes y emitidos a proveedores. Quedan pendientes hasta que se
            depositan y acreditan.
          </p>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:w-auto">
          <RegisterReceivedCheckDialog />
          <RegisterIssuedCheckDialog />
        </div>
      </div>

      <ChecksList />
    </div>
  );
}
