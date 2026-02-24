'use client'
import { useEffect, useState } from 'react'
import { scoreColor } from '@/lib/utils'

interface Props {
  score: number
}

function getStrokeColor(s: number) {
  if (s >= 75) return '#10B981'
  if (s >= 50) return '#F59E0B'
  return '#EF4444'
}

export default function ScoreGauge({ score }: Props) {
  const radius = 46
  const circumference = 2 * Math.PI * radius
  const [displayScore, setDisplayScore] = useState(0)
  const [offset, setOffset] = useState(circumference)

  useEffect(() => {
    const ringTimer = setTimeout(() => {
      setOffset(circumference - (score / 100) * circumference)
    }, 150)

    const duration = 950
    const steps = 55
    let step = 0
    const counterTimer = setInterval(() => {
      step++
      setDisplayScore(Math.round(Math.min((step / steps) * score, score)))
      if (step >= steps) clearInterval(counterTimer)
    }, duration / steps)

    return () => {
      clearTimeout(ringTimer)
      clearInterval(counterTimer)
    }
  }, [score, circumference])

  const color = getStrokeColor(score)
  const textClass = scoreColor(score)

  return (
    <div className="relative flex items-center justify-center w-[120px] h-[120px]">
      <svg width="120" height="120" viewBox="0 0 120 120" className="gauge-svg">
        <defs>
          <filter id="score-glow" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Track */}
        <circle cx="60" cy="60" r={radius} fill="none" stroke="#F1F5F9" strokeWidth="10" />

        {/* Glow ring */}
        <circle
          cx="60" cy="60" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          opacity="0.25"
          filter="url(#score-glow)"
          className="gauge-ring"
        />

        {/* Main ring */}
        <circle
          cx="60" cy="60" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="gauge-ring"
        />
      </svg>

      <span className={`text-3xl font-bold tabular-nums leading-none ${textClass}`}>
        {displayScore}
      </span>
    </div>
  )
}
