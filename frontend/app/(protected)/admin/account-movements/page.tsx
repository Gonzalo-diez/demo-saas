import { AccountLedgerTabs } from "@/features/admin/account-ledger/components/account-ledger-tabs";

export default function AccountMovementsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Cuenta corriente</h2>
        <p className="text-sm text-muted-foreground">
          Cuenta corriente al estilo planilla: clientes, proveedores (por vendedor) y ventas
          online, con productos, cantidades y formas de pago con fecha.
        </p>
      </div>

      <AccountLedgerTabs />
    </div>
  );
}