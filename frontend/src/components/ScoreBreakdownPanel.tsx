'use client'
import { useEffect, useRef } from 'react'
import { translations, Lang } from '@/lib/i18n'

interface Props {
  breakdown: {
    completeness: number
    consistency: number
    fraud_signals: number
    documentation: number
  }
  lang: Lang
}

function barColor(value: number) {
  if (value >= 75) return 'bg-gradient-to-r from-emerald-400 to-green-500'
  if (value >= 50) return 'bg-gradient-to-r from-amber-400 to-yellow-500'
  return 'bg-gradient-to-r from-red-400 to-rose-500'
}

function valueColor(value: number) {
  if (value >= 75) return 'text-green-600'
  if (value >= 50) return 'text-amber-600'
  return 'text-red-500'
}

const ICONS = ['◈', '⬡', '◉', '◫']

export default function ScoreBreakdown({ breakdown, lang }: Props) {
  const t = translations[lang]
  const barRefs = useRef<(HTMLDivElement | null)[]>([])

  const items = [
    { label: t.scoreCompleteness, value: breakdown.completeness },
    { label: t.scoreConsistency,  value: breakdown.consistency },
    { label: t.scoreFraud,        value: breakdown.fraud_signals },
    { label: t.scoreDocs,         value: breakdown.documentation },
  ]

  useEffect(() => {
    // Imperatively animate widths — avoids JSX style prop lint warning
    const timers = items.map(({ value }, idx) => {
      const el = barRefs.current[idx]
      if (!el) return null
      return setTimeout(() => {
        el.style.width = `${value}%`
      }, 80 + idx * 90)
    })
    return () => { timers.forEach(t => t !== null && clearTimeout(t)) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="grid grid-cols-2 gap-3">
      {items.map(({ label, value }, idx) => (
        <div key={label} className="rounded-xl p-3.5 bg-gray-50 border border-gray-100">
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-1.5 min-w-0">
              <span className="text-gray-300 text-xs leading-none select-none">{ICONS[idx]}</span>
              <span className="text-xs text-gray-500 font-medium truncate">{label}</span>
            </div>
            <span className={`text-sm font-bold tabular-nums shrink-0 ml-1 ${valueColor(value)}`}>
              {value}
            </span>
          </div>
          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              ref={el => { barRefs.current[idx] = el }}
              className={`h-1.5 w-0 rounded-full transition-[width] duration-[850ms] ease-out ${barColor(value)}`}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
