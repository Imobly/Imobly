import { apiClient, buildQueryString } from './client'
import {
  NotificationResponse,
  NotificationCreate,
  NotificationUpdate,
  NotificationFilters,
  NotificationCount,
  PaginatedNotifications,
} from '@/lib/types/api'

export class NotificationsService {
  private readonly endpoint = '/notifications'

  // Listar notificações com filtros (resposta paginada)
  async getNotifications(filters?: NotificationFilters): Promise<NotificationResponse[]> {
    const queryString = filters ? buildQueryString(filters) : ''
    const response = await apiClient.get<PaginatedNotifications | NotificationResponse[]>(
      `${this.endpoint}/${queryString}`
    )
    // Suportar tanto resposta paginada quanto array direto
    if (response && 'items' in response) {
      return response.items
    }
    return (response as NotificationResponse[]) ?? []
  }

  // Listar notificações paginadas (retorna objeto completo com total)
  async getNotificationsPaginated(filters?: NotificationFilters): Promise<PaginatedNotifications> {
    const queryString = filters ? buildQueryString(filters) : ''
    return apiClient.get<PaginatedNotifications>(`${this.endpoint}/${queryString}`)
  }

  // Obter notificação por ID
  async getNotification(id: string): Promise<NotificationResponse> {
    return apiClient.get<NotificationResponse>(`${this.endpoint}/${id}/`)
  }

  // Criar nova notificação
  async createNotification(notification: NotificationCreate): Promise<NotificationResponse> {
    return apiClient.post<NotificationResponse>(`${this.endpoint}/`, notification)
  }

  // Marcar notificação como lida
  async markAsRead(id: string): Promise<NotificationResponse> {
    return apiClient.put<NotificationResponse>(`${this.endpoint}/${id}/read/`)
  }

  // Marcar todas as notificações como lidas
  async markAllAsRead(): Promise<{ message: string }> {
    return apiClient.put<{ message: string }>(`${this.endpoint}/mark-all-read/`)
  }

  // Deletar notificação
  async deleteNotification(id: string): Promise<void> {
    return apiClient.delete<void>(`${this.endpoint}/${id}/`)
  }

  // Obter quantidade de notificações não lidas
  async getUnreadCount(): Promise<NotificationCount> {
    return apiClient.get<NotificationCount>(`${this.endpoint}/count/unread/`)
  }

  // Obter apenas notificações não lidas
  async getUnreadNotifications(): Promise<NotificationResponse[]> {
    return apiClient.get<NotificationResponse[]>(`${this.endpoint}/unread/`)
  }

  // Processar tarefas de background (atualizar status, gerar notificações)
  async processBackgroundTasks(): Promise<{
    payment_status_changes: {
      pending_to_overdue: number;
      total_overdue: number;
      total_pending: number;
      total_paid: number;
      total_partial: number;
    };
    contract_notifications: number;
    payment_reminders: number;
    overdue_notifications: number;
  }> {
    return apiClient.post(`${this.endpoint}/process-background-tasks/`)
  }

  // Limpar notificações antigas
  async cleanupOldNotifications(days: number = 30): Promise<{ message: string; deleted_count: number }> {
    return apiClient.delete<{ message: string; deleted_count: number }>(
      `${this.endpoint}/cleanup/?days=${days}`
    )
  }
}

// Instância singleton do serviço
export const notificationsService = new NotificationsService()