import { apiFetch } from '@/lib/fetcher';
import type {
  NotificationQueryParams,
  NotificationListResponse,
  UnreadCountResponse,
  MarkReadResponse,
  MarkAllReadResponse,
  NotificationCategory,
} from '@/features/admin/notifications/types';

// Helper para armar la Query String limpiando valores undefined/null
function buildQueryString(params?: Record<string, unknown>): string {
  if (!params) return '';
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
}

export const notificationsApi = {
  // GET /notifications
  getNotifications: (params?: NotificationQueryParams) => {
    const query = buildQueryString(params);
    return apiFetch<NotificationListResponse>(`/api/notifications${query}`);
  },

  // GET /notifications/unread-count
  getUnreadCount: () => {
    return apiFetch<UnreadCountResponse>('/api/notifications/unread-count');
  },

  // POST /notifications/{notification_id}/read
  markRead: (notificationId: number) => {
    return apiFetch<MarkReadResponse>(`/api/notifications/${notificationId}/read`, {
      method: 'POST',
    });
  },

  // POST /notifications/read-all
  markAllRead: (category?: NotificationCategory) => {
    const query = buildQueryString(category ? { category } : undefined);
    return apiFetch<MarkAllReadResponse>(`/api/notifications/read-all${query}`, {
      method: 'POST',
    });
  },
};