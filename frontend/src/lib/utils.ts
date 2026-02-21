import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function scoreColor(score: number): string {
  if (score >= 75) return 'text-green-600'
  if (score >= 50) return 'text-amber-500'
  return 'text-red-500'
}

export function scoreBg(score: number): string {
  if (score >= 75) return 'bg-green-500'
  if (score >= 50) return 'bg-amber-400'
  return 'bg-red-500'
}

export function scoreRing(score: number): string {
  if (score >= 75) return 'stroke-green-500'
  if (score >= 50) return 'stroke-amber-400'
  return 'stroke-red-500'
}

export function suggestionStyle(s: string | null) {
  switch (s) {
    case 'approve': return { bg: 'bg-green-50', border: 'border-green-300', text: 'text-green-700', dot: 'bg-green-500' }
    case 'reject':  return { bg: 'bg-red-50',   border: 'border-red-300',   text: 'text-red-700',   dot: 'bg-red-500' }
    default:        return { bg: 'bg-amber-50',  border: 'border-amber-300', text: 'text-amber-700', dot: 'bg-amber-400' }
  }
}

export function severityStyle(s: string) {
  switch (s) {
    case 'error':   return { bg: 'bg-red-50',   border: 'border-red-200',   text: 'text-red-700',   icon: '●' }
    case 'info':    return { bg: 'bg-blue-50',  border: 'border-blue-200',  text: 'text-blue-700',  icon: 'ℹ' }
    default:        return { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', icon: '▲' }
  }
}

export function getSessionId(): string {
  if (typeof window === 'undefined') return ''
  let id = sessionStorage.getItem('claimiq_session')
  if (!id) {
    id = crypto.randomUUID()
    sessionStorage.setItem('claimiq_session', id)
  }
  return id
}
