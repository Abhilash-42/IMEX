'use client'

import { useState, useEffect } from 'react'
import ReactFlow, { 
  MiniMap, 
  Controls, 
  Background, 
  Node, 
  Edge
} from 'react-flow-renderer'
import { api, Supplier, Component, Product } from '../api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Network, Home, ChevronRight, Activity, ShieldAlert, Award } from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function GraphPage() {
  const router = useRouter()
  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [selectedNode, setSelectedNode] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const suppliers = await api.getSuppliers()
        const products = await api.getProducts()
        
        // Define node list and edge list
        const initialNodes: Node[] = []
        const initialEdges: Edge[] = []

        // Y positioning intervals
        const supplierYStep = 110
        const componentYStep = 100
        const productYStep = 150

        // 1. Add Suppliers (Left Column: X = 100)
        suppliers.forEach((s, idx) => {
          initialNodes.push({
            id: `supplier-${s.id}`,
            type: 'input',
            data: { 
              label: (
                <div className="flex flex-col text-left">
                  <span className="text-[10px] font-bold text-orange-400 tracking-wider uppercase">Supplier</span>
                  <span className="font-semibold text-white text-sm truncate">{s.name}</span>
                  <span className="text-[11px] text-gray-400 mt-1">{s.city}, {s.country}</span>
                  <div className="flex justify-between items-center mt-2 border-t border-white/10 pt-1 text-[10px]">
                    <span className="text-gray-400">Criticality:</span>
                    <span className={`font-bold ${s.criticality_score >= 80 ? 'text-red-400' : 'text-orange-400'}`}>
                      {s.criticality_score}%
                    </span>
                  </div>
                </div>
              ),
              raw: s,
              nodeType: 'supplier'
            },
            position: { x: 80, y: 50 + idx * supplierYStep },
            style: {
              background: 'rgba(255, 107, 0, 0.05)',
              border: s.criticality_score >= 80 ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(251, 146, 60, 0.3)',
              borderRadius: '12px',
              padding: '12px',
              width: 190,
              boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
              color: '#fff'
            }
          })
        })

        // Hardcoded Components (Middle Column: X = 390)
        const components = [
          { id: 1, name: '5nm Silicon Wafers', criticality: 'high', lead_time_days: 45, cost_per_unit: 1200, supplier_id: 2 },
          { id: 2, name: 'GPU Microcontrollers', criticality: 'high', lead_time_days: 60, cost_per_unit: 450, supplier_id: 1 },
          { id: 3, name: 'OLED Panels', criticality: 'medium', lead_time_days: 20, cost_per_unit: 85, supplier_id: 4 },
          { id: 4, name: 'ECU Logic Boards', criticality: 'high', lead_time_days: 35, cost_per_unit: 320, supplier_id: 3 }
        ]

        components.forEach((c, idx) => {
          initialNodes.push({
            id: `component-${c.id}`,
            data: { 
              label: (
                <div className="flex flex-col text-left">
                  <span className="text-[10px] font-bold text-yellow-400 tracking-wider uppercase">Component</span>
                  <span className="font-semibold text-white text-sm truncate">{c.name}</span>
                  <span className="text-[11px] text-gray-400 mt-1">Lead Time: {c.lead_time_days} days</span>
                  <div className="flex justify-between items-center mt-2 border-t border-white/10 pt-1 text-[10px]">
                    <span className="text-gray-400">Cost:</span>
                    <span className="font-bold text-yellow-400">${c.cost_per_unit}</span>
                  </div>
                </div>
              ),
              raw: c,
              nodeType: 'component'
            },
            position: { x: 380, y: 70 + idx * componentYStep },
            style: {
              background: 'rgba(234, 179, 8, 0.05)',
              border: '1px solid rgba(234, 179, 8, 0.3)',
              borderRadius: '12px',
              padding: '12px',
              width: 190,
              boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
              color: '#fff'
            }
          })

          // Connect Supplier -> Component
          initialEdges.push({
            id: `edge-s${c.supplier_id}-c${c.id}`,
            source: `supplier-${c.supplier_id}`,
            target: `component-${c.id}`,
            animated: true,
            arrowHeadType: 'arrowclosed',
            style: { stroke: 'rgba(251, 146, 60, 0.5)', strokeWidth: 1.5 }
          } as any)
        })

        // 3. Add Products (Right Column: X = 680)
        products.forEach((p, idx) => {
          initialNodes.push({
            id: `product-${p.id}`,
            type: 'output',
            data: { 
              label: (
                <div className="flex flex-col text-left">
                  <span className="text-[10px] font-bold text-teal-400 tracking-wider uppercase">Finished Product</span>
                  <span className="font-semibold text-white text-sm truncate">{p.name}</span>
                  <span className="text-[11px] text-gray-400 mt-1">{p.business_unit}</span>
                  <div className="flex justify-between items-center mt-2 border-t border-white/10 pt-1 text-[10px]">
                    <span className="text-gray-400">Monthly Sales:</span>
                    <span className="font-bold text-teal-400">{p.monthly_sales} units</span>
                  </div>
                </div>
              ),
              raw: p,
              nodeType: 'product'
            },
            position: { x: 680, y: 100 + idx * productYStep },
            style: {
              background: 'rgba(20, 184, 166, 0.05)',
              border: '1px solid rgba(20, 184, 166, 0.3)',
              borderRadius: '12px',
              padding: '12px',
              width: 190,
              boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
              color: '#fff'
            }
          })
        })

        // Connect Components -> Products
        // Component 1 (Silicon) used in Product 2 (Server)
        initialEdges.push({
          id: 'edge-c1-p2',
          source: 'component-1',
          target: 'product-2',
          animated: true,
          arrowHeadType: 'arrowclosed',
          style: { stroke: 'rgba(234, 179, 8, 0.5)', strokeWidth: 1.5 }
        } as any)

        // Component 2 (Microcontrollers) used in Product 1 (ECU) and Product 2 (Server)
        initialEdges.push({
          id: 'edge-c2-p1',
          source: 'component-2',
          target: 'product-1',
          animated: true,
          arrowHeadType: 'arrowclosed',
          style: { stroke: 'rgba(234, 179, 8, 0.5)', strokeWidth: 1.5 }
        } as any)
        initialEdges.push({
          id: 'edge-c2-p2',
          source: 'component-2',
          target: 'product-2',
          animated: true,
          arrowHeadType: 'arrowclosed',
          style: { stroke: 'rgba(234, 179, 8, 0.5)', strokeWidth: 1.5 }
        } as any)

        // Component 3 (OLED Panels) used in Product 3 (TV)
        initialEdges.push({
          id: 'edge-c3-p3',
          source: 'component-3',
          target: 'product-3',
          animated: true,
          arrowHeadType: 'arrowclosed',
          style: { stroke: 'rgba(234, 179, 8, 0.5)', strokeWidth: 1.5 }
        } as any)

        // Component 4 (ECU Logic Boards) used in Product 1 (ECU)
        initialEdges.push({
          id: 'edge-c4-p1',
          source: 'component-4',
          target: 'product-1',
          animated: true,
          arrowHeadType: 'arrowclosed',
          style: { stroke: 'rgba(234, 179, 8, 0.5)', strokeWidth: 1.5 }
        } as any)

        setNodes(initialNodes)
        setEdges(initialEdges)
        setLoading(false)
      } catch (err) {
        console.error(err)
        setLoading(false)
      }
    }

    loadData()
  }, [])

  const onNodeClick = (_: any, node: Node) => {
    setSelectedNode(node.data)
  }

  return (
    <div className="min-h-screen bg-black text-white flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-center p-6 border-b border-white/10 glass">
        <div className="flex items-center gap-3">
          <Network className="h-8 w-8 text-orange-500" />
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-500 to-orange-300 bg-clip-text text-transparent">
              Supply Chain Dependency Graph
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">Interactive visual model of materials, suppliers, and products</p>
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

      {/* Main Grid Content */}
      <div className="flex-1 flex flex-col md:flex-row relative">
        {/* React Flow Container */}
        <div className="flex-1 min-h-[500px] md:h-auto bg-[radial-gradient(#1a1a1a_1px,transparent_1px)] [background-size:20px_20px] bg-black">
          {loading ? (
            <div className="flex items-center justify-center h-full text-gray-400">
              Loading dependency graph...
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodeClick={onNodeClick}
              fitView
              attributionPosition="bottom-right"
            >
              <Controls />
              <Background color="#333" gap={20} />
            </ReactFlow>
          )}
        </div>

        {/* Sidebar Details Drawer */}
        <div className="w-full md:w-[350px] border-t md:border-t-0 md:border-l border-white/10 bg-zinc-950 p-6 flex flex-col gap-6 overflow-y-auto">
          <div>
            <h2 className="text-lg font-semibold text-white">Node Inspector</h2>
            <p className="text-xs text-gray-400 mt-1">Select any element in the graph to view properties, dependencies, and operational metrics.</p>
          </div>

          {selectedNode ? (
            <div className="space-y-6 fade-in">
              {/* Type Badge */}
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-bold tracking-wider uppercase px-2 py-1 rounded ${
                  selectedNode.nodeType === 'supplier' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                  selectedNode.nodeType === 'component' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                  'bg-teal-500/20 text-teal-400 border border-teal-500/30'
                }`}>
                  {selectedNode.nodeType} Details
                </span>
              </div>

              {/* Data Layout */}
              {selectedNode.nodeType === 'supplier' && (
                <div className="space-y-4">
                  <h3 className="text-xl font-bold text-white">{selectedNode.raw.name}</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white/5 rounded-xl p-3 border border-white/5">
                      <div className="text-[10px] text-gray-400 flex items-center gap-1">
                        <Activity className="h-3 w-3 text-orange-500" />
                        Criticality
                      </div>
                      <div className="text-xl font-bold text-orange-400 mt-1">{selectedNode.raw.criticality_score}%</div>
                    </div>
                    <div className="bg-white/5 rounded-xl p-3 border border-white/5">
                      <div className="text-[10px] text-gray-400 flex items-center gap-1">
                        <Award className="h-3 w-3 text-orange-500" />
                        Reliability
                      </div>
                      <div className="text-xl font-bold text-orange-400 mt-1">{selectedNode.raw.reliability_score}%</div>
                    </div>
                  </div>
                  <div className="space-y-2 border-t border-white/10 pt-4 text-sm text-gray-300">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Country:</span>
                      <span>{selectedNode.raw.country}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">City:</span>
                      <span>{selectedNode.raw.city}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Status:</span>
                      <span className="text-green-400 font-medium">Active</span>
                    </div>
                  </div>
                </div>
              )}

              {selectedNode.nodeType === 'component' && (
                <div className="space-y-4">
                  <h3 className="text-xl font-bold text-white">{selectedNode.raw.name}</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white/5 rounded-xl p-3 border border-white/5">
                      <div className="text-[10px] text-gray-400">Lead Time</div>
                      <div className="text-lg font-bold text-yellow-400 mt-1">{selectedNode.raw.lead_time_days} Days</div>
                    </div>
                    <div className="bg-white/5 rounded-xl p-3 border border-white/5">
                      <div className="text-[10px] text-gray-400">Unit Cost</div>
                      <div className="text-lg font-bold text-yellow-400 mt-1">${selectedNode.raw.cost_per_unit}</div>
                    </div>
                  </div>
                  <div className="space-y-2 border-t border-white/10 pt-4 text-sm text-gray-300">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Risk Priority:</span>
                      <span className="text-red-400 uppercase font-bold text-xs bg-red-950/30 px-2 py-0.5 rounded border border-red-500/20">
                        {selectedNode.raw.criticality}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {selectedNode.nodeType === 'product' && (
                <div className="space-y-4">
                  <h3 className="text-xl font-bold text-white">{selectedNode.raw.name}</h3>
                  <p className="text-xs text-gray-400 italic bg-white/5 p-3 rounded-lg border border-white/5">
                    "{selectedNode.raw.description}"
                  </p>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white/5 rounded-xl p-3 border border-white/5">
                      <div className="text-[10px] text-gray-400">Unit Price</div>
                      <div className="text-lg font-bold text-teal-400 mt-1">${selectedNode.raw.revenue_per_unit}</div>
                    </div>
                    <div className="bg-white/5 rounded-xl p-3 border border-white/5">
                      <div className="text-[10px] text-gray-400">Monthly Volume</div>
                      <div className="text-lg font-bold text-teal-400 mt-1">{selectedNode.raw.monthly_sales} Units</div>
                    </div>
                  </div>
                  <div className="space-y-2 border-t border-white/10 pt-4 text-sm text-gray-300">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Business Unit:</span>
                      <span>{selectedNode.raw.business_unit}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Est. Monthly Revenue:</span>
                      <span className="font-semibold text-white">
                        ${((selectedNode.raw.revenue_per_unit * selectedNode.raw.monthly_sales) / 1000000).toFixed(2)}M
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center border border-dashed border-white/10 rounded-xl p-6 text-gray-500">
              <ShieldAlert className="h-8 w-8 text-gray-600 mb-2" />
              <p className="text-sm">No node selected</p>
              <p className="text-[11px] mt-1 text-center">Click a node to inspect properties.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
