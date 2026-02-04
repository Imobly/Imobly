"use client"

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface NotificationFiltersProps {
  filters: {
    type: string
    priority: string
    read: string
    actionRequired: string
  }
  onFiltersChange: (filters: any) => void
}

export function NotificationFilters({ filters, onFiltersChange }: NotificationFiltersProps) {
  const updateFilter = (key: string, value: string) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  return (
    <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center">
      <Select value={filters.type} onValueChange={(value) => updateFilter("type", value)}>
        <SelectTrigger className="w-48">
          <SelectValue placeholder="Tipo" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todos os tipos</SelectItem>
          <SelectItem value="contract_expiring">Contratos vencendo</SelectItem>
          <SelectItem value="payment_overdue">Pagamentos atrasados</SelectItem>
          <SelectItem value="maintenance_urgent">Manutenções urgentes</SelectItem>
          <SelectItem value="system_alert">Alertas do sistema</SelectItem>
          <SelectItem value="reminder">Lembretes</SelectItem>
        </SelectContent>
      </Select>

      <Select value={filters.priority} onValueChange={(value) => updateFilter("priority", value)}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Prioridade" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todas</SelectItem>
          <SelectItem value="urgent">Urgente</SelectItem>
          <SelectItem value="high">Alta</SelectItem>
          <SelectItem value="medium">Média</SelectItem>
          <SelectItem value="low">Baixa</SelectItem>
        </SelectContent>
      </Select>

      <Select value={filters.read} onValueChange={(value) => updateFilter("read", value)}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todas</SelectItem>
          <SelectItem value="unread">Não lidas</SelectItem>
          <SelectItem value="read">Lidas</SelectItem>
        </SelectContent>
      </Select>

      <Select value={filters.actionRequired} onValueChange={(value) => updateFilter("actionRequired", value)}>
        <SelectTrigger className="w-48">
          <SelectValue placeholder="Ação necessária" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todas</SelectItem>
          <SelectItem value="required">Ação necessária</SelectItem>
          <SelectItem value="not_required">Sem ação necessária</SelectItem>
        </SelectContent>
      </Select>
    </div>
  )
}
