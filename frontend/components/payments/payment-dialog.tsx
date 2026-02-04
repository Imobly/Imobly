"use client"

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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Calculator, AlertCircle, Info, Loader2 } from "lucide-react"
import { currencyMask, currencyUnmask } from "@/lib/utils/masks"
import { useContracts } from "@/lib/hooks/useContracts"
import { contractsService } from "@/lib/api/contracts"
import { paymentsService } from "@/lib/api/payments"
import { apiClient } from "@/lib/api/client"
import { ContractResponse } from "@/lib/types/api"
import { toast } from "sonner"

interface PaymentFormData {
  contract_id: number
  due_date: string
  payment_date: string
  paid_amount: string
  payment_method?: "pix" | "boleto" | "transferencia" | "dinheiro" | "cartao_credito" | "cartao_debito" | "outro"
  description?: string
}

interface PaymentDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  payment?: any | null
  onSave: () => void
}

const initialPayment: PaymentFormData = {
  contract_id: 0,
  due_date: "",
  payment_date: new Date().toISOString().split('T')[0],
  paid_amount: "",
  payment_method: undefined,
  description: "",
}

interface CalculationResult {
  base_amount: number
  fine_amount: number
  interest_amount: number
  total_addition: number
  total_expected: number
  days_overdue: number
  status: string
  paid_amount: number
  remaining_amount: number
}

export function PaymentDialog({ open, onOpenChange, payment, onSave }: PaymentDialogProps) {
  const [formData, setFormData] = useState<PaymentFormData>(initialPayment)
  const [isLoading, setIsLoading] = useState(false)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})
  const [selectedContract, setSelectedContract] = useState<ContractResponse | null>(null)
  const [calculation, setCalculation] = useState<CalculationResult | null>(null)
  const [isCalculating, setIsCalculating] = useState(false)
  const [propertyName, setPropertyName] = useState<string>("")
  const [tenantName, setTenantName] = useState<string>("")
  const [dueDay, setDueDay] = useState<number>(0)
  
  const { contracts } = useContracts()

  const toBRShort = (iso: string) => {
    if (!iso) return ""
    // Parse data como local, não UTC, para evitar problema de timezone
    const [year, month, day] = iso.split('-').map(Number)
    const dd = String(day).padStart(2, '0')
    const mm = String(month).padStart(2, '0')
    const yy = String(year).slice(-2)
    return `${dd}/${mm}/${yy}`
  }
  const fromBRShortToISO = (br: string) => {
    if (!br) return ""
    // Limpar string para aceitar apenas números e /
    const cleaned = br.replace(/[^\d\/]/g, '')
    const m = cleaned.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2}|\d{4})$/)
    if (!m) return "" // Retorna vazio se formato inválido
    const d = parseInt(m[1], 10)
    const mo = parseInt(m[2], 10)
    let y = parseInt(m[3], 10)
    if (y < 100) y = 2000 + y
    
    // Validar valores
    if (d < 1 || d > 31 || mo < 1 || mo > 12) return ""
    
    // Formatar como ISO
    const dd = String(d).padStart(2, '0')
    const mm = String(mo).padStart(2, '0')
    return `${y}-${mm}-${dd}`
  }

  useEffect(() => {
    if (payment) {
      // Se for edição, carregar dados existentes
      setFormData({
        contract_id: payment.contract_id || 0,
        due_date: payment.due_date || "",
        payment_date: payment.payment_date || new Date().toISOString().split('T')[0],
        paid_amount: payment.amount ? currencyMask(payment.amount) : "",
        payment_method: payment.payment_method || undefined,
        description: payment.description || "",
      })
    } else {
      setFormData(initialPayment)
      setCalculation(null)
      setSelectedContract(null)
    }
  }, [payment, open])

  // Carregar dados do contrato selecionado
  const handleContractChange = async (contractId: string) => {
    const id = parseInt(contractId)
    if (!id) return

    try {
      const contract = await contractsService.getContract(id)
      setSelectedContract(contract)
      
      // Buscar nome do imóvel
      try {
        const property = await apiClient.get<{ name: string }>(`/properties/${contract.property_id}/`)
        setPropertyName(property.name || `Imóvel #${contract.property_id}`)
      } catch {
        setPropertyName(`Imóvel #${contract.property_id}`)
      }
      
      // Buscar nome do inquilino
      try {
        const tenant = await apiClient.get<{ name: string }>(`/tenants/${contract.tenant_id}/`)
        setTenantName(tenant.name || `Inquilino #${contract.tenant_id}`)
      } catch {
        setTenantName(`Inquilino #${contract.tenant_id}`)
      }
      
      // Calcular data de vencimento baseada no dia de início do contrato
      // Parse data como local para evitar problema de timezone
      const [year, month, day] = contract.start_date.split('-').map(Number)
      const dayOfMonth = day
      setDueDay(dayOfMonth)
      
      const today = new Date()
      const dueDate = new Date(today.getFullYear(), today.getMonth(), dayOfMonth)
      
      setFormData(prev => ({
        ...prev,
        contract_id: contract.id,
        due_date: dueDate.toISOString().split('T')[0],
      }))
    } catch (error) {
      console.error('Erro ao carregar contrato:', error)
      toast.error("Erro ao carregar dados do contrato")
    }
  }

  // Calcular valores automaticamente quando mudar data de pagamento ou vencimento
  useEffect(() => {
    const calculate = async () => {
      if (!formData.contract_id || !formData.due_date) return

      setIsCalculating(true)
      try {
        const result = await paymentsService.calculatePayment({
          contract_id: formData.contract_id,
          due_date: formData.due_date,
          payment_date: formData.payment_date || undefined,
          paid_amount: formData.paid_amount ? currencyUnmask(formData.paid_amount) : undefined,
        })
        setCalculation(result)
      } catch (error) {
        console.error('Erro ao calcular pagamento:', error)        // Mesmo com erro, permite continuar
        setCalculation(null)
      } finally {
        setIsCalculating(false)
      }
    }

    // Adiciona delay para evitar muitas requisições
    const timer = setTimeout(calculate, 300)
    return () => clearTimeout(timer)
  }, [formData.contract_id, formData.due_date, formData.payment_date])

  // Preenche automaticamente o valor pago com o total calculado se usuário não digitou nada
  useEffect(() => {
    if (calculation && (!formData.paid_amount || currencyUnmask(formData.paid_amount) === 0)) {
      const autoValue = currencyMask(calculation.total_expected)
      setFormData(prev => ({ ...prev, paid_amount: autoValue }))
    }
  }, [calculation])

  // Validação do formulário
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}

    if (!formData.contract_id || formData.contract_id === 0) {
      errors.contract_id = "Selecione um contrato"
    }
    if (!formData.due_date) {
      errors.due_date = "Data de vencimento é obrigatória"
    }
    if (!formData.payment_date) {
      errors.payment_date = "Data de pagamento é obrigatória"
    }
    
    const paidAmountValue = currencyUnmask(formData.paid_amount)
    
    if (!formData.paid_amount || paidAmountValue <= 0) {
      errors.paid_amount = "Valor deve ser maior que zero"
    }
    
    if (!formData.payment_method) {
      errors.payment_method = "Forma de pagamento é obrigatória"
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const resolveErrorMessage = (error: any): string => {
    const status = error?.response?.status
    const data = error?.response?.data
    if (!status) return 'Erro inesperado. Verifique sua conexão.'
    switch (status) {
      case 401:
        return 'Sessão expirada. Faça login novamente.'
      case 403:
        return 'Sem permissão para este contrato.'
      case 404:
        return 'Recurso não encontrado.'
      case 422: {
        const detail = data?.detail
        if (Array.isArray(detail)) return detail.map((d: any) => d.msg || d.message || JSON.stringify(d)).join(' | ')
        return typeof detail === 'string' ? detail : 'Dados inválidos. Verifique os campos.'
      }
      case 500:
        return 'Erro interno do servidor. Tente novamente.'
      default:
        return data?.detail || `Erro ${status}. Tente novamente.`
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      toast.error('Preencha todos os campos obrigatórios')
      return
    }
    
    setIsLoading(true)
    
    try {
      const paidAmount = currencyUnmask(formData.paid_amount)
      // Edição de pagamento existente
      if (payment?.id) {
        const updateBody: any = {
          due_date: formData.due_date,
          payment_date: formData.payment_date,
          amount: calculation?.base_amount ?? undefined,
          fine_amount: calculation?.fine_amount ?? undefined,
          total_amount: paidAmount || calculation?.total_expected || undefined,
          payment_method: formData.payment_method,
          description: formData.description?.trim() || undefined,
        }
        // Definir status conforme valores
        if (paidAmount) {
          const expected = calculation?.total_expected ?? paidAmount
          updateBody.status = paidAmount >= expected ? 'paid' : 'partial'
        }
        await paymentsService.updatePayment(payment.id, updateBody)
        toast.success('Pagamento atualizado com sucesso!')
        onSave()
        onOpenChange(false)
        return
      }

      // Registro de novo pagamento
      if (!selectedContract) {
        toast.error('Erro: Contrato não encontrado. Selecione novamente.')
        return
      }
      
      try {
        const storedUser = localStorage.getItem('user')
        if (storedUser) {
          const user = JSON.parse(storedUser)
          const contractUserId = Number(selectedContract.user_id)
          const currentUserId = Number(user?.id)
          if (contractUserId && currentUserId && contractUserId !== currentUserId) {
            toast.error('Este contrato pertence a outro usuário; não é possível registrar pagamento.')
            return
          }
        }
      } catch (e) {
        // Silenciar erro de user check
      }
      
      const paymentData: any = {
        contract_id: formData.contract_id,
        due_date: formData.due_date,
        payment_date: formData.payment_date,
        paid_amount: paidAmount,
      }
      if (selectedContract.property_id) paymentData.property_id = selectedContract.property_id
      if (selectedContract.tenant_id) paymentData.tenant_id = selectedContract.tenant_id
      if (formData.payment_method) paymentData.payment_method = formData.payment_method
      if (formData.description && formData.description.trim() !== '') paymentData.description = formData.description.trim()
      
      await paymentsService.registerPayment(paymentData)
      toast.success('Pagamento registrado com sucesso!')
      onSave()
      onOpenChange(false)
    } catch (error: any) {
      toast.error(resolveErrorMessage(error))
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (field: keyof PaymentFormData, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{payment ? "Editar Pagamento" : "Registrar Pagamento"}</DialogTitle>
          <DialogDescription>
            {payment ? "Edite as informações do pagamento." : "Registre um novo pagamento com cálculo automático de multa e juros."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Seleção de Contrato */}
          <div className="space-y-2">
            <Label htmlFor="contract_id">Contrato *</Label>
            <Select 
              value={formData.contract_id === 0 ? "" : formData.contract_id.toString()} 
              onValueChange={handleContractChange}
            >
              <SelectTrigger className={validationErrors.contract_id ? "border-red-500" : ""}>
                <SelectValue placeholder="Selecione um contrato" />
              </SelectTrigger>
              <SelectContent>
                {contracts.filter(c => c.status === 'active').map((contract) => (
                  <SelectItem key={contract.id} value={contract.id.toString()}>
                    {contract.title} - R$ {parseFloat(contract.rent.toString()).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {validationErrors.contract_id && (
              <p className="text-sm text-red-500 flex items-center">
                <AlertCircle className="h-3 w-3 mr-1" />
                {validationErrors.contract_id}
              </p>
            )}
          </div>

          {/* Informações do Contrato */}
          {selectedContract && (
            <Card className="bg-gray-50">
              <CardHeader>
                <CardTitle className="text-sm">Informações do Contrato</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Imóvel:</span>
                  <span className="font-medium">{propertyName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Inquilino:</span>
                  <span className="font-medium">{tenantName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Dia de Vencimento:</span>
                  <span className="font-medium">Todo dia {dueDay}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Valor do Aluguel:</span>
                  <span className="font-medium">R$ {parseFloat(selectedContract.rent.toString()).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Vigência:</span>
                  <span className="font-medium">
                    {selectedContract.start_date.split('-').reverse().join('/')} até {selectedContract.end_date.split('-').reverse().join('/')}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Taxa de Multa:</span>
                  <span className="font-medium">{parseFloat(selectedContract.fine_rate.toString()).toFixed(2)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Taxa de Juros:</span>
                  <span className="font-medium">{parseFloat(selectedContract.interest_rate.toString()).toFixed(2)}% ao mês</span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Datas */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="due_date">Data de Vencimento *</Label>
              <Input
                id="due_date"
                type="date"
                value={formData.due_date}
                onChange={(e) => handleInputChange("due_date", e.target.value)}
                className={validationErrors.due_date ? "border-red-500" : ""}
                required
              />
              {validationErrors.due_date && (
                <p className="text-sm text-red-500 flex items-center">
                  <AlertCircle className="h-3 w-3 mr-1" />
                  {validationErrors.due_date}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="payment_date">Data de Pagamento *</Label>
              <Input
                id="payment_date"
                type="date"
                value={formData.payment_date}
                onChange={(e) => handleInputChange("payment_date", e.target.value)}
                className={validationErrors.payment_date ? "border-red-500" : ""}
                required
              />
              {validationErrors.payment_date && (
                <p className="text-sm text-red-500 flex items-center">
                  <AlertCircle className="h-3 w-3 mr-1" />
                  {validationErrors.payment_date}
                </p>
              )}
            </div>
          </div>

          {/* Cálculo Automático */}
          {calculation && (
            <Card className="border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <Calculator className="mr-2 h-5 w-5" />
                  Cálculo Automático
                </CardTitle>
                <CardDescription className="flex items-center gap-2">
                  {calculation.days_overdue > 0 ? (
                    <>
                      <span className="px-2 py-0.5 rounded text-xs bg-red-100 text-red-700 font-medium">Atrasado</span>
                      Pagamento com {calculation.days_overdue} dias de atraso
                    </>
                  ) : (
                    <span className="px-2 py-0.5 rounded text-xs bg-green-100 text-green-700 font-medium">Em dia</span>
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-700">Valor Base:</span>
                    <span className="font-medium">R$ {parseFloat(calculation.base_amount.toString()).toFixed(2).replace('.', ',')}</span>
                  </div>
                  {parseFloat(calculation.fine_amount.toString()) > 0 && (
                    <div className="flex justify-between text-orange-700">
                      <span>Multa ({selectedContract ? parseFloat(selectedContract.fine_rate.toString()).toFixed(2) : '0.00'}%):</span>
                      <span className="font-medium">R$ {parseFloat(calculation.fine_amount.toString()).toFixed(2).replace('.', ',')}</span>
                    </div>
                  )}
                  {parseFloat(calculation.interest_amount.toString()) > 0 && (
                    <div className="flex justify-between text-orange-700">
                      <span>Juros ({calculation.days_overdue} dias):</span>
                      <span className="font-medium">R$ {parseFloat(calculation.interest_amount.toString()).toFixed(2).replace('.', ',')}</span>
                    </div>
                  )}
                  <div className="border-t pt-2 mt-2 flex justify-between text-lg font-bold">
                    <span>Total a Pagar:</span>
                    <span className="text-green-700">R$ {parseFloat(calculation.total_expected.toString()).toFixed(2).replace('.', ',')}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {isCalculating && (
            <div className="flex items-center justify-center text-sm text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              Calculando...
            </div>
          )}

          {/* Valor Pago e Forma de Pagamento */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="paid_amount">Valor Pago *</Label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-gray-500">R$</span>
                <Input
                  id="paid_amount"
                  type="text"
                  inputMode="decimal"
                  value={formData.paid_amount}
                  onChange={(e) => handleInputChange("paid_amount", currencyMask(currencyUnmask(e.target.value)))}
                  placeholder="0,00"
                  className={validationErrors.paid_amount ? "border-red-500 pl-10" : "pl-10"}
                  required
                />
              </div>
              {calculation && currencyUnmask(formData.paid_amount) !== calculation.total_expected && (
                <p className="text-xs text-orange-600 flex items-center">
                  <Info className="h-3 w-3 mr-1" />
                  Total calculado: R$ {calculation.total_expected.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  <Button type="button" variant="link" className="p-0 ml-2 h-auto text-xs" onClick={() => handleInputChange('paid_amount', currencyMask(calculation.total_expected))}>Usar total</Button>
                </p>
              )}
              {validationErrors.paid_amount && (
                <p className="text-sm text-red-500 flex items-center">
                  <AlertCircle className="h-3 w-3 mr-1" />
                  {validationErrors.paid_amount}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="payment_method">Forma de Pagamento *</Label>
              <Select
                value={formData.payment_method || ""}
                onValueChange={(value) => handleInputChange("payment_method", value as any)}
              >
                <SelectTrigger className={validationErrors.payment_method ? "border-red-500" : ""}>
                  <SelectValue placeholder="Selecione a forma" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pix">PIX</SelectItem>
                  <SelectItem value="boleto">Boleto</SelectItem>
                  <SelectItem value="transferencia">Transferência Bancária</SelectItem>
                  <SelectItem value="dinheiro">Dinheiro</SelectItem>
                  <SelectItem value="cartao_credito">Cartão de Crédito</SelectItem>
                  <SelectItem value="cartao_debito">Cartão de Débito</SelectItem>
                  <SelectItem value="outro">Outro</SelectItem>
                </SelectContent>
              </Select>
              {validationErrors.payment_method && (
                <p className="text-sm text-red-500 flex items-center">
                  <AlertCircle className="h-3 w-3 mr-1" />
                  {validationErrors.payment_method}
                </p>
              )}
            </div>
          </div>

          {/* Descrição */}
          <div className="space-y-2">
            <Label htmlFor="description">Descrição (Opcional)</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleInputChange("description", e.target.value)}
              placeholder="Ex: Pagamento referente a novembro/2025"
              rows={3}
            />
          </div>
          <DialogFooter className="mt-6">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Salvando...
                </>
              ) : (
                "Registrar Pagamento"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
