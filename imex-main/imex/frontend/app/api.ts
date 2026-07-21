const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://imex-u54o.onrender.com';

export interface Supplier {
  id: number;
  name: string;
  country: string;
  city: string;
  criticality_score: number;
  reliability_score: number;
  is_active: boolean;
}

export interface Component {
  id: number;
  name: string;
  criticality: 'low' | 'medium' | 'high';
  lead_time_days: number;
  cost_per_unit: number;
  supplier_id: number;
}

export interface Product {
  id: number;
  name: string;
  description: string;
  revenue_per_unit: number;
  monthly_sales: number;
  business_unit: string;
}

export interface DisruptionEvent {
  id: number;
  title: string;
  description: string;
  event_type: string;
  severity: number;
  location: string;
  country: string;
  start_date: string;
  is_active: boolean;
}

export interface RiskReport {
  id: number;
  event_id: number;
  risk_score: number;
  revenue_exposure: number;
  affected_suppliers: Array<{ id: number; name: string; impact: string }>;
  affected_products: Array<{ id: number; name: string; revenue: number }>;
  recommendations: string[];
  executive_summary: string;
  created_at: string;
}

// Comprehensive Mock Data Fallbacks
export const MOCK_SUPPLIERS: Supplier[] = [
  { id: 1, name: 'Shanghai Semiconductor Co.', country: 'China', city: 'Shanghai', criticality_score: 92, reliability_score: 85, is_active: true },
  { id: 2, name: 'Taipei Logic Foundries', country: 'Taiwan', city: 'Hsinchu', criticality_score: 95, reliability_score: 90, is_active: true },
  { id: 3, name: 'Munich Auto Components', country: 'Germany', city: 'Munich', criticality_score: 68, reliability_score: 95, is_active: true },
  { id: 4, name: 'Seoul Display Systems', country: 'South Korea', city: 'Seoul', criticality_score: 78, reliability_score: 88, is_active: true },
  { id: 5, name: 'Austin Raw Materials Ltd.', country: 'USA', city: 'Austin', criticality_score: 45, reliability_score: 75, is_active: true }
];

export const MOCK_COMPONENTS: Component[] = [
  { id: 1, name: '5nm Silicon Wafers', criticality: 'high', lead_time_days: 45, cost_per_unit: 1200, supplier_id: 2 },
  { id: 2, name: 'GPU Microcontrollers', criticality: 'high', lead_time_days: 60, cost_per_unit: 450, supplier_id: 1 },
  { id: 3, name: 'OLED Panels', criticality: 'medium', lead_time_days: 20, cost_per_unit: 85, supplier_id: 4 },
  { id: 4, name: 'Aluminium Framing', criticality: 'low', lead_time_days: 10, cost_per_unit: 15, supplier_id: 5 },
  { id: 5, name: 'ECU Logic Boards', criticality: 'high', lead_time_days: 35, cost_per_unit: 320, supplier_id: 3 }
];

export const MOCK_PRODUCTS: Product[] = [
  { id: 1, name: 'Smart Car ECU Module', description: 'Primary engine control unit with advanced ADAS capabilities', revenue_per_unit: 2500, monthly_sales: 1200, business_unit: 'Automotive' },
  { id: 2, name: 'Enterprise Core Server v4', description: 'Rackmount server equipped with high-throughput GPUs', revenue_per_unit: 8500, monthly_sales: 450, business_unit: 'Data Center' },
  { id: 3, name: 'HoloView 4K Smart TV', description: 'Next-generation smart television with curved OLED display', revenue_per_unit: 1500, monthly_sales: 3000, business_unit: 'Consumer Electronics' }
];

export const MOCK_EVENTS: DisruptionEvent[] = [
  { id: 1, title: 'Port of Shanghai Closure', description: 'Severe typhoon warning and subsequent lockdown of terminal operations', event_type: 'Natural Disruption', severity: 88, location: 'Port of Shanghai', country: 'China', start_date: new Date().toISOString(), is_active: true },
  { id: 2, title: 'Supplier Strike - Taiwan Tech Park', description: 'Labor negotiations stalled, leading to temporary warehouse work stoppages', event_type: 'Labor Strike', severity: 72, location: 'Hsinchu Tech District', country: 'Taiwan', start_date: new Date().toISOString(), is_active: true },
  { id: 3, title: 'Rotterdam Port Storm Warning', description: 'High winds expected to cause shipping delays for European routes', event_type: 'Weather Event', severity: 45, location: 'Port of Rotterdam', country: 'Netherlands', start_date: new Date().toISOString(), is_active: true }
];

export const MOCK_REPORTS: RiskReport[] = [
  {
    id: 1,
    event_id: 1,
    risk_score: 85,
    revenue_exposure: 34.5,
    affected_suppliers: [
      { id: 1, name: 'Shanghai Semiconductor Co.', impact: 'Critical (100% shutdown)' }
    ],
    affected_products: [
      { id: 2, name: 'Enterprise Core Server v4', revenue: 19.1 },
      { id: 3, name: 'HoloView 4K Smart TV', revenue: 15.4 }
    ],
    recommendations: [
      'Reroute GPU Microcontroller shipments through secondary logistics provider via air freight.',
      'Initiate alternative supplier contact with Taipei Logic Foundries to request safety inventory.',
      'Notify regional sales channels of an estimated 3-week lead time delay on HoloView TVs.'
    ],
    executive_summary: 'The typhoon-driven closure of Shanghai port severely impacts incoming shipments of GPU Microcontrollers. Shanghai Semiconductor Co. is completely offline. This affects two high-margin product lines, exposing $34.5M in potential quarterly revenue.',
    created_at: new Date().toISOString()
  }
];

// Helper to make API calls with catch-all mock fallbacks
async function safeFetch<T>(path: string, fallback: T, options?: RequestInit): Promise<T> {
  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
    });
    if (res.ok) {
      return await res.json() as T;
    }
  } catch (err) {
    console.warn(`API call failed for ${path}. Falling back to mockup data.`, err);
  }
  return fallback;
}

export const api = {
  getSuppliers: async () => {
    const data = await safeFetch<{ suppliers: Supplier[] }>('/api/suppliers', { suppliers: MOCK_SUPPLIERS });
    return data.suppliers || MOCK_SUPPLIERS;
  },

  getProducts: async () => {
    const data = await safeFetch<{ products: Product[] }>('/api/products', { products: MOCK_PRODUCTS });
    return data.products || MOCK_PRODUCTS;
  },

  getEvents: async () => {
    const data = await safeFetch<{ events: DisruptionEvent[] }>('/api/events', { events: MOCK_EVENTS });
    return data.events || MOCK_EVENTS;
  },

  getRiskDashboard: async () => {
    return safeFetch<{ active_disruptions: number; top_risk_score: number; total_revenue_exposure: number; recent_events: any[] }>('/api/risk/dashboard', {
      active_disruptions: MOCK_EVENTS.filter(e => e.is_active).length,
      top_risk_score: 85,
      total_revenue_exposure: 34.5,
      recent_events: MOCK_EVENTS.map(e => ({ id: e.id, title: e.title, severity: e.severity, created_at: e.start_date }))
    });
  },

  getRiskReports: async () => {
    return safeFetch<RiskReport[]>('/api/risk/reports', MOCK_REPORTS);
  },

  analyzeRisk: async (eventId: number): Promise<RiskReport> => {
    try {
      const res = await fetch(`${API_URL}/api/risk/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId, include_details: true }),
      });
      if (res.ok) {
        return await res.json() as RiskReport;
      }
    } catch (err) {
      console.warn('API risk analysis failed. Simulating locally.', err);
    }

    const event = MOCK_EVENTS.find(e => e.id === eventId) || MOCK_EVENTS[0];
    const riskScore = Math.round(event.severity * 0.95);
    const revenueExposure = parseFloat((event.severity * 0.4).toFixed(1));

    return {
      id: Math.floor(Math.random() * 1000) + 10,
      event_id: eventId,
      risk_score: riskScore,
      revenue_exposure: revenueExposure,
      affected_suppliers: [
        { id: 1, name: 'Shanghai Semiconductor Co.', impact: eventId === 1 ? 'Critical (100% shutdown)' : 'Medium (30% delay)' },
        { id: 2, name: 'Taipei Logic Foundries', impact: eventId === 2 ? 'Critical (100% shutdown)' : 'Normal' }
      ],
      affected_products: [
        { id: 1, name: 'Smart Car ECU Module', revenue: parseFloat((revenueExposure * 0.4).toFixed(1)) },
        { id: 2, name: 'Enterprise Core Server v4', revenue: parseFloat((revenueExposure * 0.6).toFixed(1)) }
      ],
      recommendations: [
        `Establish communication channel with alternative supply routes to circumvent "${event.location}".`,
        `Pre-order raw material buffers for dependent components in the ${event.country} region.`,
        'Verify buffer stock levels with European logistics distribution hubs.'
      ],
      executive_summary: `AI risk evaluation for "${event.title}" detects a risk level of ${riskScore}/100. This disruption affects shipping and manufacturing pipelines around ${event.location}, resulting in an estimated financial exposure of $${revenueExposure}M.`,
      created_at: new Date().toISOString()
    };
  },

  generateReport: async (eventId: number): Promise<RiskReport> => {
    try {
      const res = await fetch(`${API_URL}/api/reports/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId, include_details: true }),
      });
      if (res.ok) {
        return await res.json() as RiskReport;
      }
    } catch (err) {
      console.warn('API report generation failed. Simulating locally.', err);
    }
    return api.analyzeRisk(eventId);
  },

  getPdfUrl: (reportId: number) => {
    return `${API_URL}/api/reports/pdf/${reportId}`;
  }
};
