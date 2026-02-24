"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Plus, Search, Grid3X3, List, Users, UserCheck, UserX, Edit, Trash2, RefreshCw, AlertTriangle } from "lucide-react"
import { useTenants } from "@/lib/hooks/useTenants"
import { TenantDialog } from "@/components/tenants/tenant-dialog"
import { TenantCard } from "@/components/tenants/tenant-card"
import { EmptyState } from "@/components/ui/empty-state"
import { ApiService } from "@/lib/api"
import { TenantList } from "@/components/tenants/tenant-list"
import { toast } from "sonner"

export function TenantsView() {
  const [searchTerm, setSearchTerm] = useState("")
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
  const [showDialog, setShowDialog] = useState(false)
  const [selectedTenant, setSelectedTenant] = useState<any | null>(null)
  
  const { tenants, loading, error, refetch, createTenant, updateTenant, deleteTenant } = useTenants()

  // Mostrar loading
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <div>
          <h2 className="text-xl font-semibold text-center">Carregando Inquilinos</h2>
          <p className="text-gray-500 text-center mt-2">Aguarde um momento...</p>
        </div>
      </div>
    )
  }

  // Mostrar erro
  if (error) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Erro ao carregar inquilinos"
        description={`Não foi possível carregar a lista de inquilinos. ${error}`}
        action={{
          label: "Tentar novamente",
          onClick: refetch
        }}
        variant="error"
      />
    )
  }

  const filteredTenants = tenants.filter((tenant) => {
    const matchesSearch = 
      tenant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tenant.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tenant.cpf_cnpj.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesSearch
  })

  const statusCounts = {
    total: tenants.length,
    active: tenants.filter((t) => t.status === "active").length,
    inactive: tenants.filter((t) => t.status === "inactive").length,
  }

  const handleAdd = () => {
    setSelectedTenant(null)
    setShowDialog(true)
  }

  const handleEdit = (tenant: any) => {
    setSelectedTenant(tenant)
    setShowDialog(true)
  }

  const handleSave = async (tenantData: any) => {
    try {
      console.log("💾 Salvando inquilino:", tenantData)
      console.log("📤 Payload do inquilino:", JSON.stringify(tenantData, null, 2))
      
      // Separar dados do contrato dos dados do inquilino
      const { contract, contract_id, ...tenantOnly } = tenantData
      
      console.log("📋 Dados do contrato separados:", JSON.stringify(contract, null, 2))
      console.log("👤 Dados do inquilino separados:", JSON.stringify(tenantOnly, null, 2))
      
      let savedTenant: any
      let savedContract: any = null
      
      // Validar se tem dados de contrato preenchidos
      const hasContractData = contract && contract.property_id && contract.title && contract.start_date && contract.end_date
      
      console.log("❓ Tem dados de contrato?", hasContractData)
      
      if (selectedTenant) {
        // MODO EDIÇÃO: Atualizar inquilino existente
        
        // Se tem dados de contrato, criar/atualizar
        if (hasContractData) {
          try {
            const contractData = {
              title: contract.title,
              property_id: contract.property_id,
              tenant_id: selectedTenant.id,
              start_date: contract.start_date,
              end_date: contract.end_date,
              rent: parseFloat(contract.rent.replace(/[^\d,]/g, '').replace(',', '.')) || 0,
              deposit: parseFloat(contract.deposit.replace(/[^\d,]/g, '').replace(',', '.')) || 0,
              interest_rate: parseFloat((contract.interest_rate || '').replace(',', '.')) || 0,
              fine_rate: parseFloat((contract.fine_rate || '').replace(',', '.')) || 0,
              status: contract.status || 'active',
            }
            
            if (selectedTenant.contract_id) {
              // Atualizar contrato existente
              savedContract = await ApiService.contracts.updateContract(selectedTenant.contract_id, contractData)
              console.log("✅ Contrato atualizado:", savedContract)
            } else {
              // Criar novo contrato para inquilino existente
              savedContract = await ApiService.contracts.createContract(contractData)
              console.log("✅ Contrato criado:", savedContract)
            }
          } catch (contractError: any) {
            console.error('⚠️ Erro ao salvar contrato:', contractError)
            throw new Error(`Erro ao salvar contrato: ${contractError.detail || contractError.message}`)
          }
        }
        
        // Atualizar inquilino
        const tenantPayload: any = { ...tenantOnly }
        if (savedContract?.id) {
          tenantPayload.contract_id = savedContract.id
        } else if (contract_id && typeof contract_id === 'number') {
          tenantPayload.contract_id = contract_id
        }
        
        savedTenant = await updateTenant(selectedTenant.id, tenantPayload)
        console.log("✅ Inquilino atualizado:", savedTenant)
        
      } else {
        // MODO CRIAÇÃO: Criar novo inquilino
        
        // Primeiro criar o inquilino SEM contract_id
        const tenantPayload: any = { ...tenantOnly }
        savedTenant = await createTenant(tenantPayload)
        console.log("✅ Inquilino criado:", savedTenant)
        
        // Se tem dados de contrato, criar contrato COM o tenant_id agora
        if (hasContractData && savedTenant?.id) {
          try {
            const contractData = {
              title: contract.title,
              property_id: contract.property_id,
              tenant_id: savedTenant.id, // Agora temos o ID do inquilino
              start_date: contract.start_date,
              end_date: contract.end_date,
              rent: parseFloat(contract.rent.replace(/[^\d,]/g, '').replace(',', '.')) || 0,
              deposit: parseFloat(contract.deposit.replace(/[^\d,]/g, '').replace(',', '.')) || 0,
              interest_rate: parseFloat((contract.interest_rate || '').replace(',', '.')) || 0,
              fine_rate: parseFloat((contract.fine_rate || '').replace(',', '.')) || 0,
              status: contract.status || 'active',
            }
            
            savedContract = await ApiService.contracts.createContract(contractData)
            console.log("✅ Contrato criado:", savedContract)
            
            // Atualizar inquilino com contract_id
            await updateTenant(savedTenant.id, {
              contract_id: savedContract.id
            })
            console.log("✅ Inquilino vinculado ao contrato")
          } catch (contractError: any) {
            console.error('⚠️ Erro ao criar contrato:', contractError)
            // Não falha a operação, inquilino já foi criado
            toast.error(`Inquilino criado mas erro ao criar contrato: ${contractError.detail || contractError.message}`)
          }
        }
      }
      
      setShowDialog(false)
      setSelectedTenant(null)
      await refetch()
      
      if (savedContract) {
        toast.success('Inquilino e contrato salvos com sucesso!')
      } else {
        toast.success('Inquilino salvo com sucesso!')
      }
    } catch (error: any) {
      console.error('❌ Erro ao salvar inquilino:', error)
      toast.error(`Erro ao salvar: ${error.message || 'Verifique os dados e tente novamente.'}`)
    }
  }

  const handleDelete = async (tenantId: number) => {
    if (confirm('Tem certeza que deseja deletar este inquilino?')) {
      try {
        await deleteTenant(tenantId)
        toast.success('Inquilino deletado com sucesso!')
      } catch (error: any) {
        console.error('Erro ao deletar inquilino:', error)
        
        // Extrair mensagem de erro do backend
        const errorMessage = error?.response?.data?.detail || error?.message || 'Erro ao deletar inquilino'
        
        // Verificar se é erro de contrato ativo
        if (errorMessage.includes('contrato') || errorMessage.includes('vinculado')) {
          toast.error(errorMessage, {
            duration: 5000,
            description: 'Encerre ou delete os contratos antes de excluir o inquilino.'
          })
        } else {
          toast.error(errorMessage)
        }
      }
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Inquilinos</h1>
          <p className="text-gray-600">Gerencie seus inquilinos</p>
        </div>
        <Button onClick={handleAdd} className="bg-blue-600 hover:bg-blue-700">
          <Plus className="mr-2 h-4 w-4" />
          Novo Inquilino
        </Button>
      </div>

      {/* Status Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total de Inquilinos</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statusCounts.total}</div>
            <p className="text-xs text-muted-foreground">
              Total registrado
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ativos</CardTitle>
            <UserCheck className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statusCounts.active}</div>
            <p className="text-xs text-muted-foreground">
              Inquilinos ativos
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Inativos</CardTitle>
            <UserX className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statusCounts.inactive}</div>
            <p className="text-xs text-muted-foreground">
              Inquilinos inativos
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="Buscar inquilinos..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant={viewMode === "grid" ? "default" : "outline"}
            size="sm"
            onClick={() => setViewMode("grid")}
          >
            <Grid3X3 className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === "list" ? "default" : "outline"}
            size="sm"
            onClick={() => setViewMode("list")}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="space-y-6">
        {tenants.length === 0 ? (
          <EmptyState
            icon={Users}
            title="Nenhum inquilino cadastrado"
            description="Comece adicionando seu primeiro inquilino ao sistema."
            action={{
              label: "Adicionar Primeiro Inquilino",
              onClick: handleAdd
            }}
          />
        ) : filteredTenants.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Nenhum inquilino encontrado com os filtros aplicados.</p>
          </div>
        ) : (
          viewMode === "list" ? (
            <TenantList tenants={filteredTenants as any} onEdit={handleEdit} onDelete={handleDelete} />
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredTenants.map((tenant) => (
                <TenantCard
                  key={tenant.id}
                  tenant={tenant as any}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          )
        )}
      </div>

      {/* Dialog */}
      <TenantDialog
        open={showDialog}
        onOpenChange={setShowDialog}
        tenant={selectedTenant}
        onSave={handleSave}
      />
    </div>
  )
}