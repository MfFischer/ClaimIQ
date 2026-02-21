'use client'
import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useRouter } from 'next/navigation'
import { uploadClaim } from '@/lib/api'
import { getSessionId } from '@/lib/utils'
import { translations, Lang } from '@/lib/i18n'
import Navbar from '@/components/Navbar'

const ACCEPTED = {
  'application/pdf': ['.pdf'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'image/tiff': ['.tiff', '.tif'],
}

export default function UploadPage() {
  const router = useRouter()
  const [lang, setLang] = useState<Lang>('de')
  const t = translations[lang]

  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [step, setStep] = useState(0)

  const steps = [t.processingStep1, t.processingStep2, t.processingStep3, t.processingStep4]

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) { setFile(accepted[0]); setError('') }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
    onDropRejected: (rejects) => {
      const code = rejects[0]?.errors[0]?.code
      setError(code === 'file-too-large' ? t.errorFilesize : t.errorFiletype)
    },
  })

  const handleSubmit = async () => {
    if (!file) return
    setLoading(true); setError(''); setStep(0)
    const interval = setInterval(() =>
      setStep(prev => prev < steps.length - 1 ? prev + 1 : prev), 1200)
    try {
      const result = await uploadClaim(file, getSessionId())
      clearInterval(interval)
      router.push(`/result/${result.claim_id}?lang=${lang}`)
    } catch (e: any) {
      clearInterval(interval)
      setError(e?.response?.data?.detail || t.errorUpload)
      setLoading(false)
    }
  }

  return (
    <>
      <Navbar lang={lang} onToggle={() => setLang(l => l === 'de' ? 'en' : 'de')} />
      <main className="max-w-xl mx-auto px-4 py-12">

        <div className="text-center mb-10 animate-fade-up">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{t.uploadTitle}</h1>
          <p className="text-gray-500">{t.uploadSubtitle}</p>
        </div>

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`relative border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer
            transition-all duration-200
            ${isDragActive
              ? 'border-brand-600 bg-brand-50 scale-[1.01]'
              : file
                ? 'border-green-400 bg-green-50'
                : 'border-gray-200 bg-white hover:border-brand-400 hover:bg-brand-50'
            }`}
        >
          <input {...getInputProps()} />
          {file ? (
            <div className="space-y-2">
              <div className="text-4xl">📄</div>
              <p className="font-semibold text-gray-800 text-sm">{file.name}</p>
              <p className="text-xs text-gray-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              <button onClick={e => { e.stopPropagation(); setFile(null) }}
                className="text-xs text-red-400 hover:text-red-600 underline">
                {lang === 'de' ? 'Entfernen' : 'Remove'}
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="text-5xl">📂</div>
              <p className="font-medium text-gray-600">
                {isDragActive ? t.uploadDropzoneActive : t.uploadDropzone}
              </p>
              <p className="text-xs text-gray-400">{t.uploadFormats}</p>
            </div>
          )}
        </div>

        {/* Processing steps */}
        {loading && (
          <div className="mt-5 bg-white rounded-xl border border-gray-100 p-5 animate-fade-in space-y-3">
            {steps.map((s, i) => (
              <div key={i} className={`flex items-center gap-3 transition-opacity ${i <= step ? 'opacity-100' : 'opacity-30'}`}>
                <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs shrink-0
                  ${i < step ? 'bg-green-500 text-white' : i === step ? 'bg-brand-600 text-white animate-pulse' : 'bg-gray-200'}`}>
                  {i < step ? '✓' : i === step ? '…' : '○'}
                </div>
                <span className={`text-sm ${i <= step ? 'text-gray-800' : 'text-gray-400'}`}>{s}</span>
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 animate-fade-in">
            {error}
          </div>
        )}

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={!file || loading}
          className={`mt-5 w-full py-4 rounded-2xl font-semibold text-white text-base transition-all
            ${!file || loading
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-brand-600 hover:bg-brand-800 shadow-lg shadow-brand-600/20 hover:scale-[1.01]'
            }`}
        >
          {loading ? t.uploadProcessing : t.uploadButton}
        </button>

        <p className="text-center text-xs text-gray-400 mt-4">{t.uploadHint}</p>
      </main>
    </>
  )
}
