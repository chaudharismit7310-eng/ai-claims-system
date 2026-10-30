import { useState, useEffect } from 'react'
import axios from 'axios'
import { API_BASE_URL } from './config'
import {
  PieChart, Pie, Cell, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer,
  LabelList
} from 'recharts'

function AnalyticsDashboard() {

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  const token = localStorage.getItem('token')

  useEffect(() => {
    axios.get(`${API_BASE_URL}/claims/analytics/overview`, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(res => {
      setData(res.data)
      setLoading(false)
    })
    .catch(() => setLoading(false))
  }, [token])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-500 border-t-transparent"></div>
      </div>
    )
  }

  if (!data) {
    return <div className="text-center py-12 text-gray-500">Failed to load analytics data.</div>
  }

  // Format currency
  const formatCurrency = (val) => {
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} Lakhs`
    return `₹${val.toLocaleString('en-IN')}`
  }

  // Prepare Chart Data
  const fraudVectorData = [
    { name: 'Recycled Photo (dHash)', value: data.fraud_vector_breakdown.duplicate_dhash },
    { name: 'AI/Stock (CLIP/ELA)', value: data.fraud_vector_breakdown.stock_or_ai_forgery },
    { name: 'Directional Discrepancy', value: data.fraud_vector_breakdown.directional_contradiction },
    { name: 'Inflated Garage Estimate', value: data.fraud_vector_breakdown.inflated_garage_estimate },
  ]

  const statusData = [
    { name: 'Approved', value: data.status_distribution.approved },
    { name: 'Settled Adjusted', value: data.status_distribution.settled_adjusted },
    { name: 'Manual Review', value: data.status_distribution.manual_review },
    { name: 'Rejected', value: data.status_distribution.rejected },
    { name: 'Pending', value: data.status_distribution.pending },
  ].filter(d => d.value > 0)

  const COLORS = ['#10b981', '#f59e0b', '#6366f1', '#ef4444', '#9ca3af']

  return (
    <div className="max-w-7xl mx-auto pb-10">
      
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">
          Executive Underwriting Intelligence
        </h2>
        <p className="text-gray-500 mt-2 font-medium">
          Real-time AI claims portfolio health and fraud prevention analytics.
        </p>
      </div>

      {/* ROW 1: KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* KPI 1 */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10 text-4xl">🛡️</div>
          <p className="text-sm font-semibold text-emerald-600 mb-1 uppercase tracking-wider">Total Fraud Prevented</p>
          <h3 className="text-3xl font-bold text-gray-900 mb-1">
            {formatCurrency(data.total_fraud_loss_prevented)}
          </h3>
          <p className="text-xs text-emerald-500 font-medium">Capital Protected</p>
        </div>

        {/* KPI 2 */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10 text-4xl">⚡</div>
          <p className="text-sm font-semibold text-blue-600 mb-1 uppercase tracking-wider">Avg Adjudication Speed</p>
          <h3 className="text-3xl font-bold text-gray-900 mb-1">
            {data.avg_turnaround_time_seconds}s
          </h3>
          <p className="text-xs text-gray-500 font-medium">vs. 12-Day Industry Survey Delay</p>
        </div>

        {/* KPI 3 */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10 text-4xl">🎯</div>
          <p className="text-sm font-semibold text-purple-600 mb-1 uppercase tracking-wider">Straight-Through Processing</p>
          <h3 className="text-3xl font-bold text-gray-900 mb-1">
            {data.stp_rate.toFixed(1)}%
          </h3>
          <p className="text-xs text-gray-500 font-medium">Automated instant approvals</p>
        </div>

        {/* KPI 4 */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10 text-4xl">📑</div>
          <p className="text-sm font-semibold text-indigo-600 mb-1 uppercase tracking-wider">Total Claims Triaged</p>
          <h3 className="text-3xl font-bold text-gray-900 mb-1">
            {data.total_claims_count.toLocaleString()}
          </h3>
          <p className="text-xs text-gray-500 font-medium">
            Active & Settled Claims
          </p>
        </div>
      </div>

      {/* ROW 2: Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        
        {/* Fraud Attack Vector Bar Chart */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
            <span>🔬</span> Fraud Attack Vector Breakdown
          </h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={fraudVectorData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e7eb" />
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" width={140} tick={{ fontSize: 12, fill: '#4b5563', fontWeight: 500 }} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: '#f3f4f6' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                <Bar dataKey="value" fill="#ef4444" radius={[0, 4, 4, 0]} barSize={24}>
                  <LabelList dataKey="value" position="right" style={{ fill: '#ef4444', fontWeight: 'bold' }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Adjudication Funnel Pie Chart */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
            <span>📊</span> Adjudication Funnel
          </h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={80}
                  outerRadius={110}
                  paddingAngle={5}
                  dataKey="value"
                  stroke="none"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: '12px', fontWeight: 500, color: '#4b5563' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* ROW 3: Portfolio Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-200 bg-gray-50/50">
          <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <span>🏭</span> OEM Vehicle Portfolio Health
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white border-b border-gray-200 text-xs uppercase tracking-wider text-gray-500 font-semibold">
                <th className="py-4 px-6">Brand / Make</th>
                <th className="py-4 px-6 text-center">Total Claims</th>
                <th className="py-4 px-6 text-right">Avg Claim Value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.make_wise_stats.map((makeData, i) => (
                <tr key={i} className="hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-6 font-semibold text-gray-800">{makeData.make}</td>
                  <td className="py-4 px-6 text-center text-gray-600 font-medium">
                    <span className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-xs">
                      {makeData.total_claims}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-right font-medium text-gray-900">
                    {formatCurrency(makeData.avg_claim_amount)}
                  </td>
                </tr>
              ))}
              {data.make_wise_stats.length === 0 && (
                <tr>
                  <td colSpan="3" className="py-8 text-center text-gray-500">
                    No claims portfolio data available yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  )
}

export default AnalyticsDashboard