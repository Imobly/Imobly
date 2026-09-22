// Utilitários para máscaras de input

import { formatNumber, getDecimalSeparator, toNumber } from './format'

/**
 * Máscara para telefone brasileiro
 * Aceita: (11) 98888-8888 ou (11) 3888-8888
 */
export function phoneMask(value: string): string {
  if (!value) return ''
  
  // Remove tudo que não é número
  const numbers = value.replace(/\D/g, '')
  
  // Limita a 11 dígitos (DDD + 9 dígitos)
  const limited = numbers.slice(0, 11)
  
  // Aplica a máscara
  if (limited.length <= 2) {
    return limited
  } else if (limited.length <= 6) {
    return `(${limited.slice(0, 2)}) ${limited.slice(2)}`
  } else if (limited.length <= 10) {
    return `(${limited.slice(0, 2)}) ${limited.slice(2, 6)}-${limited.slice(6)}`
  } else {
    return `(${limited.slice(0, 2)}) ${limited.slice(2, 7)}-${limited.slice(7)}`
  }
}

/**
 * Remove máscara de telefone, retorna apenas números
 */
export function phoneUnmask(value: string): string {
  return value.replace(/\D/g, '')
}

/**
 * Máscara para CPF
 * Formato: 000.000.000-00
 */
export function cpfMask(value: string): string {
  if (!value) return ''
  
  const numbers = value.replace(/\D/g, '')
  const limited = numbers.slice(0, 11)
  
  if (limited.length <= 3) {
    return limited
  } else if (limited.length <= 6) {
    return `${limited.slice(0, 3)}.${limited.slice(3)}`
  } else if (limited.length <= 9) {
    return `${limited.slice(0, 3)}.${limited.slice(3, 6)}.${limited.slice(6)}`
  } else {
    return `${limited.slice(0, 3)}.${limited.slice(3, 6)}.${limited.slice(6, 9)}-${limited.slice(9)}`
  }
}

/**
 * Máscara para CNPJ
 * Formato: 00.000.000/0000-00
 */
export function cnpjMask(value: string): string {
  if (!value) return ''
  
  const numbers = value.replace(/\D/g, '')
  const limited = numbers.slice(0, 14)
  
  if (limited.length <= 2) {
    return limited
  } else if (limited.length <= 5) {
    return `${limited.slice(0, 2)}.${limited.slice(2)}`
  } else if (limited.length <= 8) {
    return `${limited.slice(0, 2)}.${limited.slice(2, 5)}.${limited.slice(5)}`
  } else if (limited.length <= 12) {
    return `${limited.slice(0, 2)}.${limited.slice(2, 5)}.${limited.slice(5, 8)}/${limited.slice(8)}`
  } else {
    return `${limited.slice(0, 2)}.${limited.slice(2, 5)}.${limited.slice(5, 8)}/${limited.slice(8, 12)}-${limited.slice(12)}`
  }
}

/**
 * Máscara para CPF ou CNPJ (detecta automaticamente)
 */
export function cpfCnpjMask(value: string): string {
  if (!value) return ''
  
  const numbers = value.replace(/\D/g, '')
  
  if (numbers.length <= 11) {
    return cpfMask(value)
  } else {
    return cnpjMask(value)
  }
}

/**
 * Remove máscara de CPF/CNPJ, retorna apenas números
 */
export function cpfCnpjUnmask(value: string): string {
  return value.replace(/\D/g, '')
}

/**
 * Máscara para CEP
 * Formato: 00000-000
 */
export function cepMask(value: string): string {
  if (!value) return ''
  
  const numbers = value.replace(/\D/g, '')
  const limited = numbers.slice(0, 8)
  
  if (limited.length <= 5) {
    return limited
  } else {
    return `${limited.slice(0, 5)}-${limited.slice(5)}`
  }
}

/**
 * Formata um valor monetário no padrão da máquina do usuário (2 casas).
 *
 * Aceita número ou string — inclusive o decimal canônico que a API devolve
 * (`"600.0"`, resultado de `Decimal` serializado pelo Pydantic). Antes essa
 * string era lida dígito a dígito como centavos, e R$ 600,00 aparecia no
 * formulário de edição como R$ 60,00.
 *
 * Para o campo funcionar como calculadora (dígitos entrando da direita para a
 * esquerda), o `onChange` passa o texto por `currencyUnmask` PRIMEIRO; é a
 * divisão por 100 de lá que produz os centavos, não esta função.
 */
export function currencyMask(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return ''

  return formatNumber(value)
}

/**
 * Lê o campo monetário como uma sequência de centavos e devolve o número.
 *
 * Só os dígitos importam: digitar `6` vira 0,06 e `600` vira 6,00,
 * independentemente de a máquina separar decimais com `,` ou com `.`.
 */
export function currencyUnmask(value: string | number | null | undefined): number {
  if (value === null || value === undefined || value === '') return 0
  if (typeof value === 'number') return value

  // Preserva o sinal, que `\D` descartaria junto com os separadores.
  const negative = value.trim().startsWith('-')
  const numbers = value.replace(/\D/g, '')

  if (!numbers) return 0

  const amount = parseInt(numbers, 10) / 100
  return negative ? -amount : amount
}

/**
 * Máscara para números inteiros (evita zeros à esquerda)
 */
export function integerMask(value: string): string {
  if (!value) return ''
  
  // Remove tudo que não é número
  const numbers = value.replace(/\D/g, '')
  
  // Remove zeros à esquerda
  const withoutLeadingZeros = numbers.replace(/^0+/, '') || '0'
  
  return withoutLeadingZeros
}

/**
 * Máscara para área em metros quadrados.
 *
 * Aceita `,` e `.` como decimal — num teclado ABNT2 a tecla do bloco numérico
 * produz `,` mesmo com o Windows em `en-US` — e exibe o separador da máquina.
 * Mantém o texto como string enquanto se digita: converter para número a cada
 * tecla impedia digitar `85,` antes do `5`.
 */
export function areaMask(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return ''
  // Sem agrupamento de milhar: o separador de milhar voltaria por esta mesma
  // função na tecla seguinte e seria lido como decimal (1.500 -> 1,5).
  if (typeof value === 'number') {
    return formatNumber(value, { useGrouping: false, maximumFractionDigits: 2 })
  }

  const separator = getDecimalSeparator()

  // Normaliza qualquer separador digitado para o da máquina e mantém só o
  // primeiro: o resto é ruído de digitação.
  const cleaned = value.replace(/[^\d.,]/g, '').replace(/[.,]/g, separator)
  const [integerPart, ...rest] = cleaned.split(separator)

  if (rest.length === 0) return integerPart

  const decimalPart = rest.join('').slice(0, 2)
  return `${integerPart}${separator}${decimalPart}`
}

/**
 * Valida CPF
 */
export function isValidCPF(cpf: string): boolean {
  const numbers = cpf.replace(/\D/g, '')
  
  if (numbers.length !== 11) return false
  
  // Verifica se todos os dígitos são iguais
  if (/^(\d)\1+$/.test(numbers)) return false
  
  // Validação dos dígitos verificadores
  let sum = 0
  let remainder
  
  for (let i = 1; i <= 9; i++) {
    sum += parseInt(numbers.substring(i - 1, i)) * (11 - i)
  }
  
  remainder = (sum * 10) % 11
  if (remainder === 10 || remainder === 11) remainder = 0
  if (remainder !== parseInt(numbers.substring(9, 10))) return false
  
  sum = 0
  for (let i = 1; i <= 10; i++) {
    sum += parseInt(numbers.substring(i - 1, i)) * (12 - i)
  }
  
  remainder = (sum * 10) % 11
  if (remainder === 10 || remainder === 11) remainder = 0
  if (remainder !== parseInt(numbers.substring(10, 11))) return false
  
  return true
}

/**
 * Valida CNPJ
 */
export function isValidCNPJ(cnpj: string): boolean {
  const numbers = cnpj.replace(/\D/g, '')
  
  if (numbers.length !== 14) return false
  
  // Verifica se todos os dígitos são iguais
  if (/^(\d)\1+$/.test(numbers)) return false
  
  // Validação dos dígitos verificadores
  let size = numbers.length - 2
  let nums = numbers.substring(0, size)
  const digits = numbers.substring(size)
  let sum = 0
  let pos = size - 7
  
  for (let i = size; i >= 1; i--) {
    sum += parseInt(nums.charAt(size - i)) * pos--
    if (pos < 2) pos = 9
  }
  
  let result = sum % 11 < 2 ? 0 : 11 - (sum % 11)
  if (result !== parseInt(digits.charAt(0))) return false
  
  size = size + 1
  nums = numbers.substring(0, size)
  sum = 0
  pos = size - 7
  
  for (let i = size; i >= 1; i--) {
    sum += parseInt(nums.charAt(size - i)) * pos--
    if (pos < 2) pos = 9
  }
  
  result = sum % 11 < 2 ? 0 : 11 - (sum % 11)
  if (result !== parseInt(digits.charAt(1))) return false
  
  return true
}

/**
 * Valida telefone brasileiro
 */
export function isValidPhone(phone: string): boolean {
  const numbers = phone.replace(/\D/g, '')
  
  // Deve ter 10 (fixo) ou 11 (celular) dígitos
  if (numbers.length !== 10 && numbers.length !== 11) return false
  
  // DDD deve estar entre 11 e 99
  const ddd = parseInt(numbers.substring(0, 2))
  if (ddd < 11 || ddd > 99) return false
  
  return true
}

/**
 * Máscara para percentuais (até 2 casas), no separador da máquina.
 */
export function percentageMask(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return ''
  if (typeof value === 'number') return formatNumber(value, { useGrouping: false, maximumFractionDigits: 2 })

  const separator = getDecimalSeparator()
  const cleaned = value.replace(/[^\d.,]/g, '').replace(/[.,]/g, separator)
  const [integerPart, ...rest] = cleaned.split(separator)

  if (rest.length === 0) return integerPart

  const decimalPart = rest.join('').slice(0, 2)
  return `${integerPart}${separator}${decimalPart}`
}

/**
 * Remove máscara de percentual e retorna número.
 */
export function percentageUnmask(value: string | number | null | undefined): number {
  return toNumber(value)
}
