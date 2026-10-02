import { z } from "zod";

const baseCheckFields = {
  check_number: z
    .string()
    .trim()
    .min(1, "El número de cheque es obligatorio")
    .max(50, "Máximo 50 caracteres"),
  bank_name: z.string().trim().max(100).optional().or(z.literal("")),
  drawer_name: z.string().trim().max(255).optional().or(z.literal("")),
  amount: z.coerce.number().positive("El monto debe ser mayor a 0"),
  issue_date: z.string().min(1, "La fecha de emisión es obligatoria"),
  payment_date: z.string().min(1, "La fecha de pago es obligatoria"),
  due_date: z.string().min(1, "La fecha de vencimiento es obligatoria"),
  notes: z.string().trim().max(1000).optional().or(z.literal("")),
};

const allocationFields = {
  allocate: z.boolean().optional(),
  allocation_document_type: z.enum(["sales_invoice", "sales_quote"]).optional(),
  allocation_invoice_id: z.coerce.number().int().positive().optional(),
  allocation_amount: z.coerce.number().positive().optional(),
};

const issuedAllocationFields = {
  allocate: z.boolean().optional(),
  allocation_invoice_id: z.coerce.number().int().positive().optional(),
  allocation_amount: z.coerce.number().positive().optional(),
};

export const registerReceivedCheckSchema = z
  .object({
    client_id: z.coerce.number().int().positive("Seleccioná un cliente"),
    ...baseCheckFields,
    ...allocationFields,
  })
  .refine((data) => data.payment_date >= data.issue_date, {
    message: "La fecha de pago no puede ser anterior a la de emisión",
    path: ["payment_date"],
  })
  .refine((data) => data.due_date >= data.payment_date, {
    message: "El vencimiento no puede ser anterior a la fecha de pago",
    path: ["due_date"],
  })
  .refine(
    (data) => !data.allocate || (!!data.allocation_document_type && !!data.allocation_invoice_id && !!data.allocation_amount),
    {
      message: "Completá tipo de documento, número y monto para imputar el cheque",
      path: ["allocation_invoice_id"],
    }
  )
  .refine((data) => !data.allocate || (data.allocation_amount ?? 0) <= data.amount, {
    message: "El monto imputado no puede superar el monto del cheque",
    path: ["allocation_amount"],
  });

export const registerIssuedCheckSchema = z
  .object({
    supplier_id: z.coerce.number().int().positive("Seleccioná un proveedor"),
    ...baseCheckFields,
    ...issuedAllocationFields,
  })
  .refine((data) => data.payment_date >= data.issue_date, {
    message: "La fecha de pago no puede ser anterior a la de emisión",
    path: ["payment_date"],
  })
  .refine((data) => data.due_date >= data.payment_date, {
    message: "El vencimiento no puede ser anterior a la fecha de pago",
    path: ["due_date"],
  })
  .refine((data) => !data.allocate || (!!data.allocation_invoice_id && !!data.allocation_amount), {
    message: "Completá número de remito y monto para imputar el cheque",
    path: ["allocation_invoice_id"],
  })
  .refine((data) => !data.allocate || (data.allocation_amount ?? 0) <= data.amount, {
    message: "El monto imputado no puede superar el monto del cheque",
    path: ["allocation_amount"],
  });

export const rejectCheckSchema = z.object({
  notes: z.string().trim().max(1000).optional().or(z.literal("")),
});

export type RegisterReceivedCheckFormInput = z.input<typeof registerReceivedCheckSchema>;
export type RegisterReceivedCheckFormValues = z.output<typeof registerReceivedCheckSchema>;
export type RegisterIssuedCheckFormInput = z.input<typeof registerIssuedCheckSchema>;
export type RegisterIssuedCheckFormValues = z.output<typeof registerIssuedCheckSchema>;
export type RejectCheckFormValues = z.output<typeof rejectCheckSchema>;