'use client'
import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'

// ── Animated counter hook ─────────────────────────────────────────────────────
function useCounter(target: number, duration = 1800, start = false) {
  const [value, setValue] = useState(0)
  useEffect(() => {
    if (!start) return
    let startTime: number
    const step = (timestamp: number) => {
      if (!startTime) startTime = timestamp
      const progress = Math.min((timestamp - startTime) / duration, 1)
      const ease = 1 - Math.pow(1 - progress, 3)
      setValue(Math.floor(ease * target))
      if (progress < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }, [target, duration, start])
  return value
}

// ── Intersection observer hook ────────────────────────────────────────────────
function useInView(threshold = 0.2) {
  const ref = useRef<HTMLDivElement>(null)
  const [inView, setInView] = useState(false)
  useEffect(() => {
    const obs = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) setInView(true) },
      { threshold }
    )
    if (ref.current) obs.observe(ref.current)
    return () => obs.disconnect()
  }, [threshold])
  return { ref, inView }
}

// ── Animated stat card ────────────────────────────────────────────────────────
function StatCard({ value, suffix, label, delay }: {
  value: number; suffix: string; label: string; delay: number
}) {
  const { ref, inView } = useInView(0.1)
  const count = useCounter(value, 1800, inView)
  return (
    <div ref={ref} className="text-center px-4">
      <div className="text-5xl font-extrabold text-white mb-1 tabular-nums">
        {count}{suffix}
      </div>
      <div className="text-brand-200 text-sm font-medium">{label}</div>
    </div>
  )
}

// ── Mini score gauge ──────────────────────────────────────────────────────────
function MiniGauge({ score, color }: { score: number; color: string }) {
  const r = 28
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  return (
    <svg width="72" height="72" viewBox="0 0 72 72">
      <circle cx="36" cy="36" r={r} fill="none" stroke="#E5E7EB" strokeWidth="7" />
      <circle
        cx="36" cy="36" r={r} fill="none" stroke={color} strokeWidth="7"
        strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={offset}
        style={{ transform: 'rotate(-90deg)', transformOrigin: 'center', transition: 'stroke-dashoffset 1.2s ease' }}
      />
      <text x="36" y="41" textAnchor="middle" fontSize="14" fontWeight="700" fill={color}>{score}</text>
    </svg>
  )
}

// ── Processing step ────────────────────────────────────────────────────────────
function ProcessStep({ n, label, sub, active }: {
  n: number; label: string; sub: string; active: boolean
}) {
  return (
    <div className={`flex items-start gap-3 transition-all duration-500 ${active ? 'opacity-100' : 'opacity-25'}`}>
      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5
        ${active ? 'bg-brand-600 text-white' : 'bg-gray-200 text-gray-400'}`}>
        {active ? '✓' : n}
      </div>
      <div>
        <p className={`text-sm font-semibold ${active ? 'text-gray-900' : 'text-gray-400'}`}>{label}</p>
        <p className="text-xs text-gray-400 mt-0.5">{sub}</p>
      </div>
    </div>
  )
}

// ── Animated product mockup ────────────────────────────────────────────────────
function MockResultCard() {
  const [step, setStep] = useState(0)
  const [showResult, setShowResult] = useState(false)

  useEffect(() => {
    const timers = [
      setTimeout(() => setStep(1), 700),
      setTimeout(() => setStep(2), 1500),
      setTimeout(() => setStep(3), 2200),
      setTimeout(() => { setStep(4); setShowResult(true) }, 3100),
    ]
    return () => timers.forEach(clearTimeout)
  }, [])

  return (
    <div className="bg-white rounded-2xl shadow-card-lg border border-gray-100 overflow-hidden w-full max-w-[340px]">
      {/* Titlebar */}
      <div className="bg-gradient-to-r from-brand-800 to-brand-600 px-4 py-3 flex items-center gap-3">
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-400/70" />
          <div className="w-2.5 h-2.5 rounded-full bg-amber-400/70" />
          <div className="w-2.5 h-2.5 rounded-full bg-green-400/70" />
        </div>
        <span className="text-white/80 text-xs font-medium">ClaimIQ — Kfz-Analyse</span>
      </div>

      <div className="p-5 space-y-4 min-h-[320px]">
        {/* Processing steps */}
        {!showResult && (
          <div className="space-y-3.5">
            <ProcessStep n={1} label="Dokument einlesen" sub="PDF · 2.3 MB" active={step >= 1} />
            <ProcessStep n={2} label="OCR-Erkennung (deu+eng)" sub="Tesseract · Konfidenz 87%" active={step >= 2} />
            <ProcessStep n={3} label="KI-Extraktion" sub="Gemini · 18 Felder" active={step >= 3} />
            <ProcessStep n={4} label="Score berechnen" sub="4 Dimensionen analysiert" active={step >= 4} />
          </div>
        )}

        {/* Result */}
        {showResult && (
          <div className="animate-fade-up space-y-4">
            {/* Score row */}
            <div className="flex items-center gap-4">
              <MiniGauge score={82} color="#22C55E" />
              <div>
                <p className="text-[11px] text-gray-400 mb-0.5">Bearbeitungsreife-Score</p>
                <p className="text-2xl font-extrabold text-green-600">82 <span className="text-base text-gray-300 font-normal">/ 100</span></p>
                <span className="inline-flex items-center gap-1.5 mt-1 px-2 py-0.5 rounded-full
                  bg-amber-50 border border-amber-200 text-[11px] text-amber-700 font-semibold">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 inline-block" />
                  Prüfung erforderlich
                </span>
              </div>
            </div>

            {/* Score breakdown bars */}
            <div className="grid grid-cols-2 gap-1.5">
              {[
                { label: 'Vollständigkeit', v: 90, c: 'bg-green-500' },
                { label: 'Konsistenz',      v: 85, c: 'bg-green-500' },
                { label: 'Betrugssignale',  v: 95, c: 'bg-green-500' },
                { label: 'Dokumentation',   v: 60, c: 'bg-amber-400' },
              ].map(({ label, v, c }) => (
                <div key={label} className="bg-gray-50 rounded-lg p-2 border border-gray-100">
                  <div className="flex justify-between mb-1">
                    <span className="text-[9px] text-gray-400 truncate">{label}</span>
                    <span className="text-[9px] font-bold text-gray-600">{v}</span>
                  </div>
                  <div className="h-1.5 bg-gray-200 rounded-full">
                    <div className={`h-1.5 rounded-full ${c} transition-all duration-700`} style={{ width: `${v}%` }} />
                  </div>
                </div>
              ))}
            </div>

            {/* Flag */}
            <div className="flex items-start gap-2 p-2.5 rounded-lg bg-amber-50 border border-amber-200">
              <span className="text-amber-500 text-xs shrink-0">▲</span>
              <p className="text-[11px] text-amber-700 leading-relaxed">
                Kein Gutachten — bei Schaden über 2.000 € empfohlen.
              </p>
            </div>

            {/* Checklist */}
            <div className="space-y-1.5">
              {[
                { t: 'Gutachten anfordern', req: true },
                { t: 'Polizeibericht-Kopie', req: true },
                { t: 'Fotos (mind. 4 Ansichten)', req: false },
              ].map(({ t, req }) => (
                <div key={t} className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full border-2 border-gray-300 shrink-0" />
                  <span className="text-[11px] text-gray-700 flex-1">{t}</span>
                  {req && <span className="text-[9px] text-red-500 font-semibold">Pflicht</span>}
                </div>
              ))}
            </div>

            {/* CTA */}
            <button className="w-full py-2.5 rounded-xl bg-brand-600 text-white text-xs font-bold
              hover:bg-brand-800 transition-colors shadow-sm">
              📄 Schadensübersicht herunterladen
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Feature card ──────────────────────────────────────────────────────────────
function FeatureCard({ icon, title, desc, delay }: {
  icon: string; title: string; desc: string; delay: number
}) {
  const { ref, inView } = useInView(0.1)
  return (
    <div
      ref={ref}
      className={`bg-white rounded-2xl p-6 shadow-card border border-gray-100
        hover:shadow-card-lg hover:-translate-y-1 transition-all duration-300
        ${inView ? 'animate-fade-up' : 'opacity-0'}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="text-3xl mb-4">{icon}</div>
      <h3 className="font-bold text-gray-900 mb-2 text-base">{title}</h3>
      <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
    </div>
  )
}

// ── Timeline step ─────────────────────────────────────────────────────────────
function TimelineStep({ n, title, desc, last = false }: {
  n: number; title: string; desc: string; last?: boolean
}) {
  const { ref, inView } = useInView(0.15)
  return (
    <div ref={ref} className={`flex gap-5 ${inView ? 'animate-fade-up' : 'opacity-0'}`}>
      <div className="flex flex-col items-center">
        <div className="w-10 h-10 rounded-full bg-brand-600 text-white flex items-center
          justify-center font-bold text-sm shrink-0 shadow-glow">
          {n}
        </div>
        {!last && <div className="w-0.5 flex-1 bg-gradient-to-b from-brand-400 to-transparent mt-2 min-h-[40px]" />}
      </div>
      <div className="pb-10">
        <h4 className="font-bold text-gray-900 mb-2 text-base">{title}</h4>
        <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN LANDING PAGE COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════
export default function LandingPage() {
  const [lang, setLang] = useState<'de' | 'en'>('en')
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 30)
    window.addEventListener('scroll', h, { passive: true })
    return () => window.removeEventListener('scroll', h)
  }, [])

  const c = lang === 'en' ? {
    navLinks: [
      { label: 'Features',     href: '#features' },
      { label: 'How it works', href: '#how' },
      { label: 'Tech Stack',   href: '#tech' },
      { label: 'Try it',       href: '/upload' },
    ],
    heroBadge: '🟢 Live now — Motor vehicle claims AI',
    hero1: 'Insurance Claims.',
    hero2: 'Decided in Seconds.',
    heroSub: 'ClaimIQ reads German Kfz claim documents, extracts every field with AI, scores readiness across 4 dimensions, and gives brokers an action checklist — all in under 5 seconds.',
    heroCta: 'Try the App — Free',
    heroLearn: 'Learn more ↓',
    heroHint: 'No account · No API key · Works instantly in demo mode',
    stats: [
      { value: 82, suffix: '%', label: 'Avg. Readiness Score' },
      { value: 5,  suffix: 's', label: 'Avg. processing time' },
      { value: 4,  suffix: 'x', label: 'Faster than manual' },
      { value: 0,  suffix: '€', label: 'Cost to get started' },
    ],
    featHeading: "Everything a broker needs. Nothing they don't.",
    features: [
      { icon: '🎯', title: 'Claim Readiness Score', desc: 'A 0–100 score across completeness, consistency, fraud signals, and documentation. Instantly know if a claim is ready to forward.' },
      { icon: '🤖', title: 'AI Field Extraction',   desc: 'Gemini extracts all Kfz fields — Kennzeichen, Schadenshöhe, VSN, Unfallhergang — from any PDF or scanned image.' },
      { icon: '📋', title: 'Broker Action Checklist', desc: 'Not just a summary — an interactive to-do list of exactly what to request next. Required vs optional, checkable in-app.' },
      { icon: '📄', title: 'Shareable PDF Report',  desc: 'One click downloads a branded Schadensübersicht PDF. Brokers send it to clients. ClaimIQ markets itself with every share.' },
      { icon: '🔍', title: 'Fraud Signal Detection', desc: 'Auto-flags German insurance fraud patterns: claim date = policy start, suspiciously round amounts, late filing without reason.' },
      { icon: '🌐', title: 'German + English UI',   desc: 'Full DE/EN language toggle. Built for German brokers first, with English for international hiring demos.' },
    ],
    howHeading: 'From document to decision in 4 steps',
    steps: [
      { title: 'Upload',       desc: 'Drag and drop any PDF or image. Mobile camera supported. No login — works instantly via anonymous session.' },
      { title: 'OCR Pipeline', desc: 'Tesseract runs first (free, local, German language pack). If confidence is below 80%, Google Vision steps in automatically.' },
      { title: 'AI Analysis',  desc: 'Two Gemini calls: extraction prompt pulls structured Kfz fields, scoring prompt rates quality and generates the action checklist. All in German.' },
      { title: 'Result + PDF', desc: 'Score gauge, 4-dimension breakdown, flags, interactive checklist, and a branded PDF report — ready to share with the insurer.' },
    ],
    techHeading: 'Engineering built for how brokers actually work',
    techSub: 'Every layer chosen for reliability, cost control, and German data-residency compliance — not for trend-chasing.',
    ctaBadge: '🚀 Now in beta — Kfz claims',
    ctaHeading: 'Ready to cut claim processing time in half?',
    ctaSub: 'ClaimIQ is purpose-built for small and mid-sized German insurance brokers. Upload your next Kfz Schadensmeldung and get a structured, decision-ready result in seconds — no setup, no contract, no commitment.',
    ctaBtn1: '⚡ Analyse a claim now',
    ctaBtn2: '📩 Request early access',
    ctaHint: 'Free during beta · GDPR-compliant · No data stored after session',
    footerTagline: '· Kfz claims intelligence for German insurance brokers',
    footerLinks: ['Features', 'How it works', 'Open App'],
    footerNote: '© 2025 ClaimIQ · GDPR-compliant · Germany',
  } : {
    navLinks: [
      { label: 'Funktionen',      href: '#features' },
      { label: 'So funktioniert\'s', href: '#how' },
      { label: 'Tech-Stack',      href: '#tech' },
      { label: 'Ausprobieren',    href: '/upload' },
    ],
    heroBadge: '🟢 Jetzt live — Kfz-Schadenanalyse mit KI',
    hero1: 'Kfz-Schäden.',
    hero2: 'In Sekunden entschieden.',
    heroSub: 'ClaimIQ liest deutsche Kfz-Schadenformulare, extrahiert alle Felder per KI, bewertet die Bearbeitungsreife in 4 Dimensionen und erstellt eine Aktionsliste — in unter 5 Sekunden.',
    heroCta: 'App kostenlos testen',
    heroLearn: 'Mehr erfahren ↓',
    heroHint: 'Kein Konto · Kein API-Key · Im Demo-Modus sofort nutzbar',
    stats: [
      { value: 82, suffix: '%', label: 'Ø Bearbeitungsreife-Score' },
      { value: 5,  suffix: 's', label: 'Ø Verarbeitungszeit' },
      { value: 4,  suffix: 'x', label: 'Schneller als manuelle Prüfung' },
      { value: 0,  suffix: '€', label: 'Kosten zum Einstieg' },
    ],
    featHeading: 'Alles was Makler brauchen. Nichts was sie nicht brauchen.',
    features: [
      { icon: '🎯', title: 'Bearbeitungsreife-Score',  desc: 'Ein 0–100-Score über Vollständigkeit, Konsistenz, Betrugssignale und Dokumentation. Sofort sehen ob der Schaden weiterleitungsbereit ist.' },
      { icon: '🤖', title: 'KI-Feldextraktion',        desc: 'Gemini extrahiert alle Kfz-Felder — Kennzeichen, Schadenshöhe, VSN, Unfallhergang — aus jeder PDF oder gescannten Datei.' },
      { icon: '📋', title: 'Makler-Aktionsliste',      desc: 'Keine reine Zusammenfassung — eine interaktive To-Do-Liste mit genau dem was als nächstes angefordert werden muss.' },
      { icon: '📄', title: 'Teilbarer PDF-Bericht',    desc: 'Ein Klick lädt eine Schadensübersicht-PDF herunter. Makler senden sie an Kunden. ClaimIQ vermarktet sich mit jeder Weiterleitung selbst.' },
      { icon: '🔍', title: 'Betrugshinweis-Erkennung', desc: 'Automatische Flags bei deutschen Betrugsmustern: Schadendatum = Policenbeginn, runde Beträge ohne Gutachten, späte Meldung.' },
      { icon: '🌐', title: 'Deutsch + Englische UI',   desc: 'Vollständiger DE/EN-Umschalter. Primär für den deutschen Maklermarkt, mit Englisch für internationale Demo-Präsentationen.' },
    ],
    howHeading: 'Vom Dokument zur Entscheidung in 4 Schritten',
    steps: [
      { title: 'Hochladen',     desc: 'Drag & Drop jede PDF oder Bilddatei. Kamera-Upload mobil unterstützt. Kein Konto erforderlich — funktioniert sofort per anonymer Session.' },
      { title: 'OCR-Pipeline',  desc: 'Tesseract verarbeitet zuerst (kostenlos, lokal, Deutsches Sprachpaket). Bei Konfidenz unter 80% übernimmt Google Vision automatisch.' },
      { title: 'KI-Analyse',    desc: 'Zwei Gemini-Aufrufe: Extraktions-Prompt holt strukturierte Kfz-Felder, Scoring-Prompt bewertet und erstellt die Aktionsliste — alles auf Deutsch.' },
      { title: 'Ergebnis + PDF', desc: 'Score-Anzeige, 4-Dimensionen-Aufschlüsselung, Hinweise, interaktive Checkliste und Schadensübersicht-PDF — bereit zur Weiterleitung.' },
    ],
    techHeading: 'Technik gebaut für den Makleralltag',
    techSub: 'Jede Schicht gewählt für Zuverlässigkeit, Kostenkontrolle und DSGVO-Konformität — nicht für Technologietrends.',
    ctaBadge: '🚀 Jetzt in der Beta — Kfz-Schäden',
    ctaHeading: 'Bereit die Schadenbearbeitung zu halbieren?',
    ctaSub: 'ClaimIQ ist speziell für kleine und mittelständische Versicherungsmakler in Deutschland entwickelt. Laden Sie Ihre nächste Kfz-Schadensmeldung hoch und erhalten Sie in Sekunden ein strukturiertes, entscheidungsreifes Ergebnis — ohne Setup, ohne Vertrag, ohne Verpflichtung.',
    ctaBtn1: '⚡ Schaden jetzt analysieren',
    ctaBtn2: '📩 Early Access anfragen',
    ctaHint: 'Während der Beta kostenlos · DSGVO-konform · Keine Datenspeicherung nach der Session',
    footerTagline: '· Kfz-Schadensintelligenz für deutsche Versicherungsmakler',
    footerLinks: ['Funktionen', 'So funktioniert\'s', 'App öffnen'],
    footerNote: '© 2025 ClaimIQ · DSGVO-konform · Deutschland',
  }

  return (
    <div className="min-h-screen bg-white overflow-x-hidden">

      {/* ── NAVBAR ─────────────────────────────────────────────────────────── */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300
        ${scrolled ? 'bg-white/95 backdrop-blur-md shadow-sm border-b border-gray-100' : 'bg-transparent'}`}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">

          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <span className={`font-extrabold text-xl tracking-tight transition-colors
              ${scrolled ? 'text-brand-600' : 'text-white'}`}>
              ClaimIQ
            </span>
            <span className={`text-xs rounded-full px-2 py-0.5 font-semibold hidden sm:block transition-all
              ${scrolled
                ? 'border border-brand-200 text-brand-600'
                : 'border border-white/30 text-white/70'}`}>
              Kfz Beta
            </span>
          </div>

          {/* Desktop links */}
          <div className="hidden md:flex items-center gap-6">
            {c.navLinks.slice(0, 3).map(({ label, href }) => (
              <a key={label} href={href}
                className={`text-sm font-medium transition-colors
                  ${scrolled ? 'text-gray-600 hover:text-brand-600' : 'text-white/80 hover:text-white'}`}>
                {label}
              </a>
            ))}
          </div>

          {/* Right controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setLang(l => l === 'de' ? 'en' : 'de')}
              className={`text-xs font-bold border rounded-lg px-2.5 py-1.5 transition-all
                ${scrolled
                  ? 'border-gray-200 text-gray-500 hover:border-brand-400 hover:text-brand-600'
                  : 'border-white/30 text-white/80 hover:border-white hover:text-white'}`}>
              {lang === 'de' ? 'EN' : 'DE'}
            </button>
            <Link href="/upload"
              className="hidden sm:inline-flex items-center px-4 py-2 rounded-xl bg-white text-brand-700
                text-sm font-bold hover:bg-brand-50 transition-all shadow-sm hover:shadow-glow">
              {c.heroCta}
            </Link>
            {/* Hamburger */}
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className={`md:hidden p-1.5 rounded-lg transition-colors
                ${scrolled ? 'text-gray-600' : 'text-white'}`}>
              <div className="space-y-1.5">
                <div className="w-5 h-0.5 bg-current" />
                <div className="w-5 h-0.5 bg-current" />
                <div className="w-5 h-0.5 bg-current" />
              </div>
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="md:hidden bg-white border-t border-gray-100 px-5 py-4 space-y-3 shadow-lg">
            {c.navLinks.map(({ label, href }) => (
              href.startsWith('#')
                ? <a key={label} href={href} onClick={() => setMenuOpen(false)}
                    className="block text-sm font-medium text-gray-700 py-1.5">{label}</a>
                : <Link key={label} href={href} onClick={() => setMenuOpen(false)}
                    className="block text-sm font-medium text-gray-700 py-1.5">{label}</Link>
            ))}
            <Link href="/upload" onClick={() => setMenuOpen(false)}
              className="block text-center mt-2 py-3 rounded-xl bg-brand-600 text-white text-sm font-bold">
              {c.heroCta}
            </Link>
          </div>
        )}
      </nav>

      {/* ── HERO ───────────────────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex items-center overflow-hidden
        bg-gradient-to-br from-brand-900 via-[#0d2d5e] to-brand-700">

        {/* Grid background */}
        <div className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.8) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255,255,255,0.8) 1px, transparent 1px)`,
            backgroundSize: '64px 64px',
          }} />

        {/* Glow orbs */}
        <div className="absolute top-1/3 -left-32 w-[500px] h-[500px] bg-brand-500 rounded-full
          opacity-10 blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-1/4 -right-20 w-80 h-80 bg-blue-400 rounded-full
          opacity-10 blur-3xl animate-pulse-slow" style={{ animationDelay: '2s' }} />

        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 pt-24 pb-32 w-full">
          <div className="grid lg:grid-cols-[1fr_auto] gap-12 xl:gap-20 items-center">

            {/* Copy */}
            <div className="text-white max-w-xl">
              {/* Live badge */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full
                bg-white/10 border border-white/20 text-xs text-white/80 font-medium mb-7
                animate-fade-in backdrop-blur-sm">
                {c.heroBadge}
              </div>

              <h1 className="text-5xl sm:text-6xl xl:text-7xl font-extrabold leading-[1.08] tracking-tight mb-2
                animate-fade-up" style={{ animationDelay: '100ms' }}>
                {c.hero1}
              </h1>
              <h1 className="text-5xl sm:text-6xl xl:text-7xl font-extrabold leading-[1.08] tracking-tight mb-7
                animate-fade-up"
                style={{
                  animationDelay: '200ms',
                  backgroundImage: 'linear-gradient(135deg, #93C5FD 0%, #60A5FA 40%, #BFDBFE 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                }}>
                {c.hero2}
              </h1>

              <p className="text-brand-100/90 text-base sm:text-lg leading-relaxed mb-9 animate-fade-up"
                style={{ animationDelay: '280ms' }}>
                {c.heroSub}
              </p>

              <div className="flex flex-wrap gap-3 mb-5 animate-fade-up" style={{ animationDelay: '360ms' }}>
                <Link href="/upload"
                  className="inline-flex items-center gap-2 px-7 py-3.5 rounded-2xl bg-white
                    text-brand-700 font-extrabold text-base hover:bg-brand-50 transition-all
                    shadow-glow-lg hover:shadow-glow hover:scale-105 active:scale-95">
                  ⚡ {c.heroCta}
                </Link>
                <a href="#how"
                  className="inline-flex items-center gap-2 px-7 py-3.5 rounded-2xl
                    border-2 border-white/25 text-white font-semibold text-base
                    hover:bg-white/10 hover:border-white/40 transition-all">
                  {c.heroLearn}
                </a>
              </div>

              <p className="text-brand-300/80 text-sm animate-fade-in" style={{ animationDelay: '450ms' }}>
                {c.heroHint}
              </p>
            </div>

            {/* Mockup */}
            <div className="flex justify-center lg:justify-end animate-float">
              <MockResultCard />
            </div>
          </div>
        </div>

        {/* Fade to white */}
        <div className="absolute bottom-0 left-0 right-0 h-28 bg-gradient-to-b from-transparent to-white" />
      </section>

      {/* ── STATS ──────────────────────────────────────────────────────────── */}
      <section className="bg-brand-600 py-16">
        <div className="max-w-4xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 divide-x divide-brand-500/50">
            {c.stats.map((s, i) => (
              <StatCard key={i} value={s.value} suffix={s.suffix} label={s.label} delay={i * 150} />
            ))}
          </div>
        </div>
      </section>

      {/* ── FEATURES ───────────────────────────────────────────────────────── */}
      <section id="features" className="py-24 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-14">
            <h2 className="text-4xl font-extrabold text-gray-900 mb-4">{c.featHeading}</h2>
            <div className="w-16 h-1 bg-brand-600 rounded-full mx-auto" />
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {c.features.map((f, i) => (
              <FeatureCard key={i} icon={f.icon} title={f.title} desc={f.desc} delay={i * 70} />
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ───────────────────────────────────────────────────── */}
      <section id="how" className="py-24 bg-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-14">
            <h2 className="text-4xl font-extrabold text-gray-900 mb-4">{c.howHeading}</h2>
            <div className="w-16 h-1 bg-brand-600 rounded-full mx-auto" />
          </div>
          <div className="max-w-xl mx-auto">
            {c.steps.map((s, i) => (
              <TimelineStep key={i} n={i + 1} title={s.title} desc={s.desc}
                last={i === c.steps.length - 1} />
            ))}
          </div>
        </div>
      </section>

      {/* ── TECH STACK ─────────────────────────────────────────────────────── */}
      <section id="tech" className="py-24 bg-brand-900">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-14">
            <h2 className="text-4xl font-extrabold text-white mb-4">{c.techHeading}</h2>
            <p className="text-brand-200 max-w-xl mx-auto text-base">{c.techSub}</p>
          </div>

          {/* Stack cards */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
            {[
              { layer: 'Frontend',  items: ['Next.js 14', 'TypeScript', 'Tailwind CSS', 'PWA / Mobile'], border: 'border-blue-400/25',   bg: 'bg-blue-950/40' },
              { layer: 'Backend',   items: ['Python 3.11', 'FastAPI', 'SQLAlchemy Async', 'Pydantic v2'], border: 'border-green-400/25',  bg: 'bg-green-950/40' },
              { layer: 'AI / OCR',  items: ['Google Gemini', 'Tesseract OCR', 'OpenCV', 'German NLP'],   border: 'border-purple-400/25', bg: 'bg-purple-950/40' },
              { layer: 'Database',  items: ['SQLite (dev)', 'Neon Postgres', 'Alembic migrations', 'Async ORM'], border: 'border-amber-400/25', bg: 'bg-amber-950/40' },
              { layer: 'Storage',   items: ['Local (dev)', 'Cloudflare R2', 'S3-compatible', 'Zero egress fees'], border: 'border-orange-400/25', bg: 'bg-orange-950/40' },
              { layer: 'Deploy',    items: ['VPS + Nginx', 'Docker-ready', 'Railway option', 'GDPR-aware'], border: 'border-teal-400/25',  bg: 'bg-teal-950/40' },
            ].map(({ layer, items, border, bg }) => (
              <div key={layer} className={`rounded-2xl border ${border} ${bg} p-5`}>
                <p className="text-white font-bold text-xs uppercase tracking-widest mb-3">{layer}</p>
                <div className="flex flex-wrap gap-1.5">
                  {items.map(item => (
                    <span key={item} className="text-xs text-white/60 bg-white/8 border border-white/10
                      rounded-full px-2.5 py-0.5">
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Request lifecycle diagram */}
          <div className="bg-black/40 border border-white/10 rounded-2xl p-6 overflow-x-auto">
            <p className="text-green-400/50 text-xs font-mono mb-3"># Request lifecycle</p>
            {[
              { t: 'Browser (Next.js PWA)',                         c: 'text-white' },
              { t: '  └─▶ POST /api/v1/claims/upload',              c: 'text-brand-300' },
              { t: '        └─▶ FastAPI (Python + async)',           c: 'text-white' },
              { t: '              ├─▶ Tesseract OCR  (deu+eng)',     c: 'text-green-300' },
              { t: '              ├─▶ Google Vision  (fallback)',    c: 'text-green-300/60' },
              { t: '              ├─▶ Gemini → extraction (DE)',     c: 'text-purple-300' },
              { t: '              ├─▶ Gemini → scoring (DE)',        c: 'text-purple-300' },
              { t: '              └─▶ SQLite / Neon Postgres',       c: 'text-amber-300' },
              { t: '  ◀─ { score, flags, checklist, suggestion }',  c: 'text-brand-300' },
              { t: '  └─▶ GET /claims/{id}/pdf  →  PDF report',     c: 'text-orange-300' },
            ].map(({ t, c: tc }, i) => (
              <p key={i} className={`text-xs font-mono leading-7 ${tc}`}>{t}</p>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ────────────────────────────────────────────────────────────── */}
      <section id="try" className="py-24 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <div className="inline-block bg-brand-50 border border-brand-100 rounded-full
            px-4 py-1.5 text-sm text-brand-600 font-bold mb-7">
            {c.ctaBadge}
          </div>

          <h2 className="text-4xl sm:text-5xl font-extrabold text-gray-900 mb-6 leading-tight">
            {c.ctaHeading}
          </h2>

          <p className="text-gray-500 text-lg leading-relaxed mb-10 max-w-2xl mx-auto">
            {c.ctaSub}
          </p>

          {/* Trust signals */}
          <div className="flex flex-wrap justify-center gap-6 mb-12">
            {[
              { icon: '🇩🇪', label: lang === 'en' ? 'Built for Germany' : 'Für den deutschen Markt' },
              { icon: '🔒', label: lang === 'en' ? 'GDPR-compliant' : 'DSGVO-konform' },
              { icon: '⚡', label: lang === 'en' ? 'Under 5 seconds' : 'Unter 5 Sekunden' },
              { icon: '📄', label: lang === 'en' ? 'PDF report included' : 'PDF-Bericht inklusive' },
            ].map(({ icon, label }) => (
              <div key={label} className="flex items-center gap-2 text-gray-500 text-sm">
                <span className="text-lg">{icon}</span>
                <span>{label}</span>
              </div>
            ))}
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/upload"
              className="px-9 py-4 rounded-2xl bg-brand-600 text-white font-extrabold text-lg
                hover:bg-brand-800 shadow-glow hover:shadow-glow-lg transition-all hover:scale-105
                active:scale-95">
              {c.ctaBtn1}
            </Link>
            <a
              href={`mailto:afefischer@gmail.com?subject=${encodeURIComponent(
                lang === 'en'
                  ? 'ClaimIQ Early Access Request'
                  : 'ClaimIQ Early Access Anfrage'
              )}&body=${encodeURIComponent(
                lang === 'en'
                  ? 'Hi,\n\nI would like to request early access to ClaimIQ.\n\nName:\nCompany:\nUse case:\n'
                  : 'Hallo,\n\nIch möchte Early Access zu ClaimIQ anfragen.\n\nName:\nUnternehmen:\nAnwendungsfall:\n'
              )}`}
              className="px-9 py-4 rounded-2xl border-2 border-gray-200 text-gray-700 font-bold text-lg
                hover:border-brand-400 hover:text-brand-600 transition-all">
              {c.ctaBtn2}
            </a>
          </div>

          <p className="text-gray-400 text-sm mt-5">{c.ctaHint}</p>
        </div>
      </section>

      {/* ── FOOTER ─────────────────────────────────────────────────────────── */}
      <footer className="bg-gray-50 border-t border-gray-100 py-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row
          items-center justify-between gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-brand-600 font-extrabold text-xl">ClaimIQ</span>
            <span className="text-gray-400">{c.footerTagline}</span>
          </div>
          <div className="flex items-center gap-5">
            {[
              { label: c.footerLinks[0], href: '#features' },
              { label: c.footerLinks[1], href: '#how' },
              { label: c.footerLinks[2], href: '/upload' },
            ].map(({ label, href }) => (
              href.startsWith('#')
                ? <a key={label} href={href} className="text-gray-400 hover:text-brand-600 transition-colors">{label}</a>
                : <Link key={label} href={href} className="text-gray-400 hover:text-brand-600 transition-colors">{label}</Link>
            ))}
          </div>
          <p className="text-xs text-gray-300">{c.footerNote}</p>
        </div>
      </footer>

    </div>
  )
}
