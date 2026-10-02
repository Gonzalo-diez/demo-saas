'use client';

import { useRouter } from 'next/navigation';
import { AlertTriangle, AlertCircle, Package, FileText } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';
import { cn } from '@/lib/utils';
import type { NotificationResponse, NotificationSeverity, NotificationCategory } from '@/features/admin/notifications/types';

type NotificationItemProps = {
  notification: NotificationResponse;
  onMarkRead?: (id: number) => void;
  onClosePopover?: () => void;
};

const ROUTE_MAP: Record<string, (id: number) => string> = {
  product: (id) => `/admin/products?id=${id}`,
  check: (id) => `/admin/checks?id=${id}`,
};

export function NotificationItem({
  notification,
  onMarkRead,
  onClosePopover,
}: NotificationItemProps) {
  const router = useRouter();

  const handleClick = () => {
    if (!notification.is_read && onMarkRead) {
      onMarkRead(notification.id);
    }

    if (notification.entity_type && notification.entity_id) {
      const getRoute = ROUTE_MAP[notification.entity_type];
      if (getRoute) {
        router.push(getRoute(notification.entity_id));
        onClosePopover?.();
      }
    }
  };

  return (
    <div
      onClick={handleClick}
      className={cn(
        'group relative flex items-start gap-3 p-3.5 text-sm transition-colors cursor-pointer hover:bg-accent/60',
        !notification.is_read && 'bg-accent/30 font-medium'
      )}
    >
      {/* Indicador visual de no leído */}
      {!notification.is_read && (
        <span className="absolute left-1.5 top-4 h-2 w-2 rounded-full bg-blue-600" />
      )}

      {/* Ícono dinámico según severidad/categoría */}
      <NotificationIcon severity={notification.severity} category={notification.category} />

      {/* Contenido principal */}
      <div className="flex-1 space-y-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-semibold leading-none truncate text-foreground">
            {notification.title}
          </span>
          <span className="text-[10px] text-muted-foreground whitespace-nowrap">
            {formatDistanceToNow(new Date(notification.notified_at), {
              addSuffix: true,
              locale: es,
            })}
          </span>
        </div>
        <p className="text-xs text-muted-foreground leading-snug line-clamp-2">
          {notification.message}
        </p>
      </div>
    </div>
  );
}

function NotificationIcon({
  severity,
  category,
}: {
  severity: NotificationSeverity;
  category: NotificationCategory;
}) {
  if (severity === 'critical') {
    return <AlertTriangle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />;
  }
  if (severity === 'warning') {
    return <AlertCircle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />;
  }
  return category === 'stock' ? (
    <Package className="h-4 w-4 text-blue-500 shrink-0 mt-0.5" />
  ) : (
    <FileText className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
  );
}