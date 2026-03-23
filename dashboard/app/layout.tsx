import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'EA Trading Lab — Public Dashboard',
  description: 'An algorithmic forex system being validated in public.',
  openGraph: {
    title: 'EA Trading Lab',
    description: 'An algorithmic forex system being validated in public.',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
