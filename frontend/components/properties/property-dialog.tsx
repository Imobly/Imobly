"use client"

import type React from "react"

import { useState, useEffect } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Upload, X, Plus, Edit, Building, Loader2 } from "lucide-react"
import { Property } from "@/lib/types/property"
import { useTenants } from "@/lib/hooks/useTenants"
import { integerMask, currencyMask, currencyUnmask, areaMask, cepMask } from "@/lib/utils/masks"
import { propertiesService } from "@/lib/api/properties"
import { toast } from "sonner"

interface Unit {
  id: string
  number: string
  area: number
  bedrooms: number
  bathrooms: number
  rent: number
  status: 'vacant' | 'occupied' | 'maintenance'
  tenant?: string
}

interface PropertyDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  property?: Property | null
  onSave: (property: Property) => Promise<Property | undefined>
}

const initialProperty: Property = {
  name: "",
  address: "",
  neighborhood: "",
  city: "",
  state: "",
  zipCode: "",
  type: "apartment",
  area: "" as any,
  bedrooms: "" as any,
  bathrooms: "" as any,
  parkingSpaces: "" as any,
  rent: "" as any,
  status: "vacant",
  description: "",
  images: [],
  units: [],
  isResidential: false,
  tenant_id: null,
}

export function PropertyDialog({ open, onOpenChange, property, onSave }: PropertyDialogProps) {
  const [formData, setFormData] = useState<Property>(initialProperty)
  const [isLoading, setIsLoading] = useState(false)
  const [showUnitDialog, setShowUnitDialog] = useState(false)
  const [editingUnit, setEditingUnit] = useState<Unit | null>(null)
  const [uploadingImages, setUploadingImages] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [dragActive, setDragActive] = useState(false)
  const { tenants } = useTenants()

  useEffect(() => {
    if (property) {
      setFormData(property)
    } else {
      setFormData(initialProperty)
    }
  }, [property])

  const validateForm = (): boolean => {
    // Validar campos obrigatórios conforme backend PropertyBase
    if (!formData.name || formData.name.trim() === '') {
      toast.error('Nome do imóvel é obrigatório')
      return false
    }
    if (!formData.address || formData.address.trim() === '') {
      toast.error('Endereço é obrigatório')
      return false
    }
    if (!formData.neighborhood || formData.neighborhood.trim() === '') {
      toast.error('Bairro é obrigatório')
      return false
    }
    if (!formData.city || formData.city.trim() === '') {
      toast.error('Cidade é obrigatória')
      return false
    }
    if (!formData.state || formData.state.trim() === '') {
      toast.error('Estado é obrigatório')
      return false
    }
    if (!formData.zipCode || formData.zipCode.trim() === '') {
      toast.error('CEP é obrigatório')
      return false
    }
    if (!formData.type) {
      toast.error('Tipo do imóvel é obrigatório')
      return false
    }
    
    // Validar valores numéricos
    const area = typeof formData.area === 'string' ? parseFloat(formData.area) : formData.area
    if (!area || area <= 0) {
      toast.error('Área deve ser maior que zero')
      return false
    }
    
    const bedrooms = typeof formData.bedrooms === 'string' ? parseInt(formData.bedrooms) : formData.bedrooms
    if (bedrooms === undefined || bedrooms === null || bedrooms < 0) {
      toast.error('Número de quartos deve ser zero ou maior')
      return false
    }
    
    const bathrooms = typeof formData.bathrooms === 'string' ? parseInt(formData.bathrooms) : formData.bathrooms
    if (bathrooms === undefined || bathrooms === null || bathrooms < 0) {
      toast.error('Número de banheiros deve ser zero ou maior')
      return false
    }
    
    const rent = typeof formData.rent === 'string' ? parseFloat(formData.rent) : formData.rent
    if (!rent || rent <= 0) {
      toast.error('Valor do aluguel deve ser maior que zero')
      return false
    }
    
    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }
    
    setIsLoading(true)

    try {
      const savedProperty = await onSave(formData)
      
      // Se há imagens pendentes e a propriedade foi salva com sucesso, fazer upload
      const pendingFiles = (formData as any).pendingFiles
      if (pendingFiles && pendingFiles.length > 0 && savedProperty?.id) {
        setUploadingImages(true)
        setUploadProgress(0)
        
        try {
          const result = await propertiesService.uploadImages(
            savedProperty.id,
            pendingFiles,
            (progress) => setUploadProgress(progress)
          )
          
          toast.success(`Propriedade salva e ${result.uploaded_files.length} imagem(ns) enviada(s)!`)
          
          // Limpar arquivos pendentes
          setFormData(prev => ({
            ...prev,
            pendingFiles: []
          }))
        } catch (error: any) {
          console.error("Erro ao fazer upload das imagens:", error)
          toast.error("Propriedade salva, mas houve erro no upload de imagens")
        } finally {
          setUploadingImages(false)
          setUploadProgress(0)
        }
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (field: keyof Property, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleImageUpload = async (files: FileList | File[]) => {
    const fileArray = Array.from(files)
    if (fileArray.length === 0) return

    // Validar tipos de arquivo
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    const invalidFiles = fileArray.filter(f => !validTypes.includes(f.type))
    
    if (invalidFiles.length > 0) {
      toast.error("Apenas imagens (JPG, PNG, GIF, WEBP) são permitidas")
      return
    }

    // Validar tamanho (10MB por arquivo)
    const maxSize = 10 * 1024 * 1024
    const oversizedFiles = fileArray.filter(f => f.size > maxSize)
    
    if (oversizedFiles.length > 0) {
      toast.error("Cada imagem deve ter no máximo 10MB")
      return
    }

    // Se a propriedade não foi salva ainda, armazena localmente
    if (!property?.id) {
      // Criar URLs temporárias para preview
      const tempUrls = fileArray.map(file => URL.createObjectURL(file))
      setFormData(prev => ({
        ...prev,
        images: [...(prev.images || []), ...tempUrls],
        // Armazena os arquivos para upload posterior
        pendingFiles: [...(prev.pendingFiles || []), ...fileArray]
      }))
      toast.success(`${fileArray.length} imagem(ns) adicionada(s) para upload`)
      return
    }

    // Upload imediato se a propriedade já existe
    setUploadingImages(true)
    setUploadProgress(0)

    try {
      const result = await propertiesService.uploadImages(
        property.id,
        fileArray,
        (progress) => setUploadProgress(progress)
      )

      // Recarregar propriedade atualizada do backend
      const updatedProperty = await propertiesService.getProperty(property.id)
      
      // Atualizar formData com todas as imagens do backend
      setFormData(prev => ({
        ...prev,
        images: updatedProperty.images || []
      }))

      toast.success(`${result.uploaded_files.length} imagem(ns) enviada(s) com sucesso!`)
    } catch (error: any) {
      console.error("Erro ao fazer upload:", error)
      toast.error(error.response?.data?.detail || "Erro ao enviar imagens")
    } finally {
      setUploadingImages(false)
      setUploadProgress(0)
    }
  }

  const handleRemoveImage = async (imageUrl: string, index: number) => {
    if (!property?.id) {
      // Se não tem ID, apenas remove localmente
      setFormData((prev) => ({ ...prev, images: prev.images.filter((_, i) => i !== index) }))
      return
    }

    try {
      await propertiesService.deleteImage(property.id, imageUrl)
      setFormData((prev) => ({ ...prev, images: prev.images.filter((_, i) => i !== index) }))
      toast.success("Imagem removida com sucesso")
    } catch (error: any) {
      console.error("Erro ao deletar imagem:", error)
      toast.error(error.response?.data?.detail || "Erro ao remover imagem")
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleImageUpload(e.dataTransfer.files)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleImageUpload(e.target.files)
    }
  }

  const addOrUpdateUnit = (unit: Unit) => {
    if (editingUnit) {
      // Edit existing unit
      const updatedUnits = formData.units?.map(u => u.id === unit.id ? unit : u) || []
      handleInputChange('units', updatedUnits)
    } else {
      // Add new unit
      const newUnit = { ...unit, id: Date.now().toString() }
      const updatedUnits = [...(formData.units || []), newUnit]
      handleInputChange('units', updatedUnits)
    }
    setShowUnitDialog(false)
    setEditingUnit(null)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{property ? "Editar Imóvel" : "Novo Imóvel"}</DialogTitle>
          <DialogDescription>
            {property ? "Edite as informações do imóvel." : "Adicione um novo imóvel à sua carteira."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <Tabs defaultValue="basic" className="w-full">
            <TabsList className={`grid w-full ${formData.isResidential ? 'grid-cols-4' : 'grid-cols-3'}`}>
              <TabsTrigger value="basic">Informações Básicas</TabsTrigger>
              <TabsTrigger value="details">Detalhes</TabsTrigger>
              {formData.isResidential && (
                <TabsTrigger value="units">Unidades</TabsTrigger>
              )}
              <TabsTrigger value="images">Fotos</TabsTrigger>
            </TabsList>

            <TabsContent value="basic" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="name">Nome do Imóvel *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => handleInputChange("name", e.target.value)}
                    placeholder="Ex: Apartamento 101"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="type">Tipo *</Label>
                  <Select value={formData.type} onValueChange={(value) => {
                    handleInputChange("type", value)
                    handleInputChange("isResidential", value === "residential")
                  }}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="apartment">Apartamento</SelectItem>
                      <SelectItem value="house">Casa</SelectItem>
                      <SelectItem value="commercial">Comercial</SelectItem>
                      <SelectItem value="residential">Residencial</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="address">Endereço *</Label>
                  <Input
                    id="address"
                    value={formData.address}
                    onChange={(e) => handleInputChange("address", e.target.value)}
                    placeholder="Rua, número"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="neighborhood">Bairro *</Label>
                  <Input
                    id="neighborhood"
                    value={formData.neighborhood}
                    onChange={(e) => handleInputChange("neighborhood", e.target.value)}
                    placeholder="Nome do bairro"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="city">Cidade *</Label>
                  <Input
                    id="city"
                    value={formData.city}
                    onChange={(e) => handleInputChange("city", e.target.value)}
                    placeholder="Nome da cidade"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="state">Estado *</Label>
                  <Input
                    id="state"
                    value={formData.state}
                    onChange={(e) => handleInputChange("state", e.target.value)}
                    placeholder="SP"
                    maxLength={2}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="zipCode">CEP *</Label>
                  <Input
                    id="zipCode"
                    type="text"
                    inputMode="numeric"
                    value={formData.zipCode}
                    onChange={(e) => handleInputChange("zipCode", cepMask(e.target.value))}
                    placeholder="00000-000"
                    maxLength={9}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="status">Status</Label>
                  <Select value={formData.status} onValueChange={(value) => handleInputChange("status", value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="vacant">Vago</SelectItem>
                      <SelectItem value="occupied">Ocupado</SelectItem>
                      <SelectItem value="maintenance">Manutenção</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tenant_id">Inquilino (opcional)</Label>
                  <Select
                    value={formData.tenant_id ? String(formData.tenant_id) : undefined}
                    onValueChange={(value) => handleInputChange("tenant_id", value === "none" ? null : parseInt(value))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione um inquilino" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Nenhum</SelectItem>
                      {tenants.map(t => (
                        <SelectItem key={t.id} value={String(t.id)}>{t.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="details" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="area">Área (m²) *</Label>
                  <Input
                    id="area"
                    type="text"
                    inputMode="decimal"
                    value={formData.area || ''}
                    onChange={(e) => {
                      const masked = areaMask(e.target.value)
                      handleInputChange("area", masked ? parseFloat(masked) : '')
                    }}
                    placeholder="Ex: 85.5"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="rent">Valor do Aluguel *</Label>
                  <div className="relative">
                    <span className="absolute left-3 top-2.5 text-gray-500">R$</span>
                    <Input
                      id="rent"
                      type="text"
                      inputMode="decimal"
                      value={formData.rent ? currencyMask(formData.rent) : ''}
                      onChange={(e) => {
                        const value = currencyUnmask(e.target.value)
                        handleInputChange("rent", value)
                      }}
                      placeholder="0,00"
                      className="pl-10"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="bedrooms">Quartos *</Label>
                  <Input
                    id="bedrooms"
                    type="text"
                    inputMode="numeric"
                    value={formData.bedrooms || ''}
                    onChange={(e) => {
                      const masked = integerMask(e.target.value)
                      handleInputChange("bedrooms", masked ? parseInt(masked) : '')
                    }}
                    placeholder="Ex: 2"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="bathrooms">Banheiros *</Label>
                  <Input
                    id="bathrooms"
                    type="text"
                    inputMode="numeric"
                    value={formData.bathrooms || ''}
                    onChange={(e) => {
                      const masked = integerMask(e.target.value)
                      handleInputChange("bathrooms", masked ? parseInt(masked) : '')
                    }}
                    placeholder="Ex: 1"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="parkingSpaces">Vagas de Garagem</Label>
                  <Input
                    id="parkingSpaces"
                    type="text"
                    inputMode="numeric"
                    value={formData.parkingSpaces || ''}
                    onChange={(e) => {
                      const masked = integerMask(e.target.value)
                      handleInputChange("parkingSpaces", masked ? parseInt(masked) : '')
                    }}
                    placeholder="Ex: 1"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Descrição</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleInputChange("description", e.target.value)}
                  placeholder="Descreva as características do imóvel..."
                  rows={4}
                />
              </div>
            </TabsContent>

            {formData.isResidential && (
              <TabsContent value="units" className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium">Unidades do Residencial</h3>
                  <Button 
                    type="button" 
                    onClick={() => {
                      setEditingUnit(null)
                      setShowUnitDialog(true)
                    }}
                    size="sm"
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Nova Unidade
                  </Button>
                </div>

                <div className="grid gap-4">
                  {formData.units?.map((unit) => (
                    <Card key={unit.id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="space-y-1">
                          <div className="flex items-center space-x-4">
                            <h4 className="font-medium">Unidade {unit.number}</h4>
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              unit.status === 'occupied' ? 'bg-green-100 text-green-800' :
                              unit.status === 'vacant' ? 'bg-gray-100 text-gray-800' :
                              'bg-orange-100 text-orange-800'
                            }`}>
                              {unit.status === 'occupied' ? 'Ocupada' : 
                               unit.status === 'vacant' ? 'Vaga' : 'Manutenção'}
                            </span>
                          </div>
                          <div className="text-sm text-gray-600">
                            {unit.area}m² • {unit.bedrooms} quartos • {unit.bathrooms} banheiros • R$ {unit.rent.toLocaleString('pt-BR')}
                          </div>
                          {unit.tenant && (
                            <div className="text-sm text-blue-600">Inquilino: {unit.tenant}</div>
                          )}
                        </div>
                        <div className="flex space-x-2">
                          <Button 
                            type="button" 
                            variant="outline" 
                            size="sm"
                            onClick={() => {
                              setEditingUnit(unit)
                              setShowUnitDialog(true)
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button 
                            type="button" 
                            variant="outline" 
                            size="sm"
                            onClick={() => {
                              const updatedUnits = formData.units?.filter(u => u.id !== unit.id) || []
                              handleInputChange('units', updatedUnits)
                            }}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))}
                  
                  {(!formData.units || formData.units.length === 0) && (
                    <div className="text-center py-8 text-gray-500">
                      <Building className="mx-auto h-12 w-12 mb-4 opacity-50" />
                      <p>Nenhuma unidade cadastrada</p>
                      <p className="text-sm">Clique em "Nova Unidade" para começar</p>
                    </div>
                  )}
                </div>
              </TabsContent>
            )}

            <TabsContent value="images" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Fotos do Imóvel</CardTitle>
                  <CardDescription>
                    Adicione fotos para destacar seu imóvel
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {/* Área de Upload */}
                  <div
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                        className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                          dragActive ? 'border-primary bg-primary/5' : 'border-gray-300'
                        }`}
                      >
                        <input
                          type="file"
                          id="property-images"
                          multiple
                          accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
                          onChange={handleFileSelect}
                          className="hidden"
                          disabled={uploadingImages}
                        />
                        <label
                          htmlFor="property-images"
                          className="cursor-pointer flex flex-col items-center"
                        >
                          {uploadingImages ? (
                            <>
                              <Loader2 className="h-8 w-8 text-primary mb-2 animate-spin" />
                              <p className="text-sm text-gray-600 mb-1">Enviando imagens...</p>
                              <div className="w-full max-w-xs bg-gray-200 rounded-full h-2 mt-2">
                                <div
                                  className="bg-primary h-2 rounded-full transition-all"
                                  style={{ width: `${uploadProgress}%` }}
                                />
                              </div>
                              <p className="text-xs text-gray-500 mt-1">{uploadProgress}%</p>
                            </>
                          ) : (
                            <>
                              <Upload className="h-8 w-8 text-gray-400 mb-2" />
                              <p className="text-sm text-gray-600 mb-1">
                                Arraste imagens aqui ou clique para selecionar
                              </p>
                              <p className="text-xs text-gray-500">
                                JPG, PNG, GIF, WEBP (máx. 10MB cada, até 10 imagens)
                              </p>
                            </>
                          )}
                        </label>
                      </div>

                      {/* Grid de Imagens */}
                      {formData.images.length > 0 && (
                        <div className="grid gap-4 md:grid-cols-3 mt-4">
                          {formData.images.map((image, index) => (
                            <div key={index} className="relative group">
                              <img
                                src={image || "/placeholder.svg"}
                                alt={`Foto ${index + 1}`}
                                className="w-full h-32 object-cover rounded-lg"
                              />
                              <Button
                                type="button"
                                variant="destructive"
                                size="sm"
                                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                                onClick={() => handleRemoveImage(image, index)}
                              >
                                <X className="h-3 w-3" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          <DialogFooter className="mt-6">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Salvando..." : property ? "Salvar Alterações" : "Criar Imóvel"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>

      {/* Unit Dialog */}
      <UnitDialog 
        open={showUnitDialog}
        onOpenChange={setShowUnitDialog}
        unit={editingUnit}
        onSave={addOrUpdateUnit}
      />
    </Dialog>
  )
}

// Unit Dialog Component
interface UnitDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  unit?: Unit | null
  onSave: (unit: Unit) => void
}

function UnitDialog({ open, onOpenChange, unit, onSave }: UnitDialogProps) {
  const [unitData, setUnitData] = useState<Unit>({
    id: '',
    number: '',
    area: 0,
    bedrooms: 0,
    bathrooms: 0,
    rent: 0,
    status: 'vacant'
  })

  useEffect(() => {
    if (unit) {
      setUnitData(unit)
    } else {
      setUnitData({
        id: '',
        number: '',
        area: 0,
        bedrooms: 0,
        bathrooms: 0,
        rent: 0,
        status: 'vacant'
      })
    }
  }, [unit])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave(unitData)
  }

  const handleInputChange = (field: keyof Unit, value: any) => {
    setUnitData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{unit ? 'Editar Unidade' : 'Nova Unidade'}</DialogTitle>
          <DialogDescription>
            {unit ? 'Atualize as informações da unidade.' : 'Adicione uma nova unidade ao residencial.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="unit-number">Número da Unidade</Label>
              <Input
                id="unit-number"
                value={unitData.number}
                onChange={(e) => handleInputChange('number', e.target.value)}
                placeholder="Ex: 101, 202, Casa A"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="unit-area">Área (m²)</Label>
              <Input
                id="unit-area"
                type="number"
                value={unitData.area}
                onChange={(e) => handleInputChange('area', Number(e.target.value))}
                min="1"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="unit-bedrooms">Quartos</Label>
              <Input
                id="unit-bedrooms"
                type="number"
                value={unitData.bedrooms}
                onChange={(e) => handleInputChange('bedrooms', Number(e.target.value))}
                min="0"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="unit-bathrooms">Banheiros</Label>
              <Input
                id="unit-bathrooms"
                type="number"
                value={unitData.bathrooms}
                onChange={(e) => handleInputChange('bathrooms', Number(e.target.value))}
                min="0"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="unit-rent">Valor do Aluguel (R$)</Label>
              <Input
                id="unit-rent"
                type="number"
                value={unitData.rent}
                onChange={(e) => handleInputChange('rent', Number(e.target.value))}
                min="0"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="unit-status">Status</Label>
              <Select value={unitData.status} onValueChange={(value) => handleInputChange('status', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="vacant">Vaga</SelectItem>
                  <SelectItem value="occupied">Ocupada</SelectItem>
                  <SelectItem value="maintenance">Manutenção</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {unitData.status === 'occupied' && (
            <div className="space-y-2">
              <Label htmlFor="unit-tenant">Inquilino</Label>
              <Input
                id="unit-tenant"
                value={unitData.tenant || ''}
                onChange={(e) => handleInputChange('tenant', e.target.value)}
                placeholder="Nome do inquilino"
              />
            </div>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit">
              {unit ? 'Salvar Alterações' : 'Adicionar Unidade'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
