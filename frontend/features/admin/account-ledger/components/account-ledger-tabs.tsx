"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ClientSalesLedger } from "@/features/admin/account-ledger/components/client-sales-ledger";
import { SupplierPurchasesLedger } from "@/features/admin/account-ledger/components/supplier-purchases-ledger";

export function AccountLedgerTabs() {
  return (
    <Tabs defaultValue="clients">
      <TabsList>
        <TabsTrigger value="clients">Clientes</TabsTrigger>
        <TabsTrigger value="suppliers">Proveedores</TabsTrigger>
      </TabsList>

      <TabsContent value="clients">
        <ClientSalesLedger />
      </TabsContent>

      <TabsContent value="suppliers">
        <SupplierPurchasesLedger />
      </TabsContent>
    </Tabs>
  );
}