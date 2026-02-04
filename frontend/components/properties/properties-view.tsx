"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Plus, Search, Filter, Grid3X3, List, AlertTriangle, RefreshCw } from "lucide-react"
import { EmptyState } from "@/components/ui/empty-state"
import { PropertyCard } from "@/components/properties/property-card"
import { PropertyList } from "@/components/properties/property-list"
import { PropertyDialog } from "@/components/properties/property-dialog"
import { PropertyFilters } from "@/components/properties/property-filters"
import { useProperties } from "@/lib/hooks/useProperties"
import { Property, convertApiToProperty, convertPropertyToApi } from "@/lib/types/property"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"

export function PropertiesView() {
  const { properties, loading, error, refetch, createProperty, updateProperty, deleteProperty } = useProperties()
  
  const [searchTerm, setSearchTerm] = useState("")
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
  const [showDialog, setShowDialog] = useState(false)
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null)
  const [confirmDeleteName, setConfirmDeleteName] = useState<string | null>(null)

  // Mostrar loading
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Imóveis</h1>
            <p className="text-gray-600">Gerencie sua carteira de imóveis</p>
          </div>
        </div>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-lg text-gray-600">Carregando propriedades...</p>
          </div>
        </div>
      </div>
    )
  }

  // Mostrar erro
  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Imóveis</h1>
            <p className="text-gray-600">Gerencie sua carteira de imóveis</p>
          </div>
        </div>
        <EmptyState
          icon={AlertTriangle}
          title="Erro ao carregar propriedades"
          description={`Não foi possível carregar as propriedades. ${error}`}
          action={{
            label: "Tentar novamente",
            onClick: refetch
          }}
          variant="error"
        />
      </div>
    )
  }

  // Converter dados da API para formato local
  const localProperties = properties.map(convertApiToProperty)

  const filteredProperties = localProperties.filter((property) => {
    const matchesSearch =
      property.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      property.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
      property.neighborhood.toLowerCase().includes(searchTerm.toLowerCase())

    return matchesSearch
  })

  const handleEdit = (property: Property) => {
    setSelectedProperty(property)
    setShowDialog(true)
  }

  const handleAdd = () => {
    setSelectedProperty(null)
    setShowDialog(true)
  }

  const handleSave = async (propertyData: Property) => {
    try {
      // Converter dados do formulário para formato da API
      const apiData = convertPropertyToApi(propertyData)
      
      console.log("💾 Salvando propriedade:", apiData)
      
      let savedProperty
      if (selectedProperty) {
        savedProperty = await updateProperty(selectedProperty.id, apiData)
        console.log("✅ Propriedade atualizada:", savedProperty)
      } else {
        savedProperty = await createProperty(apiData)
        console.log("✅ Propriedade criada:", savedProperty)
      }
      
      setShowDialog(false)
      await refetch()
      
      // Retornar a propriedade salva (convertida para formato local)
      return savedProperty ? convertApiToProperty(savedProperty) : undefined
    } catch (error) {
      console.error("❌ Erro ao salvar propriedade:", error)
      return undefined
    }
  }

  const handleDelete = async (id: number) => {
    const prop = localProperties.find(p => p.id === id)
    setConfirmDeleteId(id)
    setConfirmDeleteName(prop?.name || null)
  }

  const confirmDelete = async () => {
    if (!confirmDeleteId) return
    try {
      await deleteProperty(confirmDeleteId)
      setConfirmDeleteId(null)
      setConfirmDeleteName(null)
      toast.success("Imóvel deletado com sucesso!")
      refetch()
    } catch (error: any) {
      console.error("Erro ao deletar propriedade:", error)
      
      // Extrair mensagem de erro do backend
      const errorMessage = error?.response?.data?.detail || error?.message || "Erro ao deletar imóvel"
      
      // Verificar se é erro de contrato ativo
      if (errorMessage.includes("contrato") || errorMessage.includes("vinculado")) {
        toast.error(errorMessage, {
          duration: 5000,
          description: "Encerre ou delete os contratos antes de excluir o imóvel."
        })
      } else {
        toast.error(errorMessage)
      }
      
      // Não fechar o dialog para que o usuário veja a mensagem
      setConfirmDeleteId(null)
      setConfirmDeleteName(null)
    }
  }

  const statusCounts = {
    total: properties.length,
    occupied: properties.filter((p) => p.status === "occupied").length,
    vacant: properties.filter((p) => p.status === "vacant").length,
    maintenance: properties.filter((p) => p.status === "maintenance").length,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Imóveis</h1>
          <p className="text-gray-600">Gerencie sua carteira de imóveis</p>
        </div>
        <Button onClick={handleAdd} className="bg-blue-600 hover:bg-blue-700">
          <Plus className="mr-2 h-4 w-4" />
          Novo Imóvel
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-3 md:grid-cols-4">
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
            </div>
            <div>
              <p className="text-xs text-gray-600">Total</p>
              <p className="text-lg font-bold">{statusCounts.total}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-green-600 rounded-full"></div>
            </div>
            <div>
              <p className="text-xs text-gray-600">Ocupados</p>
              <p className="text-lg font-bold">{statusCounts.occupied}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-gray-600 rounded-full"></div>
            </div>
            <div>
              <p className="text-xs text-gray-600">Vagos</p>
              <p className="text-lg font-bold">{statusCounts.vacant}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-orange-600 rounded-full"></div>
            </div>
            <div>
              <p className="text-xs text-gray-600">Manutenção</p>
              <p className="text-lg font-bold">{statusCounts.maintenance}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4">
        <div className="flex-1 max-w-sm">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar imóveis..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>
        </div>

        <Button
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
          size="sm"
        >
          <Filter className="mr-2 h-4 w-4" />
          Filtros
        </Button>

        <div className="flex items-center border rounded-md">
          <Button
            variant={viewMode === "grid" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setViewMode("grid")}
            className="border-0"
          >
            <Grid3X3 className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === "list" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setViewMode("list")}
            className="border-0"
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <Card>
          <CardContent className="pt-6">
            <PropertyFilters />
          </CardContent>
        </Card>
      )}

      {/* Content */}
      {filteredProperties.length === 0 ? (
        <EmptyState
          icon={Plus}
          title={searchTerm ? "Nenhum imóvel encontrado" : "Nenhum imóvel cadastrado"}
          description={
            searchTerm 
              ? "Tente ajustar os filtros ou termos de busca para encontrar o que procura."
              : "Comece adicionando seu primeiro imóvel ao sistema. Você poderá gerenciar inquilinos, pagamentos e muito mais."
          }
          action={
            !searchTerm ? {
              label: "Adicionar Primeiro Imóvel",
              onClick: handleAdd
            } : undefined
          }
        />
      ) : viewMode === "grid" ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredProperties.map((property) => (
            <PropertyCard
              key={property.id}
              property={property}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      ) : (
        <PropertyList
          properties={filteredProperties}
          onEdit={handleEdit}
        />
      )}

      {/* Dialog */}
      <PropertyDialog
        open={showDialog}
        onOpenChange={setShowDialog}
        property={selectedProperty}
        onSave={handleSave}
      />

      {/* Confirm Delete Dialog */}
      <Dialog open={confirmDeleteId !== null} onOpenChange={(open) => {
        if (!open) {
          setConfirmDeleteId(null)
          setConfirmDeleteName(null)
        }
      }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Excluir imóvel</DialogTitle>
            <DialogDescription>
              Tem certeza que deseja excluir {confirmDeleteName ? `"${confirmDeleteName}"` : "este imóvel"}? Esta ação não pode ser desfeita.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setConfirmDeleteId(null)
              setConfirmDeleteName(null)
            }}>Cancelar</Button>
            <Button variant="destructive" onClick={confirmDelete}>Excluir</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}