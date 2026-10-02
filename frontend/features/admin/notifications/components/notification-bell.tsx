'use client';

import { useState } from 'react';
import { Bell, CheckCheck, Inbox, Loader2 } from 'lucide-react';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useNotifications } from '@/features/admin/notifications/hooks/use-notification';
import { NotificationItem } from '@/features/admin/notifications/components/notification-item';
import type { NotificationCategory } from '@/features/admin/notifications/types';

export function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<string>('all');

  const categoryFilter = activeTab === 'all' ? undefined : (activeTab as NotificationCategory);

  const {
    notifications,
    unreadCount,
    byCategory,
    isLoadingList,
    markRead,
    markAllRead,
    isMarkingAllRead,
  } = useNotifications({
    category: categoryFilter,
    page_size: 15,
  });

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5 text-yellow-500 fill-yellow-500 transition-colors hover:text-yellow-600 hover:fill-yellow-600" />
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 h-5 min-w-5 rounded-full p-0 flex items-center justify-center text-[10px] font-bold border-2 border-background"
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent align="end" className="w-80 p-0 sm:w-96">
        {/* Header del Popover */}
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-sm">Notificaciones</h4>
            {unreadCount > 0 && (
              <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                {unreadCount} nuevas
              </Badge>
            )}
          </div>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              disabled={isMarkingAllRead}
              onClick={() => markAllRead(categoryFilter)}
              className="text-xs h-auto p-1 text-muted-foreground hover:text-primary"
            >
              {isMarkingAllRead ? (
                <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
              ) : (
                <CheckCheck className="mr-1 h-3.5 w-3.5" />
              )}
              Marcar leídas
            </Button>
          )}
        </div>

        {/* Filtros por pestaña */}
        <div className="px-3 pt-2.5">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3 h-8">
              <TabsTrigger value="all" className="text-xs">
                Todas
              </TabsTrigger>
              <TabsTrigger value="stock" className="text-xs">
                Stock {byCategory.stock ? `(${byCategory.stock})` : ''}
              </TabsTrigger>
              <TabsTrigger value="check" className="text-xs">
                Cheques {byCategory.check ? `(${byCategory.check})` : ''}
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {/* Lista de avisos */}
        <ScrollArea className="h-80 mt-1">
          {isLoadingList ? (
            <div className="flex h-40 items-center justify-center text-muted-foreground">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 gap-2 text-muted-foreground p-6 text-center">
              <Inbox className="h-8 w-8 stroke-[1.5]" />
              <p className="text-xs">No hay avisos pendientes en esta categoría</p>
            </div>
          ) : (
            <div className="divide-y divide-border/50">
              {notifications.map((item) => (
                <NotificationItem
                  key={item.id}
                  notification={item}
                  onMarkRead={markRead}
                  onClosePopover={() => setIsOpen(false)}
                />
              ))}
            </div>
          )}
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}