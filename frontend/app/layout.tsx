import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'OEM Alert | Enterprise Vulnerability Intelligence',
  description: 'Real-time cybersecurity alerts & vulnerability scraper for 24+ Top OEMs. Stop waiting for the NVD.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <div className="bg-glow"></div>
        {children}
      </body>
    </html>
  )
}
