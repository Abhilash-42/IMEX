'use client'

import { useState, useEffect } from 'react'
import { api, DisruptionEvent, RiskReport } from '../api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { 
  TrendingUp, 
  AlertTriangle, 
  Home, 
  RefreshCw, 
  ShieldAlert, 
  CheckCircle,
  FileText,
  DollarSign
} from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function RiskPage() {
  const router = useRouter()
  const [events, setEvents] = useState<DisruptionEvent[]>([])
  const [selectedEvent, setSelectedEvent] = useState<DisruptionEvent | null>(null)
  const [analysisResult, setAnalysisResult] = useState<RiskReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingEvents, setLoadingEvents] = useState(true)

  useEffect(() => {
    async function loadEvents() {
      try {
        const data = await api.getEvents()
        setEvents(data)
        if (data.length > 0) {
          setSelectedEvent(data[0])
        }
        setLoadingEvents(false)
      } catch (err) {
        console.error(err)
        setLoadingEvents(false)
      }
    }
    loadEvents()
  }, [])

  const runAnalysis = async () => {
    if (!selectedEvent) return
    setLoading(true)
    try {
      const result = await api.analyzeRisk(selectedEvent.id)
      setAnalysisResult(result)
      setLoading(false)
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

  // Pre-load default analysis for selected event
  useEffect(() => {
    if (selectedEvent) {
      runAnalysis()
    }
  }, [selectedEvent])

  return (
    <div className="min-h-screen bg-black text-white p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex justify-between items-center border-b border-white/10 pb-6">
          <div className="flex items-center gap-3">
            <TrendingUp className="h-8 w-8 text-orange-500" />
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-orange-500 to-orange-300 bg-clip-text text-transparent">
                Supply Chain Risk Assessment
              </h1>
              <p className="text-gray-400 mt-1">AI-driven predictive impact analysis & recommendations</p>
            </div>
          </div>
          <button 
            onClick={() => router.push('/')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-orange-500/30 text-orange-500 hover:bg-orange-500/10 transition-all text-sm font-medium"
          >
            <Home className="h-4 w-4" />
            Dashboard
          </button>
        </div>

        {/* Layout Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Events List */}
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-white">Active Disruptions</h2>
              <p className="text-xs text-gray-400 mt-1">Select an ongoing event to trigger a predictive risk assessment.</p>
            </div>

            {loadingEvents ? (
              <div className="text-gray-400 text-sm">Loading active events...</div>
            ) : (
              <div className="space-y-4">
                {events.map((e) => {
                  const isSelected = selectedEvent?.id === e.id
                  return (
                    <div 
                      key={e.id}
                      onClick={() => setSelectedEvent(e)}
                      className={`glass-card p-4 cursor-pointer hover:bg-white/5 transition-all border ${
                        isSelected ? 'border-orange-500 bg-orange-500/5' : 'border-white/5'
                      }`}
                    >
                      <div className="flex justify-between items-start gap-2">
                        <span className="font-semibold text-sm text-white">{e.title}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          e.severity >= 80 ? 'bg-red-500/20 text-red-400' :
                          e.severity >= 50 ? 'bg-orange-500/20 text-orange-400' :
                          'bg-yellow-500/20 text-yellow-400'
                        }`}>
                          Sev: {e.severity}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-2 line-clamp-2">{e.description}</p>
                      <div className="flex justify-between items-center text-[10px] text-gray-500 mt-3 pt-2 border-t border-white/5">
                        <span>{e.location}</span>
                        <span>{e.event_type}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Right Two Columns: Analysis Output */}
          <div className="lg:col-span-2 space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold text-white">Analysis Details</h2>
              <Button 
                onClick={runAnalysis}
                disabled={loading || !selectedEvent}
                className="bg-orange-600 hover:bg-orange-700 text-white text-xs font-semibold px-4 py-2 flex items-center gap-2"
              >
                <RefreshCw className={`h-3 w-3 ${loading ? 'animate-spin' : ''}`} />
                Re-Analyze
              </Button>
            </div>

            {loading ? (
              <div className="glass-card h-[400px] flex items-center justify-center text-gray-400">
                Running neural risk mapping model...
              </div>
            ) : analysisResult ? (
              <div className="space-y-6 fade-in">
                {/* Metric Summary Widgets */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Risk Score */}
                  <Card className="glass-card">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-xs text-gray-400 font-semibold tracking-wider uppercase">Neurological Risk Index</CardTitle>
                      <ShieldAlert className="h-4 w-4 text-red-500" />
                    </CardHeader>
                    <CardContent className="pt-2">
                      <div className="flex items-baseline gap-2">
                        <span className="text-4xl font-extrabold text-white">{analysisResult.risk_score}</span>
                        <span className="text-gray-400 text-sm">/ 100</span>
                      </div>
                      {/* Color Bar indicator */}
                      <div className="w-full bg-white/10 h-1.5 rounded-full mt-3 overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${
                            analysisResult.risk_score >= 80 ? 'bg-red-500' :
                            analysisResult.risk_score >= 50 ? 'bg-orange-500' :
                            'bg-yellow-500'
                          }`}
                          style={{ width: `${analysisResult.risk_score}%` }}
                        />
                      </div>
                    </CardContent>
                  </Card>

                  {/* Financial exposure */}
                  <Card className="glass-card">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-xs text-gray-400 font-semibold tracking-wider uppercase">Quarterly Revenue Exposure</CardTitle>
                      <DollarSign className="h-4 w-4 text-green-500" />
                    </CardHeader>
                    <CardContent className="pt-2">
                      <div className="text-4xl font-extrabold text-white">
                        ${analysisResult.revenue_exposure}M
                      </div>
                      <p className="text-xs text-red-400 mt-2 flex items-center gap-1 font-semibold">
                        <AlertTriangle className="h-3 w-3" />
                        Critically exposed pipeline
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* Executive Summary */}
                <Card className="glass-card p-6">
                  <h3 className="font-semibold text-sm text-white mb-2">Executive Impact Summary</h3>
                  <p className="text-xs text-gray-300 leading-relaxed">
                    {analysisResult.executive_summary}
                  </p>
                </Card>

                {/* Breakdown Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Affected Entities */}
                  <Card className="glass-card">
                    <CardHeader>
                      <CardTitle className="text-sm font-semibold text-white">Affected Supply Nodes</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {analysisResult.affected_suppliers.map((s, idx) => (
                        <div key={idx} className="flex justify-between items-center p-2 rounded bg-white/5 border border-white/5">
                          <span className="text-xs text-white font-medium">{s.name}</span>
                          <span className="text-[10px] bg-red-950/40 text-red-400 px-2 py-0.5 rounded font-semibold border border-red-500/10">
                            {s.impact}
                          </span>
                        </div>
                      ))}
                    </CardContent>
                  </Card>

                  {/* Products at Risk */}
                  <Card className="glass-card">
                    <CardHeader>
                      <CardTitle className="text-sm font-semibold text-white">Products at Risk</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {analysisResult.affected_products.map((p, idx) => (
                        <div key={idx} className="flex justify-between items-center p-2 rounded bg-white/5 border border-white/5">
                          <span className="text-xs text-white font-medium">{p.name}</span>
                          <span className="text-[10px] font-bold text-green-400">
                            ${p.revenue}M exposure
                          </span>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </div>

                {/* AI Mitigation Suggestions */}
                <Card className="glass-card p-6">
                  <h3 className="font-semibold text-sm text-white mb-4">Neural Agent Mitigation Recommendations</h3>
                  <div className="space-y-3">
                    {analysisResult.recommendations.map((rec, idx) => (
                      <div key={idx} className="flex items-start gap-3 text-xs text-gray-300">
                        <CheckCircle className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
                        <span>{rec}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            ) : (
              <div className="glass-card h-[400px] flex items-center justify-center text-gray-500 border border-dashed border-white/10 rounded-xl p-6">
                No active event selected.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
