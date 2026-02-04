"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { X } from "lucide-react"

export function PropertyFilters() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Filtros</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-2">
            <Label>Tipo</Label>
            <Select>
              <SelectTrigger>
                <SelectValue placeholder="Todos os tipos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os tipos</SelectItem>
                <SelectItem value="apartment">Apartamento</SelectItem>
                <SelectItem value="house">Casa</SelectItem>
                <SelectItem value="commercial">Comercial</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Status</Label>
            <Select>
              <SelectTrigger>
                <SelectValue placeholder="Todos os status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os status</SelectItem>
                <SelectItem value="occupied">Ocupado</SelectItem>
                <SelectItem value="vacant">Vago</SelectItem>
                <SelectItem value="maintenance">Manutenção</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Bairro</Label>
            <Select>
              <SelectTrigger>
                <SelectValue placeholder="Todos os bairros" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os bairros</SelectItem>
                <SelectItem value="centro">Centro</SelectItem>
                <SelectItem value="jardins">Jardins</SelectItem>
                <SelectItem value="vila-nova">Vila Nova</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Faixa de Aluguel</Label>
            <div className="flex space-x-2">
              <Input placeholder="Min" type="number" />
              <Input placeholder="Max" type="number" />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between mt-4">
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary" className="flex items-center gap-1">
              Apartamento
              <X className="h-3 w-3 cursor-pointer" />
            </Badge>
            <Badge variant="secondary" className="flex items-center gap-1">
              Centro
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
