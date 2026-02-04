"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { MoreHorizontal, Edit, Trash2, Eye, MapPin } from "lucide-react"
import { Property } from "@/lib/types/property"
import { useTenants } from "@/lib/hooks/useTenants"

interface PropertyListProps {
  properties: Property[]
  onEdit: (property: Property) => void
}

const statusConfig = {
  occupied: { label: "Ocupado", className: "bg-green-100 text-green-800" },
  vacant: { label: "Vago", className: "bg-gray-100 text-gray-800" },
  maintenance: { label: "Manutenção", className: "bg-orange-100 text-orange-800" },
}

const typeConfig = {
  apartment: "Apartamento",
  house: "Casa",
  commercial: "Comercial",
}

export function PropertyList({ properties, onEdit }: PropertyListProps) {
  const { tenants } = useTenants()
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Imóvel</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead>Área</TableHead>
            <TableHead>Cômodos</TableHead>
            <TableHead>Inquilino</TableHead>
            <TableHead>Aluguel</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-[50px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {properties.map((property) => (
            <TableRow key={property.id}>
              <TableCell>
                <div>
                  <div className="font-medium">{property.name}</div>
                  <div className="flex items-center text-sm text-muted-foreground">
                    <MapPin className="mr-1 h-3 w-3" />
                    {property.address}, {property.neighborhood}
                  </div>
                </div>
              </TableCell>
              <TableCell>{typeConfig[property.type as keyof typeof typeConfig]}</TableCell>
              <TableCell>{property.area}m²</TableCell>
              <TableCell>
                <div className="text-sm">
                  {property.bedrooms > 0 && `${property.bedrooms} quartos, `}
                  {property.bathrooms} banheiros
                  {property.parkingSpaces > 0 && `, ${property.parkingSpaces} vagas`}
                </div>
              </TableCell>
              <TableCell>{property.tenant_id ? (tenants.find(t => t.id === property.tenant_id)?.name || `#${property.tenant_id}`) : "-"}</TableCell>
              <TableCell className="font-medium">R$ {property.rent.toLocaleString("pt-BR")}</TableCell>
              <TableCell>
                <Badge
                  variant="secondary"
                  className={statusConfig[property.status as keyof typeof statusConfig].className}
                >
                  {statusConfig[property.status as keyof typeof statusConfig].label}
                </Badge>
              </TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onEdit(property)}>
                      <Edit className="mr-2 h-4 w-4" />
                      Editar
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Eye className="mr-2 h-4 w-4" />
                      Visualizar
                    </DropdownMenuItem>
                    <DropdownMenuItem className="text-red-600">
                      <Trash2 className="mr-2 h-4 w-4" />
                      Excluir
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
