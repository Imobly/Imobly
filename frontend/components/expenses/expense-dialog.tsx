"use client"

import React, { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Upload, Loader2, X, FileText } from "lucide-react"
import { useProperties } from "@/lib/hooks/useProperties"
import { currencyMask, currencyUnmask } from "@/lib/utils/masks"
import { expensesService } from "@/lib/api/expenses"
import { toast } from "sonner"

interface ExpenseFormData {
  type: "maintenance" | "expense"
  category: string
  description: string
  amount: number
  date: string
  property_id: number
  status: "pending" | "paid" | "scheduled"
  priority?: "low" | "medium" | "high" | "urgent"
  vendor?: string
  number?: string
  receipt?: string
  documents?: {
    id: string
    name: string
    type: 'comprovante' | 'nota_fiscal' | 'recibo' | 'outros'
    url: string
    file_type?: string
    size?: number
  }[]
}

interface ExpenseDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  expense?: any | null
  onSave: (expense: ExpenseFormData) => void
}

const allCategories = [
  // Despesas
  "IPTU",
  "Condomínio", 
  "Seguro",
  "Taxa de Administração",
  "Publicidade",
  "Documentação",
  "Advocacia",
  "Contabilidade",
  // Manutenções
  "Hidráulica",
  "Elétrica", 
  "Pintura",
  "Limpeza",
  "Jardinagem",
  "Ar Condicionado",
  "Elevador",
  "Portaria",
  "Segurança",
  "Outros",
]

const initialExpense: ExpenseFormData = {
  type: "expense",
  category: "",
  description: "",
  amount: 0,
  date: new Date().toISOString().split("T")[0],
  property_id: 0,
  status: "pending",
  priority: "medium",
  vendor: "",
  number: "",
  receipt: "",
}

export function ExpenseDialog({ open, onOpenChange, expense, onSave }: ExpenseDialogProps) {
  const [formData, setFormData] = useState<ExpenseFormData>(initialExpense)
  const [isLoading, setIsLoading] = useState(false)
  const [uploadingDocs, setUploadingDocs] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [dragActive, setDragActive] = useState(false)
  
  const { properties } = useProperties()

  useEffect(() => {
    if (expense) {
      setFormData({
        type: expense.type || "expense",
        category: expense.category || "",
        description: expense.description || "",
        amount: expense.amount || 0,
        date: expense.date || new Date().toISOString().split("T")[0],
        property_id: expense.property_id || 0,
        status: expense.status || "pending",
        priority: expense.priority || "medium",
        vendor: expense.vendor || "",
        number: expense.number || "",
        receipt: expense.receipt || "",
        documents: expense.documents || [],
      })
    } else {
      setFormData(initialExpense)
    }
  }, [expense])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      console.log("💾 Salvando despesa:", formData)
      await onSave(formData)
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (field: keyof ExpenseFormData, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleDocumentUpload = async (files: FileList | File[]) => {
    if (!expense?.id) {
      toast.error("Salve a despesa antes de adicionar documentos")
      return
    }

    const fileArray = Array.from(files)
    
    // Validar número de arquivos (máximo 5)
    if (fileArray.length > 5) {
      toast.error("Máximo de 5 arquivos por vez")
      return
    }

    // Validar tipo de arquivo
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
    const invalidFiles = fileArray.filter(file => !validTypes.includes(file.type))
    if (invalidFiles.length > 0) {
      toast.error("Apenas imagens (JPG, PNG) ou PDF são permitidos")
      return
    }

    // Validar tamanho (10MB por arquivo)
    const maxSize = 10 * 1024 * 1024
    const oversizedFiles = fileArray.filter(file => file.size > maxSize)
    if (oversizedFiles.length > 0) {
      toast.error("Cada arquivo deve ter no máximo 10MB")
      return
    }

    setUploadingDocs(true)
    setUploadProgress(0)

    try {
      const result = await expensesService.uploadDocuments(
        expense.id,
        fileArray,
        'comprovante',
        (progress) => setUploadProgress(progress)
      )

      // Atualizar lista de documentos
      const newDocs = result.uploaded_files.map((file: any) => ({
        id: file.filename,
        name: file.original_filename,
        type: 'comprovante' as const,
        url: file.url,
        file_type: file.type,
        size: file.size,
      }))

      setFormData(prev => ({
        ...prev,
        documents: [...(prev.documents || []), ...newDocs]
      }))

      toast.success(`${fileArray.length} documento(s) enviado(s) com sucesso!`)
    } catch (error: any) {
      console.error("Erro ao fazer upload:", error)
      toast.error(error.detail || "Erro ao enviar documentos")
    } finally {
      setUploadingDocs(false)
      setUploadProgress(0)
    }
  }

  const handleRemoveDocument = async (documentUrl: string) => {
    if (!expense?.id) return

    try {
      await expensesService.deleteDocument(expense.id, documentUrl)
      
      setFormData(prev => ({
        ...prev,
        documents: (prev.documents || []).filter(doc => doc.url !== documentUrl)
      }))

      toast.success("Documento removido com sucesso!")
    } catch (error: any) {
      console.error("Erro ao remover documento:", error)
      toast.error(error.detail || "Erro ao remover documento")
    }
  }

  const handleReceiptUpload = async (file: File) => {
    if (!expense?.id) {
      toast.error("Salve a despesa antes de adicionar comprovante")
      return
    }

    // Validar tipo de arquivo
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
    if (!validTypes.includes(file.type)) {
      toast.error("Apenas imagens (JPG, PNG) ou PDF são permitidos")
      return
    }

    // Validar tamanho (10MB)
    const maxSize = 10 * 1024 * 1024
    if (file.size > maxSize) {
      toast.error("O arquivo deve ter no máximo 10MB")
      return
    }

    setUploadingDocs(true)
    setUploadProgress(0)

    try {
      const result = await expensesService.uploadReceipt(
        expense.id,
        file,
        (progress) => setUploadProgress(progress)
      )

      setFormData(prev => ({ ...prev, receipt: result.file_info.url }))
      toast.success("Comprovante enviado com sucesso!")
    } catch (error: any) {
      console.error("Erro ao fazer upload:", error)
      toast.error(error.response?.data?.detail || "Erro ao enviar comprovante")
    } finally {
      setUploadingDocs(false)
      setUploadProgress(0)
    }
  }

  const handleRemoveReceipt = async () => {
    if (!expense?.id) {
      setFormData(prev => ({ ...prev, receipt: "" }))
      return
    }

    try {
      await expensesService.deleteReceipt(expense.id)
      setFormData(prev => ({ ...prev, receipt: "" }))
      toast.success("Comprovante removido com sucesso")
    } catch (error: any) {
      console.error("Erro ao deletar comprovante:", error)
      toast.error(error.response?.data?.detail || "Erro ao remover comprovante")
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
      'comprovante': 'Comprovante',
      'nota_fiscal': 'Nota Fiscal',
      'recibo': 'Recibo',
      'outros': 'Outros',
    }
    return labels[type] || type
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{expense ? "Editar Despesa" : "Nova Despesa"}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <Tabs defaultValue="data" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="data">Dados</TabsTrigger>
              <TabsTrigger value="receipt">Comprovante</TabsTrigger>
            </TabsList>

            <TabsContent value="data" className="space-y-4">
              <div className="grid gap-4 py-4">
                {/* First Row: Type and Category */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="type">Tipo *</Label>
                    <Select value={formData.type} onValueChange={(value) => handleInputChange("type", value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione o tipo" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="expense">Despesa</SelectItem>
                        <SelectItem value="maintenance">Manutenção</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="category">Categoria *</Label>
                    <Select value={formData.category} onValueChange={(value) => handleInputChange("category", value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione a categoria" />
                      </SelectTrigger>
                      <SelectContent>
                        {allCategories.map((category) => (
                          <SelectItem key={category} value={category}>
                            {category}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Second Row: Property */}
                <div className="space-y-2">
                  <Label htmlFor="property_id">Imóvel *</Label>
                  <Select value={formData.property_id.toString()} onValueChange={(value) => handleInputChange("property_id", parseInt(value))}>
                    <SelectTrigger>
                      <SelectValue className="truncate" placeholder="Selecione o imóvel" />
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

                {/* Third Row: Amount and Date */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="amount">Valor (R$) *</Label>
                    <div className="relative">
                      <span className="absolute left-3 top-2.5 text-gray-500">R$</span>
                      <Input
                        id="amount"
                        type="text"
                        inputMode="decimal"
                        value={formData.amount ? currencyMask(formData.amount) : ""}
                        onChange={(e) => handleInputChange("amount", currencyUnmask(e.target.value))}
                        placeholder="0,00"
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="date">Data *</Label>
                    <Input
                      id="date"
                      type="date"
                      value={formData.date}
                      onChange={(e) => handleInputChange("date", e.target.value)}
                      required
                    />
                  </div>
                </div>

                {/* Fourth Row: Status and Priority */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="status">Status *</Label>
                    <Select value={formData.status} onValueChange={(value) => handleInputChange("status", value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pending">Pendente</SelectItem>
                        <SelectItem value="paid">Pago</SelectItem>
                        <SelectItem value="scheduled">Agendado</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="priority">Prioridade</Label>
                    <Select value={formData.priority} onValueChange={(value) => handleInputChange("priority", value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Baixa</SelectItem>
                        <SelectItem value="medium">Média</SelectItem>
                        <SelectItem value="high">Alta</SelectItem>
                        <SelectItem value="urgent">Urgente</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Fifth Row: Description */}
                <div className="space-y-2">
                  <Label htmlFor="description">Descrição *</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => handleInputChange("description", e.target.value)}
                    placeholder="Descreva a despesa..."
                    rows={3}
                    required
                  />
                </div>

                {/* Sixth Row: Vendor and Contact */}
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="vendor">Fornecedor</Label>
                    <Input
                      id="vendor"
                      value={formData.vendor}
                      onChange={(e) => handleInputChange("vendor", e.target.value)}
                      placeholder="Nome da Empresa/Profissional"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="number">Número</Label>
                    <Input
                      id="number"
                      value={formData.number}
                      onChange={(e) => handleInputChange("number", e.target.value)}
                      placeholder="Telefone ou número do prestador"
                    />
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="receipt" className="space-y-4">
              <div className="py-4">
                <p className="text-sm text-gray-600 mb-4">
                  {expense?.id 
                    ? "Adicione comprovantes, notas fiscais ou recibos (até 5 arquivos)" 
                    : "Salve a despesa primeiro para adicionar documentos"}
                </p>
                
                {!expense?.id ? (
                  <div className="border-2 border-dashed rounded-lg p-8 text-center bg-gray-50">
                    <Upload className="mx-auto h-8 w-8 text-gray-400 mb-2" />
                    <p className="text-sm text-gray-500">Salve a despesa primeiro para adicionar documentos</p>
                  </div>
                ) : (
                  <>
                    {/* Área de Upload */}
                    <div
                      onDragEnter={handleDrag}
                      onDragLeave={handleDrag}
                      onDragOver={handleDrag}
                      onDrop={handleDrop}
                      className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-colors mb-4 ${
                        dragActive ? 'border-primary bg-primary/5' : 'border-gray-300'
                      }`}
                    >
                      <input
                        type="file"
                        id="expense-documents"
                        multiple
                        accept="image/jpeg,image/jpg,image/png,application/pdf"
                        onChange={handleFileSelect}
                        className="hidden"
                        disabled={uploadingDocs}
                      />
                      <label htmlFor="expense-documents" className="cursor-pointer flex flex-col items-center">
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
                              PDF ou imagens (JPG, PNG) até 10MB cada, máximo 5 arquivos
                            </p>
                          </>
                        )}
                      </label>
                    </div>

                    {/* Lista de Documentos */}
                    {formData.documents && formData.documents.length > 0 && (
                      <div className="space-y-2">
                        <Label>Documentos Enviados ({formData.documents.length})</Label>
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
                  </>
                )}
              </div>
            </TabsContent>
          </Tabs>

          <DialogFooter className="mt-6">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Salvando..." : expense ? "Salvar Alterações" : "Criar Despesa"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}