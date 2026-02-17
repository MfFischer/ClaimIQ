import type { Metadata, Viewport } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'ClaimIQ — Kfz-Schadenanalyse',
  description: 'KI-gestützte Analyse von Kfz-Schadensformularen für Versicherungsmakler.',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'ClaimIQ',
  },
}

export const viewport: Viewport = {
  themeColor: '#1A56A0',
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body className="bg-gray-50 min-h-screen antialiased">
        {children}
      </body>
    </html>
  )
}
