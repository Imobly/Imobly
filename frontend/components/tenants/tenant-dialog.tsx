"use client"

import React, { useState, useEffect } from "react"
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Upload, X, Loader2, FileText } from "lucide-react"
import { apiClient } from "@/lib/api/client"
import { phoneMask, cpfCnpjMask, cpfCnpjUnmask, currencyMask, currencyUnmask, percentageMask, percentageUnmask, integerMask } from "@/lib/utils/masks"
import { tenantsService } from "@/lib/api/tenants"
import { useAuth } from "@/lib/contexts/auth"
import { toast } from "sonner"

interface TenantFormData {
  name: string
  email: string
  phone: string
  cpf_cnpj: string
  birth_date: string | null
  profession: string
  emergency_contact?: {
    name: string
    phone: string
    relationship: string
  }
  documents?: {
    id: string
    name: string
    type: 'rg' | 'cpf' | 'cnh' | 'comprovante_residencia' | 'comprovante_renda' | 'contrato' | 'outros'
    url: string
  }[]
  contract_id?: number
  contract?: {
    title: string
    property_id: number | null
    start_date: string
    end_date: string
    rent: string
    deposit: string
    interest_rate: string
    fine_rate: string
    status: 'active' | 'expired' | 'terminated'
  }
  status: 'active' | 'inactive'
}

interface TenantDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  tenant?: any | null
  onSave: (tenant: TenantFormData) => Promise<any>
}

const initialTenant: TenantFormData = {
  name: "",
  email: "",
  phone: "",
  cpf_cnpj: "",
  birth_date: null,
  profession: "",
  emergency_contact: {
    name: "",
    phone: "",
    relationship: "",
  },
  documents: [],
  contract_id: undefined,
  contract: {
    title: "",
    property_id: null,
    start_date: "",
    end_date: "",
    rent: "",
    deposit: "",
    interest_rate: "",
    fine_rate: "",
    status: "active",
  },
  status: "active",
}

export function TenantDialog({ open, onOpenChange, tenant, onSave }: TenantDialogProps) {
  const [formData, setFormData] = useState<TenantFormData>(initialTenant)
  const [isLoading, setIsLoading] = useState(false)
  const [properties, setProperties] = useState<any[]>([])
  const [loadingProperties, setLoadingProperties] = useState(false)
  const [uploadingDocs, setUploadingDocs] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [dragActive, setDragActive] = useState(false)
  const [selectedDocType, setSelectedDocType] = useState<'rg' | 'cpf' | 'cnh' | 'comprovante_residencia' | 'comprovante_renda' | 'contrato' | 'outros'>('rg')
  const [pendingDocFiles, setPendingDocFiles] = useState<{ files: File[], docType: string }[]>([])
  const { user } = useAuth()

  // Carregar propriedades ao abrir o dialog
  useEffect(() => {
    if (open) {
      loadProperties()
      setPendingDocFiles([])
    }
  }, [open])

  // Preencher automaticamente o valor do aluguel quando uma propriedade for selecionada
  useEffect(() => {
    const propertyId = formData.contract?.property_id
    if (propertyId && properties.length > 0) {
      const selectedProperty = properties.find(p => p.id === propertyId)
      if (selectedProperty && selectedProperty.rent) {
        // Formatar o valor do aluguel no formato brasileiro
        const rentValue = selectedProperty.rent.toString().replace('.', ',')
        const formattedRent = currencyMask(rentValue)
        
        // Atualizar o valor do aluguel no contrato
        setFormData(prev => ({
          ...prev,
          contract: {
            ...prev.contract,
            rent: formattedRent
          }
        }))
        
        console.log(`💰 Aluguel preenchido automaticamente: R$ ${formattedRent}`)
      }
    }
  }, [formData.contract?.property_id, properties])

  const loadProperties = async () => {
    setLoadingProperties(true)
    try {
      const response = await apiClient.get('/properties/')
      setProperties(response || [])
    } catch (error) {
      console.error('Erro ao carregar propriedades:', error)
      setProperties([])
    } finally {
      setLoadingProperties(false)
    }
  }

  useEffect(() => {
    if (tenant) {
      // Função para carregar contrato se contract_id existir
      const loadContractData = async () => {
        if (tenant.contract_id) {
          try {
            const contract = await apiClient.get<any>(`/contracts/${tenant.contract_id}`)
            setFormData({
              name: tenant.name || "",
              email: tenant.email || "",
              phone: tenant.phone || "",
              cpf_cnpj: tenant.cpf_cnpj || "",
              birth_date: tenant.birth_date || null,
              profession: tenant.profession || "",
              emergency_contact: tenant.emergency_contact || {
                name: "",
                phone: "",
                relationship: "",
              },
              documents: tenant.documents || [],
              contract_id: tenant.contract_id,
              contract: {
                title: contract.title || "",
                property_id: contract.property_id || null,
                start_date: contract.start_date || "",
                end_date: contract.end_date || "",
                rent: contract.rent?.toString() || "",
                deposit: contract.deposit?.toString() || "",
                interest_rate: contract.interest_rate?.toString() || "",
                fine_rate: contract.fine_rate?.toString() || "",
                status: contract.status || "active",
              },
              status: tenant.status || "active",
            })
          } catch (error) {
            console.error("Erro ao carregar contrato:", error)
            // Se falhar, carregar sem contrato
            setFormData({
              name: tenant.name || "",
              email: tenant.email || "",
              phone: tenant.phone || "",
              cpf_cnpj: tenant.cpf_cnpj || "",
              birth_date: tenant.birth_date || null,
              profession: tenant.profession || "",
              emergency_contact: tenant.emergency_contact || {
                name: "",
                phone: "",
                relationship: "",
              },
              documents: tenant.documents || [],
              contract_id: tenant.contract_id,
              contract: initialTenant.contract,
              status: tenant.status || "active",
            })
          }
        } else {
          // Sem contract_id
          setFormData({
            name: tenant.name || "",
            email: tenant.email || "",
            phone: tenant.phone || "",
            cpf_cnpj: tenant.cpf_cnpj || "",
            birth_date: tenant.birth_date || null,
            profession: tenant.profession || "",
            emergency_contact: tenant.emergency_contact || {
              name: "",
              phone: "",
              relationship: "",
            },
            documents: tenant.documents || [],
            contract_id: undefined,
            contract: initialTenant.contract,
            status: tenant.status || "active",
          })
        }
      }
      
      loadContractData()
    } else {
      setFormData(initialTenant)
    }
  }, [tenant])

  const validateForm = (): boolean => {
    // Validar campos obrigatórios conforme backend TenantBase
    if (!formData.name || formData.name.trim() === '') {
      toast.error('Nome do inquilino é obrigatório')
      return false
    }
    if (!formData.email || formData.email.trim() === '') {
      toast.error('Email é obrigatório')
      return false
    }
    // Validação simples de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.email)) {
      toast.error('Email inválido')
      return false
    }
    if (!formData.phone || formData.phone.trim() === '') {
      toast.error('Telefone é obrigatório')
      return false
    }
    if (!formData.cpf_cnpj || formData.cpf_cnpj.trim() === '') {
      toast.error('CPF/CNPJ é obrigatório')
      return false
    }
    if (!formData.profession || formData.profession.trim() === '') {
      toast.error('Profissão é obrigatória')
      return false
    }
    
    // Validar contrato se algum campo foi preenchido
    const contract = formData.contract
    if (contract) {
      const hasAnyContractField = contract.title || contract.property_id || contract.start_date || contract.end_date || contract.rent || contract.deposit
      
      if (hasAnyContractField) {
        // Se começou a preencher contrato, validar campos obrigatórios
        if (!contract.title || contract.title.trim() === '') {
          toast.error('Título do contrato é obrigatório quando há dados de contrato')
          return false
        }
        if (!contract.property_id) {
          toast.error('Imóvel é obrigatório quando há dados de contrato')
          return false
        }
        if (!contract.start_date) {
          toast.error('Data de início do contrato é obrigatória')
          return false
        }
        if (!contract.end_date) {
          toast.error('Data de término do contrato é obrigatória')
          return false
        }
        if (!contract.rent || contract.rent.trim() === '' || parseFloat(contract.rent.replace(/[^\d,]/g, '').replace(',', '.')) <= 0) {
          toast.error('Valor do aluguel deve ser maior que zero')
          return false
        }
        
        // Validar datas - comparar strings ISO diretamente para evitar timezone
        if (contract.end_date <= contract.start_date) {
          toast.error('Data de término deve ser posterior à data de início')
          return false
        }
      }
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
      console.log("💾 Salvando inquilino:", formData)
      const savedTenant = await onSave(formData)

      // Upload pending documents after tenant is saved
      if (pendingDocFiles.length > 0 && savedTenant?.id) {
        setUploadingDocs(true)
        setUploadProgress(0)
        let totalUploaded = 0
        try {
          for (const pending of pendingDocFiles) {
            await tenantsService.uploadDocuments(
              savedTenant.id,
              pending.files,
              pending.docType as any,
              user!.id,
              savedTenant.documents || [],
              (progress) => setUploadProgress(progress)
            )
            totalUploaded += pending.files.length
          }
          toast.success(`${totalUploaded} documento(s) enviado(s) com sucesso!`)
        } catch (uploadError: any) {
          console.error("Erro ao fazer upload de documentos pendentes:", uploadError)
          toast.error("Inquilino salvo, mas houve erro no upload de documentos")
        } finally {
          setUploadingDocs(false)
          setUploadProgress(0)
          setPendingDocFiles([])
        }
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (field: keyof TenantFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleNestedChange = (parent: string, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [parent]: {
        ...(prev[parent as keyof TenantFormData] as any),
        [field]: value,
      },
    }))
  }

  const handleDocumentUpload = async (files: FileList | File[]) => {
    const fileArray = Array.from(files)
    if (fileArray.length === 0) return

    // Validar tipos de arquivo
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    const invalidFiles = fileArray.filter(f => !validTypes.includes(f.type))
    
    if (invalidFiles.length > 0) {
      toast.error("Apenas imagens, PDF, DOC ou DOCX são permitidos")
      return
    }

    // Validar tamanho (10MB por arquivo)
    const maxSize = 10 * 1024 * 1024
    const oversizedFiles = fileArray.filter(f => f.size > maxSize)
    
    if (oversizedFiles.length > 0) {
      toast.error("Cada arquivo deve ter no máximo 10MB")
      return
    }

    // Se o inquilino ainda não foi salvo, armazenar arquivos para upload posterior
    if (!tenant?.id) {
      setPendingDocFiles(prev => [...prev, { files: fileArray, docType: selectedDocType }])
      toast.success(`${fileArray.length} documento(s) adicionado(s) para envio após salvar`)
      return
    }

    setUploadingDocs(true)
    setUploadProgress(0)

    try {
      const result = await tenantsService.uploadDocuments(
        tenant.id,
        fileArray,
        selectedDocType,
        user!.id,
        formData.documents || [],
        (progress) => setUploadProgress(progress)
      )

      // Atualizar documentos locais com os novos
      setFormData(prev => ({
        ...prev,
        documents: [...(prev.documents || []), ...result.uploaded_files.map(d => ({
          id: d.id || crypto.randomUUID(),
          name: d.name,
          type: d.type as any,
          url: d.url || '',
        }))]
      }))

      toast.success(`${result.uploaded_files.length} documento(s) enviado(s) com sucesso!`)
    } catch (error: any) {
      console.error("Erro ao fazer upload:", error)
      toast.error(error?.message || "Erro ao enviar documentos")
    } finally {
      setUploadingDocs(false)
      setUploadProgress(0)
    }
  }

  const handleRemoveDocument = async (documentUrl: string) => {
    if (!tenant?.id) {
      // Se não tem ID, apenas remove localmente
      setFormData(prev => ({
        ...prev,
        documents: prev.documents?.filter(d => d.url !== documentUrl)
      }))
      return
    }

    try {
      await tenantsService.deleteDocument(tenant.id, documentUrl, formData.documents || [])
      setFormData(prev => ({
        ...prev,
        documents: prev.documents?.filter(d => d.url !== documentUrl)
      }))
      toast.success("Documento removido com sucesso")
    } catch (error: any) {
      console.error("Erro ao deletar documento:", error)
      toast.error(error?.message || "Erro ao remover documento")
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
      handleDocumentUpload(e.dataTransfer.files)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleDocumentUpload(e.target.files)
    }
  }

  const getDocTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      rg: 'RG',
      cpf: 'CPF',
      cnh: 'CNH',
      comprovante_residencia: 'Comprovante de Residência',
      comprovante_renda: 'Comprovante de Renda',
      contrato: 'Contrato',
      outros: 'Outros'
    }
    return labels[type] || type
  }

  const addDocument = () => {
    const newDoc = {
      id: `doc-${Date.now()}`,
      name: "",
      type: "outros" as const,
      url: "",
    }
    setFormData(prev => ({ 
      ...prev, 
      documents: [...(prev.documents || []), newDoc] 
    }))
  }

  const removeDocument = (docId: string) => {
    setFormData(prev => ({
      ...prev,
      documents: (prev.documents || []).filter(doc => doc.id !== docId)
    }))
  }

  const updateDocument = (docId: string, field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      documents: (prev.documents || []).map(doc =>
        doc.id === docId ? { ...doc, [field]: value } : doc
      )
    }))
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{tenant ? "Editar Inquilino" : "Novo Inquilino"}</DialogTitle>
          <DialogDescription>
            {tenant ? "Edite as informações do inquilino." : "Adicione um novo inquilino ao sistema."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <Tabs defaultValue="personal" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="personal">Dados Pessoais</TabsTrigger>
              <TabsTrigger value="contract">Contrato</TabsTrigger>
              <TabsTrigger value="documents">Documentos</TabsTrigger>
            </TabsList>

            <TabsContent value="personal" className="space-y-4">
              <div className="grid gap-4 py-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="name">Nome Completo *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => handleInputChange("name", e.target.value)}
                      placeholder="Ex: João da Silva"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email">Email *</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange("email", e.target.value)}
                      placeholder="Ex: joao@email.com"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone">Telefone *</Label>
                    <Input
                      id="phone"
                      type="text"
                      inputMode="tel"
                      value={formData.phone}
                      onChange={(e) => handleInputChange("phone", phoneMask(e.target.value))}
                      placeholder="(11) 99999-9999"
                      maxLength={15}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="cpf_cnpj">CPF/CNPJ *</Label>
                    <Input
                      id="cpf_cnpj"
                      type="text"
                      inputMode="numeric"
                      value={formData.cpf_cnpj}
                      onChange={(e) => handleInputChange("cpf_cnpj", cpfCnpjMask(e.target.value))}
                      placeholder="000.000.000-00"
                      maxLength={18}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="birth_date">Data de Nascimento</Label>
                    <Input
                      id="birth_date"
                      type="date"
                      value={formData.birth_date || ""}
                      onChange={(e) => handleInputChange("birth_date", e.target.value || null)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="profession">Profissão *</Label>
                    <Input
                      id="profession"
                      value={formData.profession}
                      onChange={(e) => handleInputChange("profession", e.target.value)}
                      placeholder="Ex: Engenheiro"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="status">Status</Label>
                  <Select value={formData.status} onValueChange={(value) => handleInputChange("status", value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Ativo</SelectItem>
                      <SelectItem value="inactive">Inativo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Emergency Contact Section */}
                <div className="pt-6 mt-6 border-t">
                  <h3 className="text-lg font-semibold mb-4">Contato de Emergência</h3>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="emergency_name">Nome</Label>
                      <Input
                        id="emergency_name"
                        value={formData.emergency_contact?.name || ""}
                        onChange={(e) => handleNestedChange("emergency_contact", "name", e.target.value)}
                        placeholder="Ex: Maria da Silva"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="emergency_phone">Telefone</Label>
                      <Input
                        id="emergency_phone"
                        type="text"
                        inputMode="tel"
                        value={formData.emergency_contact?.phone || ""}
                        onChange={(e) => handleNestedChange("emergency_contact", "phone", phoneMask(e.target.value))}
                        placeholder="(11) 88888-8888"
                        maxLength={15}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="emergency_relationship">Relacionamento</Label>
                      <Select 
                        value={formData.emergency_contact?.relationship || ""} 
                        onValueChange={(value) => handleNestedChange("emergency_contact", "relationship", value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Selecione o relacionamento" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="spouse">Cônjuge</SelectItem>
                          <SelectItem value="parent">Pai/Mãe</SelectItem>
                          <SelectItem value="sibling">Irmão/Irmã</SelectItem>
                          <SelectItem value="child">Filho/Filha</SelectItem>
                          <SelectItem value="friend">Amigo(a)</SelectItem>
                          <SelectItem value="other">Outro</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="contract" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Informações do Contrato</CardTitle>
                  <CardDescription>
                    Vincule o inquilino a um imóvel e defina os termos do contrato
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2 md:col-span-2">
                      <Label htmlFor="contract_title">Título do Contrato</Label>
                      <Input
                        id="contract_title"
                        value={formData.contract?.title || ""}
                        onChange={(e) => handleNestedChange("contract", "title", e.target.value)}
                        placeholder="Ex: Contrato Ana Costa - Apartamento 101"
                      />
                    </div>

                    <div className="space-y-2 md:col-span-2">
                      <Label htmlFor="contract_property">Imóvel</Label>
                      <Select
                        value={formData.contract?.property_id?.toString() || ""}
                        onValueChange={(value) => handleNestedChange("contract", "property_id", parseInt(value))}
                        disabled={loadingProperties}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder={loadingProperties ? "Carregando..." : "Selecione um imóvel"} />
                        </SelectTrigger>
                        <SelectContent>
                          {properties.map((property) => (
                            <SelectItem key={property.id} value={property.id.toString()}>
                              {property.name} - {property.address}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="contract_start_date">Data de Início</Label>
                      <Input
                        id="contract_start_date"
                        type="date"
                        value={formData.contract?.start_date || ""}
                        onChange={(e) => handleNestedChange("contract", "start_date", e.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="contract_end_date">Data de Término</Label>
                      <Input
                        id="contract_end_date"
                        type="date"
                        value={formData.contract?.end_date || ""}
                        onChange={(e) => handleNestedChange("contract", "end_date", e.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="contract_rent">Valor do Aluguel</Label>
                      <div className="relative">
                        <span className="absolute left-3 top-2.5 text-gray-500">R$</span>
                        <Input
                          id="contract_rent"
                          type="text"
                          inputMode="decimal"
                          value={formData.contract?.rent || ""}
                          onChange={(e) => {
                            const value = currencyMask(currencyUnmask(e.target.value))
                            handleNestedChange("contract", "rent", value)
                          }}
                          placeholder="0,00"
                          className="pl-10"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="contract_deposit">Depósito/Caução</Label>
                      <div className="relative">
                        <span className="absolute left-3 top-2.5 text-gray-500">R$</span>
                        <Input
                          id="contract_deposit"
                          type="text"
                          inputMode="decimal"
                          value={formData.contract?.deposit || ""}
                          onChange={(e) => {
                            const value = currencyMask(currencyUnmask(e.target.value))
                            handleNestedChange("contract", "deposit", value)
                          }}
                          placeholder="0,00"
                          className="pl-10"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="contract_interest_rate">Taxa de Juros (% ao mês)</Label>
                      <Input
                        id="contract_interest_rate"
                        type="text"
                        inputMode="decimal"
                        value={formData.contract?.interest_rate || ""}
                        onChange={(e) => {
                          const value = percentageMask(e.target.value)
                          handleNestedChange("contract", "interest_rate", value)
                        }}
                        placeholder="Ex: 2,00"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="contract_fine_rate">Taxa de Multa (% do valor)</Label>
                      <Input
                        id="contract_fine_rate"
                        type="text"
                        inputMode="decimal"
                        value={formData.contract?.fine_rate || ""}
                        onChange={(e) => {
                          const value = percentageMask(e.target.value)
                          handleNestedChange("contract", "fine_rate", value)
                        }}
                        placeholder="Ex: 10,00"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="contract_status">Status do Contrato</Label>
                      <Select
                        value={formData.contract?.status || "active"}
                        onValueChange={(value) => handleNestedChange("contract", "status", value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="active">Ativo</SelectItem>
                          <SelectItem value="expired">Expirado</SelectItem>
                          <SelectItem value="terminated">Rescindido</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="documents" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Documentos</CardTitle>
                  <CardDescription>
                    {tenant?.id 
                      ? "Envie CNH, RG, contratos, comprovantes de renda, etc." 
                      : "Selecione documentos agora — serão enviados automaticamente ao salvar"}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <>
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
                          id="tenant-documents"
                          multiple
                          accept="image/jpeg,image/jpg,image/png,application/pdf,.doc,.docx"
                          onChange={handleFileSelect}
                          className="hidden"
                          disabled={uploadingDocs}
                        />
                        <label htmlFor="tenant-documents" className="cursor-pointer flex flex-col items-center">
                          {uploadingDocs ? (
                            <>
                              <Loader2 className="h-8 w-8 text-primary mb-2 animate-spin" />
                              <p className="text-sm text-gray-600 mb-1">Enviando documentos...</p>
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
                                Arraste arquivos aqui ou clique para selecionar
                              </p>
                              <p className="text-xs text-gray-500">
                                PDF, DOC, DOCX ou imagens (máx. 10MB cada, até 5 arquivos)
                              </p>
                            </>
                          )}
                        </label>
                      </div>

                      {/* Lista de Documentos */}
                      {formData.documents && formData.documents.length > 0 && (
                        <div className="space-y-2">
                          <Label>Documentos Enviados</Label>
                          <div className="space-y-2">
                            {formData.documents.map((doc) => (
                              <div key={doc.id} className="flex items-center justify-between p-3 border rounded-lg bg-gray-50">
                                <div className="flex items-center gap-3 flex-1">
                                  <FileText className="h-5 w-5 text-primary" />
                                  <div className="flex-1">
                                    <p className="text-sm font-medium">{doc.name}</p>
                                    <a 
                                      href={doc.url.startsWith('http') ? doc.url : `http://localhost:8000${doc.url}`}
                                      target="_blank" 
                                      rel="noopener noreferrer"
                                      className="text-xs text-blue-600 hover:underline"
                                    >
                                      Visualizar arquivo
                                    </a>
                                  </div>
                                </div>
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleRemoveDocument(doc.url)}
                                >
                                  <X className="h-4 w-4" />
                                </Button>
                              </div>
                            ))}  
                          </div>
                        </div>
                      )}

                      {/* Pending Files (not yet uploaded - for new tenants) */}
                      {pendingDocFiles.length > 0 && (
                        <div className="space-y-2">
                          <Label>Documentos Pendentes (serão enviados ao salvar)</Label>
                          <div className="space-y-2">
                            {pendingDocFiles.map((pending, idx) =>
                              pending.files.map((file, fIdx) => (
                                <div key={`pending-${idx}-${fIdx}`} className="flex items-center justify-between p-3 border rounded-lg bg-amber-50 border-amber-200">
                                  <div className="flex items-center gap-3 flex-1">
                                    <FileText className="h-5 w-5 text-amber-600" />
                                    <div className="flex-1">
                                      <p className="text-sm font-medium">{file.name}</p>
                                      <p className="text-xs text-amber-600">
                                        {getDocTypeLabel(pending.docType)} — aguardando envio
                                      </p>
                                    </div>
                                  </div>
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                      setPendingDocFiles(prev => {
                                        const updated = [...prev]
                                        updated[idx] = {
                                          ...updated[idx],
                                          files: updated[idx].files.filter((_, i) => i !== fIdx)
                                        }
                                        return updated.filter(p => p.files.length > 0)
                                      })
                                    }}
                                  >
                                    <X className="h-4 w-4" />
                                  </Button>
                                </div>
                              ))
                            )}
                          </div>
                        </div>
                      )}
                    </>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          <DialogFooter className="mt-6">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Salvando..." : tenant ? "Salvar Alterações" : "Criar Inquilino"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}