import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationsApi } from '@/features/admin/notifications/apis/notification-api';
import type { NotificationQueryParams, NotificationCategory } from '@/features/admin/notifications/types';

// Centralización de Query Keys para la feature
export const notificationKeys = {
  all: ['notifications'] as const,
  lists: () => [...notificationKeys.all, 'list'] as const,
  list: (params?: NotificationQueryParams) => [...notificationKeys.lists(), params] as const,
  unreadCount: () => [...notificationKeys.all, 'unread-count'] as const,
};

export function useNotifications(params?: NotificationQueryParams) {
  const queryClient = useQueryClient();

  // 1. Polling liviano del contador de no leídas para el Badge
  const unreadCountQuery = useQuery({
    queryKey: notificationKeys.unreadCount(),
    queryFn: notificationsApi.getUnreadCount,
    refetchInterval: 30000, // Consulta cada 30s
  });

  // 2. Listado de notificaciones paginado / filtrado
  const listQuery = useQuery({
    queryKey: notificationKeys.list(params),
    queryFn: () => notificationsApi.getNotifications(params),
  });

  // Helper para invalidar las queries de la feature
  const invalidateNotifications = () => {
    queryClient.invalidateQueries({ queryKey: notificationKeys.all });
  };

  // 3. Mutación: Marcar una como leída
  const markReadMutation = useMutation({
    mutationFn: (id: number) => notificationsApi.markRead(id),
    onSuccess: () => {
      invalidateNotifications();
    },
  });

  // 4. Mutación: Marcar todas como leídas
  const markAllReadMutation = useMutation({
    mutationFn: (category?: NotificationCategory) => notificationsApi.markAllRead(category),
    onSuccess: () => {
      invalidateNotifications();
    },
  });

  return {
    // Listado y Paginación
    notifications: listQuery.data?.items ?? [],
    total: listQuery.data?.total ?? 0,
    page: listQuery.data?.page ?? 1,
    pageSize: listQuery.data?.page_size ?? 20,
    totalPages: listQuery.data?.total_pages ?? 1,
    isLoadingList: listQuery.isLoading,
    isFetchingList: listQuery.isFetching,
    refetchList: listQuery.refetch,

    // Contador para Badge / Campanita
    unreadCount: unreadCountQuery.data?.unread_count ?? 0,
    byCategory: unreadCountQuery.data?.by_category ?? {},
    isLoadingUnreadCount: unreadCountQuery.isLoading,

    // Mutaciones
    markRead: markReadMutation.mutate,
    markReadAsync: markReadMutation.mutateAsync,
    isMarkingRead: markReadMutation.isPending,

    markAllRead: markAllReadMutation.mutate,
    markAllReadAsync: markAllReadMutation.mutateAsync,
    isMarkingAllRead: markAllReadMutation.isPending,
  };
}