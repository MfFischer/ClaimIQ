'use client'
import { useState } from 'react'
import { ChecklistItem } from '@/lib/api'
import { Lang, translations } from '@/lib/i18n'

interface Props {
  items: ChecklistItem[]
  lang: Lang
}

export default function ActionChecklist({ items, lang }: Props) {
  const t = translations[lang]
  const [checked, setChecked] = useState<Set<number>>(new Set())

  const toggle = (i: number) => {
    setChecked(prev => {
      const next = new Set(prev)
      next.has(i) ? next.delete(i) : next.add(i)
      return next
    })
  }

  if (!items.length) return null

  const required = items.filter(x => x.required)
  const optional = items.filter(x => !x.required)
  const total = items.length
  const done = checked.size
  const pct = total ? Math.round((done / total) * 100) : 0

  const renderItem = (item: ChecklistItem, idx: number, globalIdx: number) => {
    const isDone = checked.has(globalIdx)
    const label = lang === 'de' ? (item.item_de || item.item) : (item.item || item.item_de)

    return (
      <button
        key={idx}
        type="button"
        onClick={() => toggle(globalIdx)}
        className={`w-full flex items-start gap-3 px-3.5 py-3 rounded-xl border text-left
          transition-all duration-200
          ${isDone
            ? 'bg-green-50 border-green-200'
            : 'bg-white border-gray-200 hover:border-brand-300 hover:bg-brand-50'
          }`}
      >
        {/* Checkbox circle */}
        <div className={`mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0
          transition-all duration-200
          ${isDone ? 'bg-green-500 border-green-500 scale-110' : 'border-gray-300'}`}
        >
          {isDone && (
            <svg width="9" height="9" viewBox="0 0 9 9" fill="none">
              <path d="M1.5 4.5l2 2 4-4" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          )}
        </div>

        <span className={`text-sm flex-1 leading-snug transition-colors duration-200
          ${isDone ? 'line-through text-gray-400' : 'text-gray-700'}`}
        >
          {label}
        </span>

        {item.required && !isDone && (
          <span className="shrink-0 text-[10px] font-bold uppercase tracking-wide text-red-500 bg-red-50 border border-red-200 rounded px-1.5 py-0.5 mt-0.5">
            {lang === 'de' ? 'Pflicht' : 'Required'}
          </span>
        )}
      </button>
    )
  }

  return (
    <div className="space-y-3">
      {/* Header + progress */}
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
          {t.checklistLabel}
        </h3>
        <span className="text-xs font-semibold text-gray-500 tabular-nums">
          {done}/{total}
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-gray-100 rounded-full overflow-hidden mb-1">
        <div
          className="h-1 bg-gradient-to-r from-brand-600 to-blue-400 rounded-full transition-[width] duration-500 ease-out"
          ref={el => { if (el) el.style.width = `${pct}%` }}
        />
      </div>

      {required.length > 0 && (
        <div className="space-y-2">
          {required.map((item, i) => renderItem(item, i, i))}
        </div>
      )}

      {optional.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-gray-400 uppercase tracking-widest font-semibold pt-1">Optional</p>
          {optional.map((item, i) => renderItem(item, i, required.length + i))}
        </div>
      )}
    </div>
  )
}
