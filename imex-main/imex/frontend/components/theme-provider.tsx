'use client'

import React from 'react'

interface ThemeProviderProps {
  children: React.ReactNode
  attribute?: string
  defaultTheme?: string
  enableSystem?: boolean
  forcedTheme?: string
}

export function ThemeProvider({
  children,
}: ThemeProviderProps) {
  return <>{children}</>
}
