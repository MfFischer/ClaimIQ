import { Lang } from '@/lib/i18n'

interface Props {
  lang: Lang
  onToggle: () => void
}

export default function Navbar({ lang, onToggle }: Props) {
  return (
    <nav className="sticky top-0 z-50 glass border-b border-white/50 shadow-sm">
      <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">

        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-600 to-blue-400 flex items-center justify-center shadow-sm shrink-0">
            <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
              <path d="M8 1.5L14 4.5V11.5L8 14.5L2 11.5V4.5L8 1.5Z" stroke="white" strokeWidth="1.5" strokeLinejoin="round"/>
              <path d="M8 5.5V10.5M5.5 7L8 5.5L10.5 7" stroke="white" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <span className="gradient-text font-bold text-xl tracking-tight select-none">ClaimIQ</span>
          <span className="hidden sm:flex items-center text-xs font-semibold text-brand-600 bg-brand-50 border border-brand-100 rounded-full px-2.5 py-0.5">
            Kfz Beta
          </span>
        </div>

        {/* Language toggle */}
        <button
          type="button"
          onClick={onToggle}
          className="text-xs font-semibold px-3.5 py-1.5 rounded-lg border border-gray-200 bg-white text-gray-600 hover:bg-brand-50 hover:border-brand-200 hover:text-brand-600"
        >
          {lang === 'de' ? 'EN' : 'DE'}
        </button>
      </div>
    </nav>
  )
}
