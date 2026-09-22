import * as React from 'react'

import { cn } from '@/lib/utils'

/**
 * Estado como ponto + texto, não como pílula colorida.
 *
 * Quando todo estado é uma pílula preenchida, todos gritam no mesmo volume e
 * o que é crítico deixa de se destacar. Aqui o normal é discreto e só o tom
 * `critical` ganha fundo — é o único que pede ação.
 */

export type StatusTone = 'brand' | 'positive' | 'warning' | 'critical' | 'neutral' | 'info'

const TOM: Record<StatusTone, { dot: string; text: string }> = {
  brand: { dot: 'var(--brand-600)', text: 'text-brand-700' },
  info: { dot: 'var(--brand-300)', text: 'text-foreground/80' },
  positive: { dot: 'var(--positive)', text: 'text-positive' },
  warning: { dot: 'var(--warning)', text: 'text-warning' },
  critical: { dot: 'var(--critical)', text: 'text-critical-strong' },
  neutral: { dot: 'var(--neutral-track)', text: 'text-muted-foreground' },
}

interface StatusDotProps {
  tone?: StatusTone
  children: React.ReactNode
  /** Fundo sólido claro — reserve para o que exige ação. */
  emphasis?: boolean
  className?: string
}

export function StatusDot({
  tone = 'neutral',
  children,
  emphasis = false,
  className,
}: StatusDotProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-2 text-xs font-semibold whitespace-nowrap',
        emphasis && 'rounded-full px-2.5 py-1',
        emphasis && tone === 'critical' && 'bg-critical-soft',
        emphasis && tone === 'warning' && 'bg-warning-soft',
        emphasis && tone === 'positive' && 'bg-positive-soft',
        emphasis && (tone === 'brand' || tone === 'info') && 'bg-brand-50',
        emphasis && tone === 'neutral' && 'bg-muted',
        TOM[tone].text,
        className,
      )}
    >
      <span
        className="size-2 shrink-0 rounded-full"
        style={{ backgroundColor: TOM[tone].dot }}
        aria-hidden
      />
      {children}
    </span>
  )
}
