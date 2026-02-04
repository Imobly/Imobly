"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Bell, Search, CheckCircle, AlertTriangle, Info, Clock, Trash2 } from "lucide-react"
import { useNotifications } from "@/lib/hooks/useNotifications"

export function NotificationsView() {
  const [searchTerm, setSearchTerm] = useState("")
  
  const { notifications, loading, error, refetch, markAsRead, markAllAsRead, deleteNotification } = useNotifications()

  // Mostrar loading
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg">Carregando notificações...</div>
      </div>
    )
  }

  // Mostrar erro
  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-red-500">Erro: {error}</div>
      </div>
    )
  }

  const filteredNotifications = notifications.filter((notification) => {
    const matchesSearch = 
      notification.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      notification.message.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesSearch
  })

  const statusCounts = {
    total: notifications.length,
    unread: notifications.filter((n) => !n.read_status).length,
    urgent: notifications.filter((n) => n.priority === "urgent").length,
    actionRequired: notifications.filter((n) => n.action_required).length,
  }

  const handleMarkAsRead = async (notificationId: string) => {
    await markAsRead(notificationId)
  }

  const handleMarkAllAsRead = async () => {
    await markAllAsRead()
  }

  const handleDelete = async (notificationId: string) => {
    if (confirm('Tem certeza que deseja deletar esta notificação?')) {
      await deleteNotification(notificationId)
    }
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'contract_expiring':
        return <Clock className="h-4 w-4 text-orange-500" />
      case 'payment_overdue':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case 'maintenance_urgent':
        return <AlertTriangle className="h-4 w-4 text-red-600" />
      case 'system_alert':
        return <Info className="h-4 w-4 text-blue-500" />
      default:
        return <Bell className="h-4 w-4 text-gray-500" />
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'border-l-red-500 bg-red-50'
      case 'high':
        return 'border-l-orange-500 bg-orange-50'
      case 'medium':
        return 'border-l-yellow-500 bg-yellow-50'
      default:
        return 'border-l-blue-500 bg-blue-50'
    }
  }

  return (
    <div className="space-y-6">
      {/* Action Button */}
      <div className="flex justify-end">
        <Button onClick={handleMarkAllAsRead} variant="outline">
          <CheckCircle className="mr-2 h-4 w-4" />
          Marcar Todas como Lidas
        </Button>
      </div>

      {/* Status Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total</CardTitle>
            <Bell className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statusCounts.total}</div>
            <p className="text-xs text-muted-foreground">
              Notificações no total
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Não Lidas</CardTitle>
            <div className="h-4 w-4 rounded-full bg-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statusCounts.unread}</div>
            <p className="text-xs text-muted-foreground">
              Precisam de atenção
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Urgentes</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statusCounts.urgent}</div>
            <p className="text-xs text-red-600">
              Ação imediata
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Requer Ação</CardTitle>
            <Clock className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statusCounts.actionRequired}</div>
            <p className="text-xs text-muted-foreground">
              Ações pendentes
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="Buscar notificações..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Content */}
      <div className="space-y-4">
        {filteredNotifications.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Nenhuma notificação encontrada.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredNotifications.map((notification) => (
              <Card 
                key={notification.id} 
                className={`border-l-4 ${getPriorityColor(notification.priority)} ${
                  !notification.read_status ? 'ring-2 ring-blue-100' : ''
                }`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex gap-3 flex-1">
                      {getNotificationIcon(notification.type)}
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className={`font-medium ${!notification.read_status ? 'font-semibold' : ''}`}>
                            {notification.title}
                          </h3>
                          {!notification.read_status && (
                            <span className="h-2 w-2 bg-blue-500 rounded-full"></span>
                          )}
                          {notification.action_required && (
                            <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded">
                              Ação Necessária
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-700 mb-2">
                          {notification.message}
                        </p>
                        <div className="flex items-center gap-4 text-xs text-gray-500">
                          <span>
                            {new Date(notification.date).toLocaleString('pt-BR')}
                          </span>
                          <span className="capitalize">
                            Prioridade: {notification.priority === 'urgent' ? 'Urgente' :
                                      notification.priority === 'high' ? 'Alta' :
                                      notification.priority === 'medium' ? 'Média' : 'Baixa'}
                          </span>
                          <span className="capitalize">
                            Tipo: {notification.type.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2 ml-4">
                      {!notification.read_status && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleMarkAsRead(notification.id)}
                          className="text-blue-600 hover:text-blue-700"
                        >
                          <CheckCircle className="h-4 w-4" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(notification.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}