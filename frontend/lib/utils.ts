import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

import { formatCurrency } from './utils/format'
import { currencyUnmask as unmask } from './utils/masks'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Formata um valor como moeda no padrão da máquina do usuário.
 *
 * Reexporta `formatCurrency` para não haver duas regras de formatação de
 * dinheiro no projeto — era daqui que saía o `pt-BR` cravado.
 */
export function currencyFormat(value: unknown): string {
  return formatCurrency(value)
}

/**
 * Remove a máscara de moeda e retorna o número.
 */
export function currencyUnmask(value: string): number {
  return unmask(value)
}
