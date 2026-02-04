"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { X } from "lucide-react"

export function PaymentFilters() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Filtros</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-2">
            <Label>Status</Label>
            <Select>
              <SelectTrigger>
                <SelectValue placeholder="Todos os status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os status</SelectItem>
                <SelectItem value="paid">Pago</SelectItem>
                <SelectItem value="pending">Pendente</SelectItem>
                <SelectItem value="partial">Parcial</SelectItem>
                <SelectItem value="overdue">Atrasado</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Forma de Pagamento</Label>
            <Select>
              <SelectTrigger>
                <SelectValue placeholder="Todas as formas" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas as formas</SelectItem>
                <SelectItem value="pix">PIX</SelectItem>
                <SelectItem value="bank_transfer">Transferência</SelectItem>
                <SelectItem value="cash">Dinheiro</SelectItem>
                <SelectItem value="check">Cheque</SelectItem>
                <SelectItem value="credit_card">Cartão</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Período</Label>
            <Select>
              <SelectTrigger>
                <SelectValue placeholder="Selecionar período" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os períodos</SelectItem>
                <SelectItem value="current-month">Mês atual</SelectItem>
                <SelectItem value="last-month">Mês passado</SelectItem>
                <SelectItem value="current-year">Ano atual</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Faixa de Valor</Label>
            <div className="flex space-x-2">
              <Input placeholder="Min" type="number" />
              <Input placeholder="Max" type="number" />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between mt-4">
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary" className="flex items-center gap-1">
              Atrasado
              <X className="h-3 w-3 cursor-pointer" />
            </Badge>
            <Badge variant="secondary" className="flex items-center gap-1">
              PIX
              <X className="h-3 w-3 cursor-pointer" />
            </Badge>
          </div>

          <div className="flex space-x-2">
            <Button variant="outline" size="sm">
              Limpar Filtros
            </Button>
            <Button size="sm">Aplicar Filtros</Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
