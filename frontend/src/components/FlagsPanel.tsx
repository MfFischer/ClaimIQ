'use client'
import { Flag } from '@/lib/api'
import { Lang, translations } from '@/lib/i18n'

interface Props {
  flags: Flag[]
  lang: Lang
}

function flagStyle(severity: string) {
  switch (severity) {
    case 'error':
      return {
        wrap:  'bg-red-50 border-red-200',
        text:  'text-red-700',
        icon: (
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className="shrink-0 mt-0.5">
            <circle cx="7.5" cy="7.5" r="6.5" stroke="#EF4444" strokeWidth="1.4"/>
            <path d="M7.5 4.5v3.5M7.5 10.5h.01" stroke="#EF4444" strokeWidth="1.4" strokeLinecap="round"/>
          </svg>
        ),
      }
    case 'warning':
      return {
        wrap:  'bg-amber-50 border-amber-200',
        text:  'text-amber-700',
        icon: (
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className="shrink-0 mt-0.5">
            <path d="M7.5 1.5l6 11H1.5l6-11z" stroke="#F59E0B" strokeWidth="1.4" strokeLinejoin="round"/>
            <path d="M7.5 6v3M7.5 10.5h.01" stroke="#F59E0B" strokeWidth="1.4" strokeLinecap="round"/>
          </svg>
        ),
      }
    default:
      return {
        wrap:  'bg-blue-50 border-blue-200',
        text:  'text-blue-700',
        icon: (
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className="shrink-0 mt-0.5">
            <circle cx="7.5" cy="7.5" r="6.5" stroke="#3B82F6" strokeWidth="1.4"/>
            <path d="M7.5 7v4M7.5 4.5h.01" stroke="#3B82F6" strokeWidth="1.4" strokeLinecap="round"/>
          </svg>
        ),
      }
  }
}

export default function FlagsPanel({ flags, lang }: Props) {
  const t = translations[lang]
  if (!flags.length) return null

  return (
    <div className="space-y-2.5">
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
        {t.flagsLabel}
      </h3>
      {flags.map((flag, i) => {
        const s = flagStyle(flag.severity)
        const msg = lang === 'de' ? (flag.message_de || flag.message) : (flag.message || flag.message_de)
        return (
          <div key={i} className={`flex items-start gap-2.5 px-3.5 py-3 rounded-xl border ${s.wrap}`}>
            {s.icon}
            <p className={`text-sm leading-relaxed ${s.text}`}>{msg}</p>
          </div>
        )
      })}
    </div>
  )
}
