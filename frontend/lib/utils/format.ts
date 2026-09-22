/**
 * Formatação e parsing de números e datas segundo o locale DA MÁQUINA.
 *
 * Por que não fixar `pt-BR`: a máquina do usuário pode estar em `en-US` com
 * teclado ABNT2. Com o locale cravado no código, o app exibia `1.234,56`
 * enquanto o `<input type="date">` e o teclado numérico do SO falavam
 * `1,234.56` — e a divergência entre `,` e `.` virava erro de digitação.
 * Tudo aqui deriva do locale que o navegador reporta, então exibição e
 * entrada usam sempre os mesmos separadores.
 *
 * A API é o outro lado da moeda: ela fala o formato canônico de máquina
 * (`600.00`, ISO-8601), nunca o do usuário. `toNumber` e `toDate` fazem a
 * ponte, e é só por eles que valores vindos do backend devem passar.
 */

/** Usado no servidor, onde `navigator` não existe. */
const SSR_LOCALE = 'pt-BR'

/** Locale da máquina do usuário. */
export function getLocale(): string {
  if (typeof navigator !== 'undefined' && navigator.language) {
    return navigator.language
  }
  return SSR_LOCALE
}

/** Separador decimal do locale da máquina (`,` em pt-BR, `.` em en-US). */
export function getDecimalSeparator(locale: string = getLocale()): string {
  return (
    new Intl.NumberFormat(locale)
      .formatToParts(1.1)
      .find((p) => p.type === 'decimal')?.value ?? '.'
  )
}

/** Separador de milhar do locale da máquina. */
export function getGroupSeparator(locale: string = getLocale()): string {
  return (
    new Intl.NumberFormat(locale)
      .formatToParts(1000)
      .find((p) => p.type === 'group')?.value ?? ','
  )
}

/** Número canônico de máquina, como a API serializa `Decimal`: `600`, `600.00`. */
const CANONICAL_NUMBER = /^-?\d+(\.\d+)?$/

/**
 * Converte para número qualquer coisa que a API ou um formulário entregue.
 *
 * Aceita número, decimal canônico da API (`"600.0"`) e texto digitado em
 * qualquer locale (`"1.234,56"`, `"1,234.56"`, `"R$ 600,00"`). Devolve
 * `fallback` quando não há número algum.
 *
 * O caso que motivou a função: `"600.0"` vinha da API como string (Pydantic
 * serializa `Decimal` assim) e era lido como uma sequência de centavos —
 * `6000` centavos, ou seja, R$ 60,00 no lugar de R$ 600,00.
 */
export function toNumber(value: unknown, fallback = 0): number {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : fallback
  }
  if (typeof value !== 'string') return fallback

  const trimmed = value.trim()
  if (trimmed === '') return fallback

  // Decimal canônico da API: não passa pela heurística de locale, senão
  // "1.234" (mil duzentos e trinta e quatro para a API) viraria 1,234.
  if (CANONICAL_NUMBER.test(trimmed)) {
    const canonical = Number(trimmed)
    return Number.isFinite(canonical) ? canonical : fallback
  }

  // Texto digitado: o ÚLTIMO separador é o decimal, qualquer outro é milhar.
  // Vale para as duas convenções sem precisar saber qual delas o usuário usou.
  const cleaned = trimmed.replace(/[^\d.,-]/g, '')
  const lastSeparator = Math.max(cleaned.lastIndexOf('.'), cleaned.lastIndexOf(','))

  let normalized: string
  if (lastSeparator === -1) {
    normalized = cleaned.replace(/[.,]/g, '')
  } else {
    const integerPart = cleaned.slice(0, lastSeparator).replace(/[.,]/g, '')
    const decimalPart = cleaned.slice(lastSeparator + 1).replace(/[^\d]/g, '')
    normalized = `${integerPart}.${decimalPart}`
  }

  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : fallback
}

/** Número no formato da máquina. Por padrão, 2 casas — valores monetários. */
export function formatNumber(
  value: unknown,
  options: Intl.NumberFormatOptions = { minimumFractionDigits: 2, maximumFractionDigits: 2 },
): string {
  return new Intl.NumberFormat(getLocale(), options).format(toNumber(value))
}

/**
 * Valor em reais no formato da máquina.
 *
 * A moeda continua sendo BRL — o locale decide como ESCREVER o número, não
 * qual moeda o aluguel está. Em `en-US` sai `R$600.00`; em `pt-BR`,
 * `R$ 600,00`.
 */
export function formatCurrency(value: unknown, currency = 'BRL'): string {
  return new Intl.NumberFormat(getLocale(), {
    style: 'currency',
    currency,
  }).format(toNumber(value))
}

/**
 * Converte para `Date` o que a API manda (ISO-8601).
 *
 * Uma data pura (`"2026-09-21"`, sem hora) é interpretada como local, não
 * UTC: `new Date("2026-09-21")` cai à meia-noite UTC e, em fuso negativo
 * como o do Brasil, exibia o dia 20 — vencimento sempre um dia adiantado.
 */
export function toDate(value: unknown): Date | null {
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
  if (typeof value === 'number') {
    const fromNumber = new Date(value)
    return Number.isNaN(fromNumber.getTime()) ? null : fromNumber
  }
  if (typeof value !== 'string' || value.trim() === '') return null

  const dateOnly = value.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (dateOnly) {
    return new Date(Number(dateOnly[1]), Number(dateOnly[2]) - 1, Number(dateOnly[3]))
  }

  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

/** Data no formato da máquina. Vazio quando o valor não é uma data. */
export function formatDate(
  value: unknown,
  options: Intl.DateTimeFormatOptions = {},
): string {
  const date = toDate(value)
  if (!date) return ''
  return new Intl.DateTimeFormat(getLocale(), options).format(date)
}

/** Data e hora no formato da máquina. */
export function formatDateTime(value: unknown): string {
  const date = toDate(value)
  if (!date) return ''
  return new Intl.DateTimeFormat(getLocale(), {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(date)
}

/**
 * Data no formato que o `<input type="date">` exige (`yyyy-MM-dd`), que é
 * sempre ISO independentemente do locale — o navegador é quem traduz para a
 * aparência que o usuário vê.
 */
export function toDateInputValue(value: unknown): string {
  const date = toDate(value)
  if (!date) return ''
  const mes = String(date.getMonth() + 1).padStart(2, '0')
  const dia = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${mes}-${dia}`
}
