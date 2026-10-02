import type { AccountMovementEntityType } from "@/features/admin/account-movements/types";

/**
 * Textos por tipo de entidad para las tarjetas de métricas de cuenta
 * corriente (resumen, antigüedad, ranking, evolución). Centralizado acá
 * para no repetir ternarios "client vs. supplier" en cada componente.
 */
type AccountEntityLabels = {
  /** "clientes" | "proveedores" */
  pluralLower: string;
  /** "un cliente" | "un proveedor" */
  singularWithArticle: string;
  /** Título de la tarjeta de deuda total */
  totalDebtTitle: string;
  /** Título de la tarjeta de saldo a favor */
  totalFavorTitle: string;
  /** Descripción de "balance neto" */
  netBalanceDescription: string;
  /** Título de la tarjeta de conteo de entidades con saldo */
  countTitle: string;
  /** Título del ranking en modo deudores */
  rankingDebtorsTitle: string;
  /** Título del ranking en modo a favor */
  rankingFavorTitle: string;
  /** Título del gráfico de antigüedad de deuda */
  agingTitle: string;
  /** Mensaje cuando no hay deuda pendiente */
  agingEmptyMessage: string;
  /** Placeholder del select de entidad */
  selectPlaceholder: string;
  /** Mensaje cuando no hay entidades para elegir */
  selectEmptyMessage: string;
};

const LABELS: Record<AccountMovementEntityType, AccountEntityLabels> = {
  client: {
    pluralLower: "clientes",
    singularWithArticle: "un cliente",
    totalDebtTitle: "Total adeudado por clientes",
    totalFavorTitle: "Saldo a favor de clientes",
    netBalanceDescription: "Deuda total menos saldos a favor de clientes.",
    countTitle: "Clientes con cuenta corriente",
    rankingDebtorsTitle: "Mayores deudores",
    rankingFavorTitle: "Mayores saldos a favor",
    agingTitle: "Antigüedad de deuda de clientes",
    agingEmptyMessage: "No hay remitos de venta pendientes de cobro.",
    selectPlaceholder: "Elegí un cliente...",
    selectEmptyMessage: "No hay clientes activos.",
  },
  supplier: {
    pluralLower: "proveedores",
    singularWithArticle: "un proveedor",
    totalDebtTitle: "Total que debemos a proveedores",
    totalFavorTitle: "Saldo a nuestro favor",
    netBalanceDescription: "Deuda total menos saldos a nuestro favor.",
    countTitle: "Proveedores con cuenta corriente",
    rankingDebtorsTitle: "A quiénes más les debemos",
    rankingFavorTitle: "Mayor saldo a nuestro favor",
    agingTitle: "Antigüedad de deuda con proveedores",
    agingEmptyMessage: "No hay remitos de compra pendientes de pago.",
    selectPlaceholder: "Elegí un proveedor...",
    selectEmptyMessage: "No hay proveedores activos.",
  },
};

export function getAccountEntityLabels(
  entityType: AccountMovementEntityType
): AccountEntityLabels {
  return LABELS[entityType];
}