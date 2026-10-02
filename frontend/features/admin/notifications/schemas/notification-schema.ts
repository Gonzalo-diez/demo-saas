import { z } from 'zod';

// Categorías, severidades y entidades
export const notificationCategorySchema = z.enum(['stock', 'check']);

export const notificationSeveritySchema = z.enum(['info', 'warning', 'critical']);

export const entityTypeSchema = z.enum(['product', 'check']);

// Tipos exactos según NOTIFICATION_TYPE_META
export const notificationTypeSchema = z.enum([
  'stock_near_min',
  'stock_low',
  'stock_out',
  'check_upcoming',
  'check_payable',
  'check_due_soon',
  'check_overdue',
  'check_rejected',
]);

// Schema individual (NotificationResponse)
export const notificationResponseSchema = z.object({
  id: z.number(),
  category: notificationCategorySchema,
  type: notificationTypeSchema,
  severity: notificationSeveritySchema,
  title: z.string(),
  message: z.string(),
  entity_type: entityTypeSchema.nullable(),
  entity_id: z.number().nullable(),
  data: z.record(z.string(), z.unknown()).nullable(), // Clave string + valor unknown
  is_read: z.boolean(),
  notified_at: z.string(),
  resolved_at: z.string().nullable(),
  created_at: z.string(),
});

// Listado paginado (NotificationListResponse)
export const notificationListResponseSchema = z.object({
  items: z.array(notificationResponseSchema),
  total: z.number(),
  unread_count: z.number(),
  page: z.number(),
  page_size: z.number(),
  total_pages: z.number(),
});

// Contadores para la campanita (UnreadCountResponse)
export const unreadCountResponseSchema = z.object({
  unread_count: z.number(),
  by_category: z.object({
    stock: z.number().optional(),
    check: z.number().optional(),
  }), // Reemplaza el .partial() inválido
});

// Respuestas de mutaciones
export const markReadResponseSchema = z.object({
  id: z.number(),
  is_read: z.boolean(),
});

export const markAllReadResponseSchema = z.object({
  marked: z.number(),
  unread_count: z.number(),
});

// Validación para filtros / Query Params
export const notificationQueryParamsSchema = z.object({
  page: z.number().int().positive().optional(),
  page_size: z.number().int().positive().optional(),
  category: notificationCategorySchema.optional(),
  type: notificationTypeSchema.optional(),
  unread_only: z.boolean().optional(),
  include_resolved: z.boolean().optional(),
});