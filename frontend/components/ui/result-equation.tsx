import * as React from 'react'

import { cn } from '@/lib/utils'

/**
 * Equação do resultado.
 *
 * Substitui os três cartões "Receita total / Despesas totais / Lucro" do
 * painel. Três caixas lado a lado escondem que os números são uma conta: a
 * despesa não é um número independente, é o que sai da receita. Aqui as três
 * linhas dividem a mesma escala, então a proporção entre elas é visível — com
 * R$ 1.000 de despesa contra R$ 31.670 de receita, a barra laranja é um risco,
 * e é exatamente isso que o dado diz.
 */

interface ResultEquationProps {
  title?: string
  caption?: string
  revenue: number
  expenses: number
  /** Formatação de moeda vinda da tela (locale do usuário). */
  format: (value: number) => string
  labels?: { revenue?: string; expenses?: string; result?: string }
  className?: string
}

export function ResultEquation({
  title,
  caption,
  revenue,
  expenses,
  format,
  labels,
  className,
}: ResultEquationProps) {
  const result = revenue - expenses
  // A escala é a maior grandeza envolvida; sem receita, nada a normalizar.
  const escala = Math.max(Math.abs(revenue), Math.abs(expenses), Math.abs(result))
  const pct = (v: number) => (escala > 0 ? Math.min(100, (Math.abs(v) / escala) * 100) : 0)
  const margem = revenue > 0 ? (result / revenue) * 100 : null

  return (
    <div className={cn('bg-card border-border rounded-2xl border p-6', className)}>
      {(title || caption) && (
        <div className="mb-4 flex items-center justify-between gap-4">
          {title && (
            <h3 className="text-muted-foreground text-xs font-bold tracking-widest uppercase">
              {title}
            </h3>
          )}
          {caption && (
            <span className="text-muted-foreground ml-auto text-xs">{caption}</span>
          )}
        </div>
      )}

      <div className="flex flex-col gap-4">
        <Linha
          operator=""
          label={labels?.revenue ?? 'Receita'}
          value={format(revenue)}
          width={pct(revenue)}
          color="var(--brand-600)"
        />
        <Linha
          operator="−"
          label={labels?.expenses ?? 'Despesas'}
          value={format(expenses)}
          width={pct(expenses)}
          color="var(--chart-6)"
        />

        <div className="bg-border h-px" />

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
          <span className="text-muted-foreground w-5 shrink-0 text-center text-lg font-bold">=</span>
          <span className="w-24 shrink-0 text-sm font-bold">{labels?.result ?? 'Resultado'}</span>
          <span
            className={cn(
              'font-display shrink-0 text-2xl leading-none font-bold tracking-tight sm:w-36 sm:text-right',
              result >= 0 ? 'text-positive' : 'text-critical',
            )}
          >
            {format(result)}
          </span>
          <span className="bg-muted h-3.5 flex-1 overflow-hidden rounded-full">
            <span
              className="block h-full rounded-full"
              style={{
                width: `${pct(result)}%`,
                backgroundColor: result >= 0 ? 'var(--positive)' : 'var(--critical)',
              }}
            />
          </span>
          {margem !== null && (
            <span
              className={cn(
                'shrink-0 rounded-full px-2.5 py-1 text-xs font-bold',
                result >= 0
                  ? 'bg-positive-soft text-positive-strong'
                  : 'bg-critical-soft text-critical-strong',
              )}
            >
              Margem {margem.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

function Linha({
  operator,
  label,
  value,
  width,
  color,
}: {
  operator: string
  label: string
  value: string
  width: number
  color: string
}) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
      <span className="text-muted-foreground hidden w-5 shrink-0 text-center text-lg font-bold sm:block">
        {operator}
      </span>
      <span className="text-foreground/80 w-24 shrink-0 text-sm">{label}</span>
      <span className="shrink-0 text-base font-semibold sm:w-36 sm:text-right">{value}</span>
      <span className="bg-muted h-3.5 flex-1 overflow-hidden rounded-full">
        <span
          className="block h-full rounded-full"
          style={{ width: `${width}%`, backgroundColor: color }}
        />
      </span>
    </div>
  )
}
