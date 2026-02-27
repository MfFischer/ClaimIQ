'use client'
import { useState } from 'react'
import { submitFeedback } from '@/lib/api'
import { Lang, translations } from '@/lib/i18n'

interface Props {
  claimId: string
  lang: Lang
  onClose: () => void
}

export default function FeedbackModal({ claimId, lang, onClose }: Props) {
  const t = translations[lang]
  const [field, setField] = useState('')
  const [original, setOriginal] = useState('')
  const [corrected, setCorrected] = useState('')
  const [comment, setComment] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    setLoading(true)
    try {
      await submitFeedback(claimId, {
        field_corrected: field || undefined,
        original_value: original || undefined,
        corrected_value: corrected || undefined,
        general_comment: comment || undefined,
      })
      setSubmitted(true)
      setTimeout(onClose, 1800)
    } catch {
      // silent — don't block user
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 animate-fade-in">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 animate-slide-up">
        {submitted ? (
          <div className="text-center py-6">
            <div className="text-4xl mb-3">✓</div>
            <p className="font-semibold text-green-700">{t.feedbackThanks}</p>
          </div>
        ) : (
          <>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold text-gray-800">{t.feedbackTitle}</h2>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-500 mb-1 block">{t.feedbackField}</label>
                <input
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                  value={field}
                  onChange={e => setField(e.target.value)}
                  placeholder="z.B. kennzeichen"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 mb-1 block">{t.feedbackOriginal}</label>
                <input
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                  value={original}
                  onChange={e => setOriginal(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 mb-1 block">{t.feedbackCorrected}</label>
                <input
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                  value={corrected}
                  onChange={e => setCorrected(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 mb-1 block">{t.feedbackComment}</label>
                <textarea
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 resize-none"
                  rows={2}
                  value={comment}
                  onChange={e => setComment(e.target.value)}
                />
              </div>
            </div>

            <div className="flex gap-2 mt-5">
              <button
                onClick={onClose}
                className="flex-1 py-2 rounded-lg border border-gray-200 text-gray-600 text-sm hover:bg-gray-50"
              >
                {t.feedbackCancel}
              </button>
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-800 disabled:opacity-50"
              >
                {loading ? '...' : t.feedbackSubmit}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
