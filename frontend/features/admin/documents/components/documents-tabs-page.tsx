"use client";

import type { ReactNode } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { FileSignature, FileText, type LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CreatePurchaseInvoiceDialog } from "@/features/admin/purchase-invoices/components/create-purchase-invoice-dialog";
import { PurchaseInvoicesList } from "@/features/admin/purchase-invoices/components/purchase-invoices-list";
import { CreatePurchaseQuoteDialog } from "@/features/admin/purchase-quotes/components/create-purchase-quote-dialog";
import { PurchaseQuotesList } from "@/features/admin/purchase-quotes/components/purchase-quotes-list";
import { CreateSalesInvoiceDialog } from "@/features/admin/sales-invoices/components/create-sales-invoice-dialog";
import { SalesInvoicesList } from "@/features/admin/sales-invoices/components/sales-invoices-list";
import { CreateSalesQuoteDialog } from "@/features/admin/sales-quotes/components/create-sales-quote-dialog";
import { SalesQuotesList } from "@/features/admin/sales-quotes/components/sales-quotes-list";

type DocumentsKind = "sales" | "purchases";
type DocumentTab = "remitos" | "presupuestos";

type TabConfig = {
  label: string;
  description: string;
  create: ReactNode;
  list: ReactNode;
};

type KindConfig = {
  title: string;
  tabs: Record<DocumentTab, TabConfig>;
};

const DEFAULT_TAB: DocumentTab = "remitos";
const TAB_ORDER: DocumentTab[] = ["remitos", "presupuestos"];
const TAB_ICONS: Record<DocumentTab, LucideIcon> = {
  remitos: FileText,
  presupuestos: FileSignature,
};

const CONFIG: Record<DocumentsKind, KindConfig> = {
  sales: {
    title: "Ventas",
    tabs: {
      remitos: {
        label: "Remitos",
        description:
          "Registrá ventas, importá remitos y gestioná su estado.",
        create: <CreateSalesInvoiceDialog />,
        list: <SalesInvoicesList />,
      },
      presupuestos: {
        label: "Presupuestos",
        description:
          "Cotizaciones para clientes, independientes de los remitos de venta.",
        create: <CreateSalesQuoteDialog />,
        list: <SalesQuotesList />,
      },
    },
  },
  purchases: {
    title: "Compras",
    tabs: {
      remitos: {
        label: "Remitos",
        description:
          "Registrá compras, importá remitos y gestioná su estado.",
        create: <CreatePurchaseInvoiceDialog />,
        list: <PurchaseInvoicesList />,
      },
      presupuestos: {
        label: "Presupuestos",
        description:
          "Cotizaciones de proveedores, independientes de los remitos de compra.",
        create: <CreatePurchaseQuoteDialog />,
        list: <PurchaseQuotesList />,
      },
    },
  },
};

function parseTab(value: string | null): DocumentTab {
  return value === "presupuestos" ? "presupuestos" : DEFAULT_TAB;
}

/**
 * Página unificada de Ventas / Compras: un tab por tipo de documento
 * (remito | presupuesto). El tab activo vive en la URL (?tab=...) para que
 * el refresh, el botón "atrás" y los links directos mantengan la selección.
 */
export function DocumentsTabsPage({ kind }: { kind: DocumentsKind }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const config = CONFIG[kind];
  const activeTab = parseTab(searchParams.get("tab"));
  const active = config.tabs[activeTab];

  const handleTabChange = (next: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", parseTab(next));
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  };

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
            {config.title}
          </h2>
          <p className="text-sm text-muted-foreground">{active.description}</p>
        </div>

        {/* El botón de alta cambia según el tab activo */}
        <div className="w-full sm:w-auto">{active.create}</div>
      </div>

      {/* Selector Remitos | Presupuestos: 2 botones a todo el ancho en celular, compactos a la izquierda en PC */}
      <div
        role="tablist"
        aria-label={`Tipo de documento de ${config.title.toLowerCase()}`}
        className="grid grid-cols-2 gap-2 sm:inline-flex"
      >
        {TAB_ORDER.map((tab) => {
          const Icon = TAB_ICONS[tab];
          const isActive = tab === activeTab;

          return (
            <Button
              key={tab}
              type="button"
              role="tab"
              aria-selected={isActive}
              variant={isActive ? "default" : "outline"}
              onClick={() => handleTabChange(tab)}
              className="gap-2 sm:min-w-36"
            >
              <Icon className="size-4" />
              {config.tabs[tab].label}
            </Button>
          );
        })}
      </div>

      {/* Solo se monta la lista del tab activo: no se cargan las dos a la vez */}
      <div role="tabpanel">{active.list}</div>
    </div>
  );
}