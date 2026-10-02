import { CreateClientDialog } from "@/features/admin/clients/components/create-client-dialog";
import { ClientsList } from "@/features/admin/clients/components/clients-list";

export default function ClientsPage() {
  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Clientes</h2>
          <p className="text-sm text-muted-foreground">
            Gestión de clientes del sistema.
          </p>
        </div>
        
        <CreateClientDialog />
      </div>

      <ClientsList />
    </div>
  );
}