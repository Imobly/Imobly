import * as React from 'react'

import { cn } from '@/lib/utils'

/**
 * Trilho de métricas.
 *
 * A versão mais enxuta do mesmo princípio: quando os números são poucos e só
 * contextualizam a lista abaixo, eles não precisam de cartão nenhum. Ficam
 * direto sobre o fundo da página, separados por fios, com um fecho de 1px
 * embaixo — hierarquia por posição e peso, não por caixa.
 */

export interface MetricRailItem {
  label: string
  value: React.ReactNode
  /** Cor CSS do ponto que antecede o rótulo. */
  dot?: string
  caption?: string
  tone?: 'default' | 'positive' | 'critical'
}

interface MetricRailProps {
  lead?: { label: string; value: React.ReactNode; unit?: string }
  items: MetricRailItem[]
  /** Barra de proporção opcional à direita, com legenda curta. */
  bar?: { segments: { value: number; color: string }[]; caption?: string }
  className?: string
}

export function MetricRail({ lead, items, bar, className }: MetricRailProps) {
  const soma = bar?.segments.reduce((s, seg) => s + seg.value, 0) ?? 0

  return (
    <div
      className={cn(
        'border-border flex flex-wrap items-center gap-x-7 gap-y-5 border-b pb-5',
        className,
      )}
    >
      {lead && (
        <>
          <div>
            <p className="text-muted-foreground text-xs font-semibold">{lead.label}</p>
            <p className="flex items-baseline gap-1.5">
              <span className="font-display text-3xl leading-tight font-bold tracking-tight">
                {lead.value}
              </span>
              {lead.unit && (
                <span className="text-muted-foreground text-sm">{lead.unit}</span>
              )}
            </p>
          </div>
          <div className="bg-border h-11 w-px" />
        </>
      )}

      {items.map((item, i) => (
        <React.Fragment key={item.label}>
          <div>
            <p className="text-muted-foreground flex items-center gap-2 text-xs font-semibold">
              {item.dot && (
                <span
                  className="size-2 shrink-0 rounded-full"
                  style={{ backgroundColor: item.dot }}
                  aria-hidden
                />
              )}
              {item.label}
            </p>
            <p className="flex items-baseline gap-2">
              <span
                className={cn(
                  'text-xl font-bold',
                  item.tone === 'positive' && 'text-positive',
                  item.tone === 'critical' && 'text-critical',
                )}
              >
                {item.value}
              </span>
              {item.caption && (
                <span className="text-muted-foreground text-sm">{item.caption}</span>
              )}
            </p>
          </div>
          {i < items.length - 1 && <div className="bg-border h-11 w-px" />}
        </React.Fragment>
      ))}

      {bar && (
        <div className="ml-auto w-full sm:w-56">
          <div className="bg-muted flex h-3 overflow-hidden rounded-full">
            {soma > 0 &&
              bar.segments
                .filter((seg) => seg.value > 0)
                .map((seg, i) => (
                  <div
                    key={i}
                    style={{
                      width: `${(seg.value / soma) * 100}%`,
                      backgroundColor: seg.color,
                    }}
                  />
                ))}
          </div>
          {bar.caption && (
            <p className="text-muted-foreground mt-1.5 text-xs">{bar.caption}</p>
          )}
        </div>
      )}
    </div>
  )
}
