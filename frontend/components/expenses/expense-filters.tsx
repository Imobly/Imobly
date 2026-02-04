"use client"

import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search } from "lucide-react"

interface ExpenseFiltersProps {
  filters: {
    search: string
    type: string
    category: string
    status: string
    property: string
    dateRange: string
  }
  onFiltersChange: (filters: any) => void
}

export function ExpenseFilters({ filters, onFiltersChange }: ExpenseFiltersProps) {
  const updateFilter = (key: string, value: string) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  return (
    <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
        <Input
          placeholder="Buscar despesas..."
          value={filters.search}
          onChange={(e) => updateFilter("search", e.target.value)}
          className="pl-10 w-64"
        />
      </div>

      <Select value={filters.type} onValueChange={(value) => updateFilter("type", value)}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Tipo" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todos os tipos</SelectItem>
          <SelectItem value="expense">Despesas</SelectItem>
          <SelectItem value="maintenance">Manutenções</SelectItem>
        </SelectContent>
      </Select>

      <Select value={filters.status} onValueChange={(value) => updateFilter("status", value)}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todos os status</SelectItem>
          <SelectItem value="pending">Pendente</SelectItem>
          <SelectItem value="paid">Pago</SelectItem>
          <SelectItem value="scheduled">Agendado</SelectItem>
        </SelectContent>
      </Select>

      <Select value={filters.property} onValueChange={(value) => updateFilter("property", value)}>
        <SelectTrigger className="w-48">
          <SelectValue placeholder="Imóvel" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todos os imóveis</SelectItem>
          <SelectItem value="Apartamento Centro - Apt 101">Apartamento Centro - Apt 101</SelectItem>
          <SelectItem value="Apartamento Centro - Apt 205">Apartamento Centro - Apt 205</SelectItem>
          <SelectItem value="Casa Jardins">Casa Jardins</SelectItem>
          <SelectItem value="Loja Comercial - Centro">Loja Comercial - Centro</SelectItem>
        </SelectContent>
      </Select>

      <Select value={filters.dateRange} onValueChange={(value) => updateFilter("dateRange", value)}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Período" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todo período</SelectItem>
          <SelectItem value="today">Hoje</SelectItem>
          <SelectItem value="week">Esta semana</SelectItem>
          <SelectItem value="month">Este mês</SelectItem>
          <SelectItem value="quarter">Este trimestre</SelectItem>
          <SelectItem value="year">Este ano</SelectItem>
        </SelectContent>
      </Select>
    </div>
  )
}
