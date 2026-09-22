import * as React from 'react'

import { cn } from '@/lib/utils'

/**
 * Barra de composição.
 *
 * Substitui a fileira de cartões "Total / Ocupados / Vagos / Manutenção".
 * Quatro caixas de peso igual escondem a relação entre os números: não dá para
 * ver que 10 dos 11 imóveis estão inativos. Aqui há um número principal e uma
 * barra empilhada em que cada fatia é a parte que aquele estado ocupa do todo.
 *
 * Segmentos com valor 0 continuam na legenda (a informação de que está zerado
 * importa) mas não ocupam largura na barra.
 */

export interface CompositionSegment {
  label: string
  value: number
  /** Cor CSS — use os tokens: `var(--brand-600)`, `var(--neutral-track)`… */
  color: string
}

interface CompositionBarProps {
  /** Rótulo do número principal, ex.: "Carteira". */
  label: string
  total: number
  /** Unidade ao lado do total, ex.: "imóveis". */
  unit?: string
  segments: CompositionSegment[]
  /** Bloco opcional à direita, ex.: aluguel contratado. */
  aside?: {
    label: string
    value: string
    caption?: string
  }
  className?: string
}

export function CompositionBar({
  label,
  total,
  unit,
  segments,
  aside,
  className,
}: CompositionBarProps) {
  const soma = segments.reduce((s, seg) => s + seg.value, 0)
  // Sem divisor não há proporção: a barra vira um trilho vazio em vez de
  // dividir por zero e sumir.
  const base = soma > 0 ? soma : 0

  return (
    <div
      className={cn(
        'bg-card border-border flex flex-col gap-6 rounded-2xl border p-6 lg:flex-row lg:items-center lg:gap-8',
        className,
      )}
    >
      <div className="lg:w-40 lg:shrink-0">
        <p className="text-muted-foreground text-xs font-semibold">{label}</p>
        <p className="flex items-baseline gap-2">
          <span className="font-display text-4xl leading-none font-bold tracking-tight">
            {total}
          </span>
          {unit && <span className="text-muted-foreground text-sm">{unit}</span>}
        </p>
      </div>

      <div className="bg-hairline hidden w-px self-stretch lg:block" />

      <div className="flex min-w-0 flex-1 flex-col gap-3">
        <div className="bg-muted flex h-4 overflow-hidden rounded-full">
          {base > 0 &&
            segments
              .filter((seg) => seg.value > 0)
              .map((seg) => (
                <div
                  key={seg.label}
                  style={{
                    width: `${(seg.value / base) * 100}%`,
                    backgroundColor: seg.color,
                  }}
                />
              ))}
        </div>
        <ul className="flex flex-wrap gap-x-7 gap-y-2">
          {segments.map((seg) => (
            <li key={seg.label} className="flex items-center gap-2">
              <span
                className="size-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: seg.color }}
                aria-hidden
              />
              <span className="text-foreground/80 text-sm">{seg.label}</span>
              <span className="text-sm font-bold">{seg.value}</span>
            </li>
          ))}
        </ul>
      </div>

      {aside && (
        <>
          <div className="bg-hairline hidden w-px self-stretch lg:block" />
          <div className="lg:w-40 lg:shrink-0 lg:text-right">
            <p className="text-muted-foreground text-xs font-semibold">{aside.label}</p>
            <p className="text-xl font-bold">{aside.value}</p>
            {aside.caption && (
              <p className="text-muted-foreground text-xs">{aside.caption}</p>
            )}
          </div>
        </>
      )}
    </div>
  )
}
