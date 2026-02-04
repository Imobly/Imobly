"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { MoreHorizontal, Edit, Trash2, Eye, Building2 } from "lucide-react"

interface Tenant {
  id: number
  name: string
  email: string
  phone: string
  cpfCnpj: string
  profession: string
  property: {
    id: number
    name: string
    address: string
  } | null
  contractStart: string | null
  rent: number
  status: string
}

interface TenantListProps {
  tenants: Tenant[]
  onEdit: (tenant: Tenant) => void
  onDelete?: (id: number) => void
}

const statusConfig = {
  active: { label: "Ativo", className: "bg-green-100 text-green-800" },
  inactive: { label: "Inativo", className: "bg-gray-100 text-gray-800" },
}

export function TenantList({ tenants, onEdit, onDelete }: TenantListProps) {
  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Inquilino</TableHead>
            <TableHead>Contato</TableHead>
            <TableHead>CPF/CNPJ</TableHead>
            <TableHead>Imóvel</TableHead>
            <TableHead>Aluguel</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-[50px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tenants.map((tenant) => (
            <TableRow key={tenant.id}>
              <TableCell>
                <div className="flex items-center space-x-3">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                      {getInitials(tenant.name)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="font-medium">{tenant.name}</div>
                    <div className="text-sm text-muted-foreground">{tenant.profession}</div>
                  </div>
                </div>
              </TableCell>
              <TableCell>
                <div className="text-sm">
                  <div>{tenant.email}</div>
                  <div className="text-muted-foreground">{tenant.phone}</div>
                </div>
              </TableCell>
              <TableCell className="font-mono text-sm">{tenant.cpfCnpj}</TableCell>
              <TableCell>
                {tenant.property ? (
                  <div className="flex items-center space-x-2">
                    <Building2 className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <div className="font-medium text-sm">{tenant.property.name}</div>
                      <div className="text-xs text-muted-foreground">{tenant.property.address}</div>
                    </div>
                  </div>
                ) : (
                  <span className="text-muted-foreground text-sm">-</span>
                )}
              </TableCell>
              <TableCell>
                {tenant.rent > 0 ? (
                  <span className="font-medium">R$ {tenant.rent.toLocaleString("pt-BR")}</span>
                ) : (
                  <span className="text-muted-foreground">-</span>
                )}
              </TableCell>
              <TableCell>
                <Badge
                  variant="secondary"
                  className={statusConfig[tenant.status as keyof typeof statusConfig].className}
                >
                  {statusConfig[tenant.status as keyof typeof statusConfig].label}
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
                    <DropdownMenuItem onClick={() => onEdit(tenant)}>
                      <Edit className="mr-2 h-4 w-4" />
                      Editar
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Eye className="mr-2 h-4 w-4" />
                      Visualizar
                    </DropdownMenuItem>
                    <DropdownMenuItem className="text-red-600" onClick={() => onDelete && onDelete(tenant.id)}>
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
