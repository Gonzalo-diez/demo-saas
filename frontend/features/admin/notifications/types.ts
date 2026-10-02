export type NotificationCategory = 'stock' | 'check';
export type NotificationSeverity = 'info' | 'warning' | 'critical';
export type EntityType = 'product' | 'check';

export type NotificationType =
  | 'stock_near_min'
  | 'stock_low'
  | 'stock_out'
  | 'check_upcoming'
  | 'check_payable'
  | 'check_due_soon'
  | 'check_overdue'
  | 'check_rejected';

export type NotificationResponse = {
  id: number;
  category: NotificationCategory;
  type: NotificationType;
  severity: NotificationSeverity;
  title: string;
  message: string;
  entity_type: EntityType | null;
  entity_id: number | null;
  data: Record<string, unknown> | null;
  is_read: boolean;
  notified_at: string;
  resolved_at: string | null;
  created_at: string;
};

export type NotificationListResponse = {
  items: NotificationResponse[];
  total: number;
  unread_count: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type UnreadCountResponse = {
  unread_count: number;
  by_category: Partial<Record<NotificationCategory, number>>;
};

export type MarkReadResponse = {
  id: number;
  is_read: boolean;
};

export type MarkAllReadResponse = {
  marked: number;
  unread_count: number;
};

export type NotificationQueryParams = {
  page?: number;
  page_size?: number;
  category?: NotificationCategory;
  type?: NotificationType;
  unread_only?: boolean;
  include_resolved?: boolean;
};