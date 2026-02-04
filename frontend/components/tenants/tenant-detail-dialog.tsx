"use client"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { 
  Mail, 
  Phone, 
  Building2, 
  Calendar, 
  DollarSign, 
  FileText,
  User,
  Briefcase,
  CreditCard,
  AlertCircle,
  Edit,
  Trash2,
  Download
} from "lucide-react"
import { TenantResponse } from "@/lib/types/api"
import { Separator } from "@/components/ui/separator"

interface TenantDetailDialogProps {
  tenant: TenantResponse & {
    property_name?: string
    property_address?: string
    rent?: number
    due_day?: number
    contract_start?: string
    contract_end?: string
  }
  open: boolean
  onOpenChange: (open: boolean) => void
  onEdit?: () => void
  onDelete?: () => void
}

const statusConfig = {
  active: { label: "Ativo", className: "bg-green-100 text-green-800" },
  inactive: { label: "Inativo", className: "bg-gray-100 text-gray-800" },
}

export function TenantDetailDialog({ tenant, open, onOpenChange, onEdit, onDelete }: TenantDetailDialogProps) {
  const getInitials = (name: string) => {
    return name
      .split(" ")
      .filter(n => n.length > 0)
      .slice(0, 2)
      .map((n) => n[0])
      .join("")
      .toUpperCase()
  }

  const formatPhone = (phone: string) => {
    const cleaned = phone.replace(/\D/g, '')
    if (cleaned.length === 11) {
      return `(${cleaned.slice(0, 2)}) ${cleaned.slice(2, 7)}-${cleaned.slice(7)}`
    } else if (cleaned.length === 10) {
      return `(${cleaned.slice(0, 2)}) ${cleaned.slice(2, 6)}-${cleaned.slice(6)}`
    }
    return phone
  }

  const formatCpfCnpj = (value: string) => {
    const cleaned = value.replace(/\D/g, '')
    if (cleaned.length === 11) {
      return `${cleaned.slice(0, 3)}.${cleaned.slice(3, 6)}.${cleaned.slice(6, 9)}-${cleaned.slice(9)}`
    } else if (cleaned.length === 14) {
      return `${cleaned.slice(0, 2)}.${cleaned.slice(2, 5)}.${cleaned.slice(5, 8)}/${cleaned.slice(8, 12)}-${cleaned.slice(12)}`
    }
    return value
  }

  const getDocumentTypeLabel = (type: string) => {
    const types: Record<string, string> = {
      rg: "RG",
      cpf: "CPF",
      cnh: "CNH",
      comprovante_residencia: "Comprovante de Residência",
      comprovante_renda: "Comprovante de Renda",
      contrato: "Contrato",
      outros: "Outros"
    }
    return types[type] || type
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Avatar className="h-16 w-16 ring-2 ring-blue-100">
                <AvatarFallback className="bg-gradient-to-br from-blue-500 to-blue-600 text-white font-semibold text-xl">
                  {getInitials(tenant.name)}
                </AvatarFallback>
              </Avatar>
              <div>
                <DialogTitle className="text-2xl">{tenant.name}</DialogTitle>
                <DialogDescription className="flex items-center gap-2 mt-1">
                  <Badge 
                    variant="secondary" 
                    className={statusConfig[tenant.status as keyof typeof statusConfig].className}
                  >
                    {statusConfig[tenant.status as keyof typeof statusConfig].label}
                  </Badge>
                </DialogDescription>
              </div>
            </div>
            <div className="flex gap-2">
              {onEdit && (
                <Button variant="outline" size="sm" onClick={onEdit}>
                  <Edit className="h-4 w-4 mr-1" />
                  Editar
                </Button>
              )}
              {onDelete && (
                <Button variant="outline" size="sm" onClick={onDelete} className="text-red-600 hover:text-red-700">
                  <Trash2 className="h-4 w-4 mr-1" />
                  Excluir
                </Button>
              )}
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6 mt-6">
          {/* Informações Pessoais */}
          <div>
            <h3 className="font-semibold text-lg mb-3 flex items-center">
              <User className="h-5 w-5 mr-2 text-blue-600" />
              Informações Pessoais
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-start space-x-3">
                <Mail className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-500">Email</p>
                  <p className="font-medium">{tenant.email}</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <Phone className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-500">Telefone</p>
                  <p className="font-medium">{formatPhone(tenant.phone)}</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <CreditCard className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-500">CPF/CNPJ</p>
                  <p className="font-medium font-mono">{formatCpfCnpj(tenant.cpf_cnpj)}</p>
                </div>
              </div>
              {tenant.birth_date && (
                <div className="flex items-start space-x-3">
                  <Calendar className="h-5 w-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-500">Data de Nascimento</p>
                    <p className="font-medium">{tenant.birth_date.split('-').reverse().join('/')}</p>
                  </div>
                </div>
              )}
              <div className="flex items-start space-x-3">
                <Briefcase className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-500">Profissão</p>
                  <p className="font-medium">{tenant.profession || 'Não informada'}</p>
                </div>
              </div>
            </div>
          </div>

          <Separator />

          {/* Contato de Emergência */}
          {tenant.emergency_contact && (
            <>
              <div>
                <h3 className="font-semibold text-lg mb-3 flex items-center">
                  <AlertCircle className="h-5 w-5 mr-2 text-orange-600" />
                  Contato de Emergência
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-start space-x-3">
                    <User className="h-5 w-5 text-gray-400 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-500">Nome</p>
                      <p className="font-medium">{tenant.emergency_contact.name}</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <Phone className="h-5 w-5 text-gray-400 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-500">Telefone</p>
                      <p className="font-medium">{formatPhone(tenant.emergency_contact.phone)}</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3 col-span-2">
                    <User className="h-5 w-5 text-gray-400 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-500">Relacionamento</p>
                      <p className="font-medium">{tenant.emergency_contact.relationship}</p>
                    </div>
                  </div>
                </div>
              </div>
              <Separator />
            </>
          )}

          {/* Informações do Imóvel e Contrato */}
          <div>
            <h3 className="font-semibold text-lg mb-3 flex items-center">
              <Building2 className="h-5 w-5 mr-2 text-blue-600" />
              Imóvel e Contrato
            </h3>
            {tenant.property_name ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-start space-x-3 col-span-2">
                  <Building2 className="h-5 w-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-500">Imóvel</p>
                    <p className="font-medium">{tenant.property_name}</p>
                    {tenant.property_address && (
                      <p className="text-sm text-gray-500 mt-1">{tenant.property_address}</p>
                    )}
                  </div>
                </div>
                {tenant.contract_start && (
                  <div className="flex items-start space-x-3">
                    <Calendar className="h-5 w-5 text-gray-400 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-500">Início do Contrato</p>
                      <p className="font-medium">{tenant.contract_start.split('-').reverse().join('/')}</p>
                    </div>
                  </div>
                )}
                {tenant.contract_end && (
                  <div className="flex items-start space-x-3">
                    <Calendar className="h-5 w-5 text-gray-400 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-500">Fim do Contrato</p>
                      <p className="font-medium">{tenant.contract_end.split('-').reverse().join('/')}</p>
                    </div>
                  </div>
                )}
                {tenant.due_day && (
                  <div className="flex items-start space-x-3">
                    <Calendar className="h-5 w-5 text-gray-400 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-500">Dia de Vencimento</p>
                      <p className="font-medium">Todo dia {tenant.due_day}</p>
                    </div>
                  </div>
                )}
                {tenant.rent && tenant.rent > 0 && (
                  <div className="flex items-start space-x-3">
                    <DollarSign className="h-5 w-5 text-green-600 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-500">Valor do Aluguel</p>
                      <p className="font-bold text-green-700 text-lg">
                        R$ {tenant.rent.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400">
                <Building2 className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>Nenhum imóvel vinculado</p>
              </div>
            )}
          </div>

          {/* Documentos */}
          {tenant.documents && tenant.documents.length > 0 && (
            <>
              <Separator />
              <div>
                <h3 className="font-semibold text-lg mb-3 flex items-center">
                  <FileText className="h-5 w-5 mr-2 text-blue-600" />
                  Documentos ({tenant.documents.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {tenant.documents.map((doc, index) => (
                    <div 
                      key={index} 
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <FileText className="h-5 w-5 text-blue-600" />
                        <div>
                          <p className="font-medium text-sm">{getDocumentTypeLabel(doc.type)}</p>
                          <p className="text-xs text-gray-500">{doc.name}</p>
                        </div>
                      </div>
                      {doc.url && (
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => window.open(doc.url, '_blank')}
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
