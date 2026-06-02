// Utilitários para máscaras de input

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
 * Máscara para valores monetários
 * Formato: R$ 1.234,56
 * Funciona como calculadora - dígitos entram da direita para esquerda
 */
export function currencyMask(value: string | number): string {
  if (!value && value !== 0) return ''
  
  // Se for número, converte para string de centavos
  let numbers: string
  if (typeof value === 'number') {
    // Multiplica por 100 para obter centavos e remove decimais
    numbers = Math.round(value * 100).toString()
  } else {
    // Remove tudo exceto números
    numbers = value.replace(/\D/g, '')
  }
  
  if (!numbers || numbers === '0') return '0,00'
  
  // Converte para número e divide por 100 (os últimos 2 dígitos são centavos)
  const amount = parseInt(numbers) / 100
  
  // Formata como moeda brasileira
  return amount.toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

/**
 * Remove máscara de moeda e retorna número
 * Converte a string formatada de volta para número decimal
 */
export function currencyUnmask(value: string): number {
  if (!value) return 0
  
  // Remove tudo exceto números
  const numbers = value.replace(/\D/g, '')
  
  if (!numbers) return 0
  
  // Divide por 100 pois os últimos 2 dígitos são centavos
  return parseInt(numbers) / 100
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
 * Máscara para área em metros quadrados
 * Formato: 123.45 m²
 */
export function areaMask(value: string): string {
  if (!value) return ''
  
  // Remove tudo exceto números e ponto
  const cleaned = value.replace(/[^\d.]/g, '')
  
  // Garante apenas um ponto decimal
  const parts = cleaned.split('.')
  if (parts.length > 2) {
    return `${parts[0]}.${parts.slice(1).join('')}`
  }
  
  return cleaned
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
 * Máscara para percentuais
 * Formato: 12,34
 * Permite valores decimais com até 2 casas
 */
export function percentageMask(value: string | number): string {
  if (!value && value !== 0) return ''
  
  // Se for número, converte para string com 2 decimais
  let stringValue: string
  if (typeof value === 'number') {
    stringValue = value.toFixed(2).replace('.', ',')
  } else {
    // Remove tudo exceto números e vírgula
    stringValue = value.replace(/[^\d,]/g, '')
    
    // Garante apenas uma vírgula
    const parts = stringValue.split(',')
    if (parts.length > 2) {
      stringValue = `${parts[0]},${parts.slice(1).join('')}`
    }
    
    // Limita casas decimais a 2
    if (parts.length === 2 && parts[1].length > 2) {
      stringValue = `${parts[0]},${parts[1].substring(0, 2)}`
    }
  }
  
  return stringValue
}

/**
 * Remove máscara de percentual e retorna número
 */
export function percentageUnmask(value: string): number {
  if (!value) return 0
  
  // Substitui vírgula por ponto e converte para número
  const cleaned = value.replace(',', '.')
  const number = parseFloat(cleaned)
  
  return isNaN(number) ? 0 : number
}
