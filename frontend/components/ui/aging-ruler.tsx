import * as React from 'react'

import { cn } from '@/lib/utils'

/**
 * Régua de atraso.
 *
 * Substitui os três cartões de resumo das Cobranças. O saldo em aberto vira o
 * número principal e o aging — que antes era uma listinha espremida dentro de
 * um cartão — vira a régua: uma coluna por faixa, altura proporcional. É o que
 * responde "há quanto tempo esse dinheiro está parado", que é a pergunta real.
 *
 * Faixa zerada não some: fica como um traço no zero, para a régua continuar
 * legível e a ausência ser visível.
 */

export type AgingTone = 'neutral' | 'info' | 'warning' | 'critical'

const TOM: Record<AgingTone, { bar: string; text: string }> = {
  neutral: { bar: 'var(--neutral-track)', text: 'text-muted-foreground' },
  info: { bar: 'var(--brand-300)', text: 'text-foreground' },
  warning: { bar: 'var(--chart-6)', text: 'text-foreground' },
  critical: { bar: 'var(--critical)', text: 'text-critical' },
}

export interface AgingColumn {
  label: string
  amount: number
  /** Valor já formatado — a formatação de moeda é do domínio, não daqui. */
  formatted: string
  tone?: AgingTone
}

interface AgingRulerProps {
  headline: string
  headlineLabel: string
  /** Cor do número principal. */
  headlineTone?: 'critical' | 'positive' | 'default'
  badge?: React.ReactNode
  caption?: string
  columnsLabel?: string
  columns: AgingColumn[]
  className?: string
}

const ALTURA_MAXIMA = 52

export function AgingRuler({
  headline,
  headlineLabel,
  headlineTone = 'default',
  badge,
  caption,
  columnsLabel = 'Distribuição por faixa de atraso',
  columns,
  className,
}: AgingRulerProps) {
  const maior = columns.reduce((m, c) => Math.max(m, c.amount), 0)

  return (
    <div
      className={cn(
        'bg-card border-border flex flex-col gap-6 rounded-2xl border p-6 lg:flex-row lg:items-center lg:gap-8',
        className,
      )}
    >
      <div className="lg:w-64 lg:shrink-0">
        <p className="text-muted-foreground text-xs font-semibold">{headlineLabel}</p>
        <p
          className={cn(
            'font-display text-4xl leading-tight font-bold tracking-tight',
            headlineTone === 'critical' && 'text-critical',
            headlineTone === 'positive' && 'text-positive',
          )}
        >
          {headline}
        </p>
        {(badge || caption) && (
          <div className="mt-2.5 flex flex-wrap items-center gap-2">
            {badge}
            {caption && <span className="text-muted-foreground text-xs">{caption}</span>}
          </div>
        )}
      </div>

      <div className="bg-hairline hidden w-px self-stretch lg:block" />

      <div className="min-w-0 flex-1">
        <p className="text-muted-foreground mb-3.5 text-xs font-semibold">{columnsLabel}</p>
        <div className="flex items-end gap-4">
          {columns.map((col) => {
            const tone = col.tone ?? 'neutral'
            const vazio = col.amount <= 0 || maior <= 0
            return (
              <div key={col.label} className="flex min-w-0 flex-1 flex-col justify-end gap-2">
                <div
                  className="max-w-28 rounded-md"
                  style={{
                    height: vazio ? 4 : Math.max(6, (col.amount / maior) * ALTURA_MAXIMA),
                    backgroundColor: vazio ? 'var(--hairline)' : TOM[tone].bar,
                  }}
                />
                <span
                  className={cn(
                    'truncate text-xs',
                    vazio ? 'text-muted-foreground' : 'text-foreground font-semibold',
                  )}
                >
                  {col.label}
                </span>
                <span
                  className={cn(
                    'truncate text-sm font-semibold',
                    vazio ? 'text-muted-foreground' : TOM[tone].text,
                  )}
                >
                  {col.formatted}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
