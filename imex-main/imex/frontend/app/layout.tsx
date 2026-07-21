import type { Metadata } from 'next'
import './globals.css'
import { ThemeProvider } from '@/components/theme-provider'
import { QueryProvider } from '@/components/query-provider'
import { Toaster } from '@/components/ui/toaster'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'IMEX - Supply Chain Intelligence',
  description: 'Real-time supply chain disruption intelligence platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans dark bg-black min-h-screen">
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          forcedTheme="dark"
        >
          <QueryProvider>
            <header className="sticky top-0 z-50 w-full border-b border-white/5 bg-black/40 backdrop-blur-md">
              <div className="max-w-7xl mx-auto px-8 h-16 flex items-center justify-between">
                <div className="flex items-center gap-8">
                  <Link href="/" className="font-bold text-lg bg-gradient-to-r from-orange-500 to-orange-300 bg-clip-text text-transparent">
                    IMEX
                  </Link>
                  <nav className="flex items-center gap-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    <Link href="/" className="hover:text-white transition-colors">
                      Dashboard
                    </Link>
                    <Link href="/graph" className="hover:text-white transition-colors">
                      Graph
                    </Link>
                    <Link href="/risk" className="hover:text-white transition-colors">
                      Risk Analysis
                    </Link>
                    <Link href="/reports" className="hover:text-white transition-colors">
                      Reports
                    </Link>
                  </nav>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-wider">Live</span>
                </div>
              </div>
            </header>
            <main>
              {children}
            </main>
            <Toaster />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
