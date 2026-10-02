import { z } from "zod";

// ---------------- Bloques comunes ----------------

export const ledgerPaymentEntrySchema = z.object({
  id: z.number(),
  method: z.string(),
  amount: z.string(),
  date: z.string(),
});

export const ledgerPaymentFormSchema = z.object({
  amount: z.coerce
    .number({ message: "Ingresá un monto válido" })
    .positive("El monto debe ser mayor a 0"),
  method: z.enum(["efectivo", "debito", "credito", "cheque", "otro"], {
    message: "Seleccioná un método de pago",
  }),
  date: z.string().optional().or(z.literal("")),
  notes: z.string().max(1000, "Máximo 1000 caracteres").optional().or(z.literal("")),
});

export type LedgerPaymentFormValues = z.infer<typeof ledgerPaymentFormSchema>;

export const ledgerProductLineSchema = z.object({
  product_id: z.number().nullable(),
  product_name: z.string(),
  quantity: z.number(),
  stock_current: z.number().nullable(),
});

export const salesRepSummarySchema = z.object({
  id: z.number(),
  name: z.string(),
});

// ---------------- Proveedores ----------------

export const supplierPurchaseRowSchema = z.object({
  id: z.number(),
  document_type: z.enum(["purchase_invoice", "purchase_quote"]),
  document_number: z.string(),
  purchase_date: z.string(),
  supplier_id: z.number().nullable(),
  supplier_name: z.string(),
  products: z.array(ledgerProductLineSchema),
  total_quantity: z.number(),
  total_amount: z.string().nullable(),
  payments: z.array(ledgerPaymentEntrySchema),
  paid_amount: z.string(),
  balance: z.string(),
  payment_status: z.string(),
});

export const supplierPurchasesGroupSchema = z.object({
  sales_rep: salesRepSummarySchema.nullable(),
  rows: z.array(supplierPurchaseRowSchema),
  total: z.number(),
});

export const supplierPurchasesLedgerResponseSchema = z.object({
  groups: z.array(supplierPurchasesGroupSchema),
});

// ---------------- Clientes ----------------

export const clientSaleRowSchema = z.object({
  id: z.number(),
  document_type: z.enum(["sales_invoice", "sales_quote"]),
  document_number: z.string(),
  sale_date: z.string(),
  client_id: z.number().nullable(),
  client_name: z.string(),
  sales_type: z.string().optional().nullable(),
  products: z.array(ledgerProductLineSchema),
  total_quantity: z.number(),
  total_amount: z.string().nullable(),
  payments: z.array(ledgerPaymentEntrySchema),
  paid_amount: z.string(),
  balance: z.string(),
  payment_status: z.string(),
});

export const clientSalesLedgerResponseSchema = z.object({
  items: z.array(clientSaleRowSchema),
  total: z.number(),
  page: z.number(),
  page_size: z.number(),
  total_pages: z.number(),
});

export const clientSalesSummaryGroupSchema = z.object({
  sales_rep: salesRepSummarySchema.nullable(),
  total: z.number(),
});

export const clientSalesSummaryResponseSchema = z.object({
  groups: z.array(clientSalesSummaryGroupSchema),
  total_all: z.number(),
});

// ---------------- Filtro de fechas (los tabs) ----------------

export const ledgerDateRangeFilterSchema = z
  .object({
    date_from: z.string().optional().or(z.literal("")),
    date_to: z.string().optional().or(z.literal("")),
  })
  .refine(
    (data) => {
      if (!data.date_from || !data.date_to) return true;
      return new Date(data.date_from) <= new Date(data.date_to);
    },
    {
      message: "La fecha 'desde' no puede ser posterior a la fecha 'hasta'",
      path: ["date_to"],
    }
  );

export type LedgerDateRangeFilterValues = z.infer<typeof ledgerDateRangeFilterSchema>;