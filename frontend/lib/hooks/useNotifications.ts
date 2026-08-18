import useSWR from 'swr'
import { ApiService, handleApiError } from '@/lib/api'
import { NotificationResponse, NotificationFilters, PaginatedNotifications } from '@/lib/types/api'

// Cache key builder
const NOTIFICATIONS_KEY = '/notifications'
const getNotificationsKey = (filters?: NotificationFilters) => {
  const filterStr = filters ? JSON.stringify(filters) : ''
  return filterStr ? `${NOTIFICATIONS_KEY}?${filterStr}` : NOTIFICATIONS_KEY
}

interface UseNotificationsReturn {
  notifications: NotificationResponse[]
  totalCount: number
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  createNotification: (notification: any) => Promise<NotificationResponse | null>
  markAsRead: (id: string) => Promise<boolean>
  markAllAsRead: () => Promise<boolean>
  deleteNotification: (id: string) => Promise<boolean>
}

export function useNotifications(filters?: NotificationFilters): UseNotificationsReturn {
  const key = getNotificationsKey(filters)

  const { data, error: swrError, isLoading, mutate } = useSWR<PaginatedNotifications>(
    key,
    async () => {
      // Tenta buscar como paginado; fallback para array direto
      const response = await ApiService.notifications.getNotificationsPaginated(filters)
      if (response && 'items' in response) {
        return response
      }
      // Fallback: backend retornou array direto
      const items = (response as unknown as NotificationResponse[]) ?? []
      return { items, total: items.length, skip: 0, limit: items.length }
    },
  )

  const createNotification = async (notification: any): Promise<NotificationResponse | null> => {
    try {
      const newNotification = await ApiService.notifications.createNotification(notification)
      await mutate()
      return newNotification
    } catch (err) {
      console.error('Erro ao criar notificação:', err)
      return null
    }
  }

  const markAsRead = async (id: string): Promise<boolean> => {
    try {
      await ApiService.notifications.markAsRead(id)
      // Otimistic update: marcar como lida localmente
      await mutate(
        (current) => current ? {
          ...current,
          items: current.items.map(n => n.id === id ? { ...n, read_status: true } : n),
        } : current,
        { revalidate: false }
      )
      return true
    } catch (err) {
      console.error('Erro ao marcar notificação como lida:', err)
      return false
    }
  }

  const markAllAsRead = async (): Promise<boolean> => {
    try {
      await ApiService.notifications.markAllAsRead()
      // Otimistic update: marcar todas como lidas
      await mutate(
        (current) => current ? {
          ...current,
          items: current.items.map(n => ({ ...n, read_status: true })),
        } : current,
        { revalidate: false }
      )
      return true
    } catch (err) {
      console.error('Erro ao marcar todas como lidas:', err)
      return false
    }
  }

  const deleteNotification = async (id: string): Promise<boolean> => {
    try {
      await ApiService.notifications.deleteNotification(id)
      // Otimistic update: remover da lista localmente
      await mutate(
        (current) => current ? {
          ...current,
          items: current.items.filter(n => n.id !== id),
          total: current.total - 1,
        } : current,
        { revalidate: false }
      )
      return true
    } catch (err) {
      console.error('Erro ao deletar notificação:', err)
      return false
    }
  }

  return {
    notifications: data?.items ?? [],
    totalCount: data?.total ?? 0,
    loading: isLoading,
    error: swrError ? handleApiError(swrError) : null,
    refetch: async () => { await mutate() },
    createNotification,
    markAsRead,
    markAllAsRead,
    deleteNotification,
  }
}

// Hook para contagem de notificações não lidas
export function useUnreadNotificationsCount() {
  const { data, error: swrError, isLoading } = useSWR<{ unread_count: number }>(
    `${NOTIFICATIONS_KEY}/unread-count`,
    () => ApiService.notifications.getUnreadCount(),
  )

  return {
    unreadCount: data?.unread_count ?? 0,
    loading: isLoading,
    error: swrError ? handleApiError(swrError) : null,
  }
}