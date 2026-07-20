'use client'

import { useState, useEffect } from 'react'
import { api, DisruptionEvent, RiskReport } from '../api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { FileText, Download, Home, PlusCircle, CheckCircle, ListFilter, Calendar } from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function ReportsPage() {
  const router = useRouter()
  const [reports, setReports] = useState<RiskReport[]>([])
  const [events, setEvents] = useState<DisruptionEvent[]>([])
  const [selectedEventId, setSelectedEventId] = useState<number | ''>('')
  const [generating, setGenerating] = useState(false)
  const [loading, setLoading] = useState(true)

  async function loadData() {
    try {
      const reportList = await api.getRiskReports()
      const eventList = await api.getEvents()
      setReports(reportList)
      setEvents(eventList)
      if (eventList.length > 0) {
        setSelectedEventId(eventList[0].id)
      }
      setLoading(false)
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleGenerateReport = async () => {
    if (!selectedEventId) return
    setGenerating(true)
    try {
      await api.generateReport(Number(selectedEventId))
      // Reload reports lists
      const updatedReports = await api.getRiskReports()
      setReports(updatedReports)
      setGenerating(false)
    } catch (err) {
      console.error(err)
      setGenerating(false)
    }
  }

  return (
    <div className="min-h-screen bg-black text-white p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex justify-between items-center border-b border-white/10 pb-6">
          <div className="flex items-center gap-3">
            <FileText className="h-8 w-8 text-orange-500" />
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-orange-500 to-orange-300 bg-clip-text text-transparent">
                Executive Reports Hub
              </h1>
              <p className="text-gray-400 mt-1">Download and compile audit-ready supply chain risk summaries</p>
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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Compiler Form */}
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-white">Report Compiler</h2>
              <p className="text-xs text-gray-400 mt-1">Trigger PDF generation for active event risk profiles.</p>
            </div>

            <Card className="glass-card p-6 space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Target Event</label>
                <select 
                  value={selectedEventId}
                  onChange={(e) => setSelectedEventId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full bg-zinc-900 border border-white/10 rounded-lg p-3 text-xs text-white focus:outline-none focus:border-orange-500 transition-colors"
                >
                  {events.map((e) => (
                    <option key={e.id} value={e.id}>{e.title}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2 pt-2">
                <div className="text-[10px] text-gray-400 leading-relaxed italic bg-white/5 p-3 rounded-lg border border-white/5">
                  Compilation includes affected entities risk mapping, revenue exposure calculations, and AI recommendations.
                </div>
              </div>

              <Button
                onClick={handleGenerateReport}
                disabled={generating || !selectedEventId}
                className="w-full bg-orange-600 hover:bg-orange-700 text-white font-semibold text-xs py-3 flex items-center justify-center gap-2"
              >
                <PlusCircle className={`h-4 w-4 ${generating ? 'animate-spin' : ''}`} />
                {generating ? 'Compiling Report...' : 'Compile New Report'}
              </Button>
            </Card>
          </div>

          {/* Right Column: Historical reports library */}
          <div className="lg:col-span-2 space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-white">Reports Library</h2>
              <p className="text-xs text-gray-400 mt-1">View and download compiled executive briefs.</p>
            </div>

            {loading ? (
              <div className="text-gray-400 text-sm">Loading reports list...</div>
            ) : reports.length === 0 ? (
              <div className="glass-card h-[250px] flex items-center justify-center text-gray-500 border border-dashed border-white/10 rounded-xl p-6">
                No compiled reports found. Compile one on the left.
              </div>
            ) : (
              <div className="space-y-4">
                {reports.map((report) => {
                  const event = events.find(e => e.id === report.event_id)
                  return (
                    <div 
                      key={report.id}
                      className="glass-card p-5 border border-white/5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 hover:border-orange-500/20 transition-all"
                    >
                      <div className="space-y-1.5 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-sm text-white">
                            {event ? `Risk Briefing: ${event.title}` : `Report Briefing #${report.id}`}
                          </span>
                          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                            report.risk_score >= 70 ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                            'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                          }`}>
                            Risk Score: {report.risk_score}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">
                          {report.executive_summary}
                        </p>
                        <div className="flex gap-4 text-[10px] text-gray-500 pt-1">
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {new Date(report.created_at).toLocaleDateString()}
                          </span>
                          <span>Exposure: ${report.revenue_exposure}M</span>
                        </div>
                      </div>
                      <div className="flex gap-2 w-full md:w-auto">
                        <a 
                          href={api.getPdfUrl(report.id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex-1 md:flex-none text-center bg-zinc-900 border border-white/10 hover:border-orange-500/40 text-gray-300 hover:text-white px-4 py-2.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all"
                        >
                          <Download className="h-3.5 w-3.5 text-orange-500" />
                          PDF
                        </a>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
