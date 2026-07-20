'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { 
  Activity, 
  AlertTriangle, 
  TrendingUp, 
  DollarSign,
  RefreshCw,
  Network,
  FileText,
  Bell
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { useRouter } from 'next/navigation'

const data = [
  { name: 'Jan', risk: 45, events: 12 },
  { name: 'Feb', risk: 52, events: 15 },
  { name: 'Mar', risk: 48, events: 10 },
  { name: 'Apr', risk: 65, events: 22 },
  { name: 'May', risk: 72, events: 28 },
  { name: 'Jun', risk: 58, events: 18 },
]

export function Dashboard() {
  const router = useRouter()
  const [metrics, setMetrics] = useState({
    activeDisruptions: 12,
    riskScore: 72,
    revenueExposure: 45.2,
    alerts: 8
  })

  return (
    <div className="min-h-screen bg-black p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-orange-500 to-orange-300 bg-clip-text text-transparent">
              IMEX
            </h1>
            <p className="text-gray-400 mt-1">Real-Time Supply Chain Intelligence</p>
          </div>
          <div className="flex gap-4">
            <Button variant="outline" className="glass border-orange-500/30 text-orange-500 hover:bg-orange-500/10">
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
            <Button className="bg-orange-600 hover:bg-orange-700 text-white">
              <Bell className="mr-2 h-4 w-4" />
              Alerts
            </Button>
          </div>
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="glass-card fade-in">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-400">Active Disruptions</CardTitle>
              <Activity className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{metrics.activeDisruptions}</div>
              <p className="text-xs text-gray-400 mt-1">+2 since yesterday</p>
            </CardContent>
          </Card>

          <Card className="glass-card fade-in" style={{ animationDelay: '0.1s' }}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-400">Risk Score</CardTitle>
              <AlertTriangle className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{metrics.riskScore}/100</div>
              <p className="text-xs text-orange-500 mt-1">High risk detected</p>
            </CardContent>
          </Card>

          <Card className="glass-card fade-in" style={{ animationDelay: '0.2s' }}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-400">Revenue Exposure</CardTitle>
              <DollarSign className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">${metrics.revenueExposure}M</div>
              <p className="text-xs text-gray-400 mt-1">At risk this quarter</p>
            </CardContent>
          </Card>

          <Card className="glass-card fade-in" style={{ animationDelay: '0.3s' }}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-400">Active Alerts</CardTitle>
              <Bell className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{metrics.alerts}</div>
              <p className="text-xs text-gray-400 mt-1">3 require attention</p>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white">Risk Trend</CardTitle>
            </CardHeader>
            <CardContent className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                  <defs>
                    <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#FF6B00" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#FF6B00" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="name" stroke="#666" />
                  <YAxis stroke="#666" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="risk" 
                    stroke="#FF6B00" 
                    fillOpacity={1}
                    fill="url(#riskGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white">Recent Events</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Alert className="bg-red-900/20 border-red-500/30">
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                  <AlertTitle className="text-red-500">Port of Shanghai Closure</AlertTitle>
                  <AlertDescription className="text-gray-400">
                    Typhoon warning - Estimated 5 days disruption
                  </AlertDescription>
                </Alert>
                <Alert className="bg-orange-900/20 border-orange-500/30">
                  <AlertTriangle className="h-4 w-4 text-orange-500" />
                  <AlertTitle className="text-orange-500">Supplier Strike - Taiwan</AlertTitle>
                  <AlertDescription className="text-gray-400">
                    Semiconductor supplier affected - 3 days
                  </AlertDescription>
                </Alert>
                <Alert className="bg-yellow-900/20 border-yellow-500/30">
                  <AlertTriangle className="h-4 w-4 text-yellow-500" />
                  <AlertTitle className="text-yellow-500">Weather Alert - Rotterdam</AlertTitle>
                  <AlertDescription className="text-gray-400">
                    Storm expected - Monitor port operations
                  </AlertDescription>
                </Alert>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="glass-card cursor-pointer hover:bg-white/5 transition-colors" onClick={() => router.push('/graph')}>
            <CardContent className="p-6 flex items-center gap-4">
              <Network className="h-8 w-8 text-orange-500" />
              <div>
                <h3 className="text-white font-medium">Supply Chain Graph</h3>
                <p className="text-sm text-gray-400">Visualize dependencies</p>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card cursor-pointer hover:bg-white/5 transition-colors" onClick={() => router.push('/risk')}>
            <CardContent className="p-6 flex items-center gap-4">
              <TrendingUp className="h-8 w-8 text-orange-500" />
              <div>
                <h3 className="text-white font-medium">Risk Analysis</h3>
                <p className="text-sm text-gray-400">Assess vulnerabilities</p>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card cursor-pointer hover:bg-white/5 transition-colors" onClick={() => router.push('/reports')}>
            <CardContent className="p-6 flex items-center gap-4">
              <FileText className="h-8 w-8 text-orange-500" />
              <div>
                <h3 className="text-white font-medium">Generate Report</h3>
                <p className="text-sm text-gray-400">PDF executive summary</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
