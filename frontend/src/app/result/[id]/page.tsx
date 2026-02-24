'use client'
import { useEffect, useState } from 'react'
import { useParams, useSearchParams, useRouter } from 'next/navigation'
import { getClaimResult, getPdfUrl, ClaimResult } from '@/lib/api'
import { translations, Lang } from '@/lib/i18n'
import { suggestionStyle, scoreColor } from '@/lib/utils'
import Navbar from '@/components/Navbar'
import ScoreGauge from '@/components/ScoreGauge'
import ScoreBreakdownPanel from '@/components/ScoreBreakdownPanel'
import FlagsPanel from '@/components/FlagsPanel'
import ActionChecklist from '@/components/ActionChecklist'
import FeedbackModal from '@/components/FeedbackModal'

const FIELD_LABELS: Record<string, { de: string; en: string }> = {
  schadennummer:             { de: 'Schadennummer',             en: 'Claim Number' },
  schadensdatum:             { de: 'Schadendatum',              en: 'Incident Date' },
  meldedatum:                { de: 'Meldedatum',                en: 'Report Date' },
  kennzeichen:               { de: 'Kennzeichen',               en: 'License Plate' },
  fahrzeugmarke:             { de: 'Fahrzeugmarke',             en: 'Vehicle Make' },
  fahrzeugmodell:            { de: 'Fahrzeugmodell',            en: 'Vehicle Model' },
  fahrgestellnummer:         { de: 'Fahrgestellnummer',         en: 'VIN / Chassis No.' },
  versicherungsnehmer:       { de: 'Versicherungsnehmer',       en: 'Policyholder' },
  geschaedigter:             { de: 'Geschädigter',              en: 'Injured Party' },
  kennzeichen_unfallgegner:  { de: 'Kennzeichen Unfallgegner',  en: 'Other Vehicle Plate' },
  schadenshoehe:             { de: 'Schadenshöhe',              en: 'Claim Amount' },
  selbstbeteiligung:         { de: 'Selbstbeteiligung',         en: 'Deductible' },
  versicherungsscheinnummer: { de: 'Vers.-Scheinnummer',        en: 'Policy Number' },
  versicherungsgesellschaft: { de: 'Versicherungsgesellschaft', en: 'Insurer' },
  unfallort:                 { de: 'Unfallort',                 en: 'Location' },
  unfallhergang:             { de: 'Unfallhergang',             en: 'Incident Description' },
  polizeilich_aufgenommen:   { de: 'Polizeilich aufgenommen',   en: 'Police Report Filed' },
  polizeibericht_nummer:     { de: 'Polizeibericht-Nr.',        en: 'Police Report No.' },
}

const DELAY_CLASS: Record<number, string> = {
  0:   '',
  60:  '[animation-delay:60ms]',
  120: '[animation-delay:120ms]',
  180: '[animation-delay:180ms]',
  240: '[animation-delay:240ms]',
  300: '[animation-delay:300ms]',
  340: '[animation-delay:340ms]',
}

function Card({ children, className = '', delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  return (
    <div className={`bg-white rounded-2xl shadow-card border border-gray-100 animate-fade-up ${DELAY_CLASS[delay] ?? ''} ${className}`}>
      {children}
    </div>
  )
}

export default function ResultPage() {
  const { id } = useParams<{ id: string }>()
  const searchParams = useSearchParams()
  const router = useRouter()

  const [lang, setLang] = useState<Lang>((searchParams.get('lang') as Lang) || 'de')
  const t = translations[lang]

  const [claim, setClaim] = useState<ClaimResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showFeedback, setShowFeedback] = useState(false)
  const [pdfLoading, setPdfLoading] = useState(false)

  useEffect(() => {
    if (!id) return
    getClaimResult(id)
      .then(setClaim)
      .catch(() => setError('Ergebnis konnte nicht geladen werden.'))
      .finally(() => setLoading(false))
  }, [id])

  const handleDownloadPdf = async () => {
    if (!id) return
    setPdfLoading(true)
    try {
      const url = getPdfUrl(id)
      const a = document.createElement('a')
      a.href = url
      a.download = `ClaimIQ_Schaden_${id.slice(0, 8)}.pdf`
      a.click()
    } finally {
      setPdfLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="page-bg">
        <Navbar lang={lang} onToggle={() => setLang(l => l === 'de' ? 'en' : 'de')} />
        <div className="max-w-2xl mx-auto px-4 py-24 text-center">
          <div className="inline-flex flex-col items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-brand-50 border border-brand-100 flex items-center justify-center">
              <div className="w-5 h-5 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
            </div>
            <span className="text-gray-500 font-medium">{t.processingTitle}</span>
          </div>
        </div>
      </div>
    )
  }

  if (error || !claim) {
    return (
      <div className="page-bg">
        <Navbar lang={lang} onToggle={() => setLang(l => l === 'de' ? 'en' : 'de')} />
        <div className="max-w-2xl mx-auto px-4 py-24 text-center space-y-4">
          <p className="text-red-600">{error || t.errorProcessing}</p>
          <button type="button" onClick={() => router.push('/')} className="text-brand-600 underline text-sm">
            {t.newClaim}
          </button>
        </div>
      </div>
    )
  }

  if (claim.status === 'error') {
    return (
      <div className="page-bg">
        <Navbar lang={lang} onToggle={() => setLang(l => l === 'de' ? 'en' : 'de')} />
        <div className="max-w-2xl mx-auto px-4 py-24 text-center space-y-4">
          <div className="text-5xl">⚠️</div>
          <h2 className="text-xl font-bold text-gray-800">{t.errorProcessing}</h2>
          <p className="text-sm text-gray-500 bg-red-50 rounded-xl p-4 border border-red-200">{claim.error_message}</p>
          <button
            type="button"
            onClick={() => router.push('/')}
            className="mt-2 px-6 py-3 bg-brand-600 text-white rounded-xl text-sm font-semibold hover:bg-brand-800"
          >
            {t.newClaim}
          </button>
        </div>
      </div>
    )
  }

  const suggestion = claim.suggestion || 'review'
  const sStyle = suggestionStyle(suggestion)
  const suggestionLabel = { approve: t.suggestionApprove, review: t.suggestionReview, reject: t.suggestionReject }[suggestion] ?? t.suggestionReview
  const summary = lang === 'de' ? (claim.summary_de || claim.summary || '') : (claim.summary || claim.summary_de || '')
  const isMockMode = !claim.ocr_engine && claim.status === 'done'

  const displayFields = Object.entries(claim.structured_data || {})
    .filter(([key, val]) => FIELD_LABELS[key] && val !== null && val !== undefined && val !== '')
    .map(([key, val]) => ({
      label: lang === 'de' ? FIELD_LABELS[key].de : FIELD_LABELS[key].en,
      value: typeof val === 'boolean' ? (val ? (lang === 'de' ? 'Ja' : 'Yes') : (lang === 'de' ? 'Nein' : 'No')) : String(val),
      key,
    }))

  return (
    <div className="page-bg">
      <Navbar lang={lang} onToggle={() => setLang(l => l === 'de' ? 'en' : 'de')} />

      <main className="max-w-2xl mx-auto px-4 py-8 pb-16 space-y-4">

        {/* Mock mode banner */}
        {isMockMode && (
          <div className="animate-fade-up bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm text-amber-700 flex items-center gap-2">
            <span>🧪</span>
            <span>{t.mockModeBanner}</span>
          </div>
        )}

        {/* Header row */}
        <div className="animate-fade-up flex items-center justify-between pt-1">
          <h1 className="text-2xl font-bold text-gray-900">{t.resultsTitle}</h1>
          <span className="text-xs font-medium text-gray-400 bg-white border border-gray-200 rounded-lg px-2.5 py-1 shadow-sm">
            {claim.ocr_engine === 'google_vision' ? t.ocrVision : t.ocrTesseract}
          </span>
        </div>

        {/* Score card */}
        <Card delay={60} className="p-6">
          <div className="flex items-center gap-6">
            <ScoreGauge score={claim.readiness_score ?? 0} />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-400 mb-1">{t.scoreSubtitle}</p>
              <p className={`text-4xl font-extrabold tabular-nums leading-none ${scoreColor(claim.readiness_score ?? 0)}`}>
                {claim.readiness_score ?? '—'}
                <span className="text-xl font-normal text-gray-300 ml-1">/100</span>
              </p>
              <div className={`inline-flex items-center gap-2 mt-3 px-3 py-1.5 rounded-full border text-sm font-semibold
                ${sStyle.bg} ${sStyle.border} ${sStyle.text}`}>
                <span className={`w-2 h-2 rounded-full ${sStyle.dot}`} />
                {suggestionLabel}
              </div>
            </div>
          </div>

          {claim.score_breakdown && (
            <div className="mt-5 pt-5 border-t border-gray-100">
              <ScoreBreakdownPanel breakdown={claim.score_breakdown} lang={lang} />
            </div>
          )}
        </Card>

        {/* Summary */}
        {summary && (
          <Card delay={120} className="p-5">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
              {t.summaryLabel}
            </h3>
            <p className="text-gray-700 leading-relaxed">{summary}</p>
          </Card>
        )}

        {/* Flags */}
        {claim.flags && claim.flags.length > 0 && (
          <Card delay={180} className="p-5">
            <FlagsPanel flags={claim.flags} lang={lang} />
          </Card>
        )}

        {/* Checklist */}
        {claim.action_checklist && claim.action_checklist.length > 0 && (
          <Card delay={240} className="p-5">
            <ActionChecklist items={claim.action_checklist} lang={lang} />
          </Card>
        )}

        {/* Extracted fields */}
        {displayFields.length > 0 && (
          <Card delay={300} className="p-5">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
              {t.extractedDataLabel}
            </h3>
            <div className="divide-y divide-gray-50">
              {displayFields.map(({ key, label, value }) => (
                <div key={key} className="flex gap-3 py-2.5">
                  <span className="text-sm text-gray-400 w-44 shrink-0">{label}</span>
                  <span className="text-sm text-gray-800 font-medium break-words">{value}</span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Action buttons */}
        <div className="flex flex-col sm:flex-row gap-3 pt-2 animate-fade-up [animation-delay:340ms]">
          <button
            type="button"
            onClick={handleDownloadPdf}
            disabled={pdfLoading}
            className="flex-1 flex items-center justify-center gap-2.5 py-3.5 rounded-2xl
              bg-gradient-to-r from-brand-600 to-blue-400 text-white font-semibold
              shadow-glow hover:shadow-glow-lg hover:scale-[1.015] active:scale-[0.99]
              transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:scale-100"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            {pdfLoading ? '...' : t.downloadPdf}
          </button>

          <button
            type="button"
            onClick={() => router.push('/')}
            className="flex-1 py-3.5 rounded-2xl border-2 border-gray-200 bg-white text-gray-600
              font-semibold hover:border-brand-300 hover:text-brand-600 hover:bg-brand-50
              transition-all duration-200"
          >
            {t.newClaim}
          </button>
        </div>

        {/* Feedback */}
        <div className="text-center pb-2">
          <button
            type="button"
            onClick={() => setShowFeedback(true)}
            className="text-sm text-gray-400 hover:text-brand-600 underline"
          >
            {t.feedbackButton}
          </button>
        </div>
      </main>

      {showFeedback && id && (
        <FeedbackModal claimId={id} lang={lang} onClose={() => setShowFeedback(false)} />
      )}
    </div>
  )
}
