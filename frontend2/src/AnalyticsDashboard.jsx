import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  PieChart, Pie, Cell, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer
} from 'recharts'

function AnalyticsDashboard() {

  const [data, setData] = useState(null)
  const [patterns, setPatterns] = useState(null)
  const [loading, setLoading] = useState(true)

  const token = localStorage.getItem('token')

  useEffect(() => {

    axios.get('http://127.0.0.1:8000/analytics/summary', {
      headers: { Authorization: `Bearer ${token}` }
    }).then(res => {
      setData(res.data)
      setLoading(false)
    })
    .catch(() => setLoading(false))

    axios.get('http://127.0.0.1:8000/analytics/patterns', {
      headers: { Authorization: `Bearer ${token}` }
    }).then(res => setPatterns(res.data))
      .catch(() => {})

  }, [])

  if (loading) {
    return (
      <div className="text-center py-12 text-gray-400">
        Loading analytics...
      </div>
    )
  }

  if (!data) {
    return (
      <div className="text-center py-12 text-gray-400">
        No data found
      </div>
    )
  }

  // Pie chart data
  const decisionData = [
    { name: 'Approved', value: data.approved, color: '#22c55e' },
    { name: 'Rejected', value: data.rejected, color: '#ef4444' },
    { name: 'Partial', value: data.partial, color: '#f59e0b' },
    { name: 'Pending', value: data.pending_review, color: '#8b5cf6' },
  ].filter(d => d.value > 0)

  // Bar chart data — fault breakdown
  const faultData = Object.entries(data.fault_type_breakdown || {}).map(([key, val]) => ({
    name: key.replace('_', ' '),
    count: val
  }))

  // Bar chart data — AI decisions
  const aiData = Object.entries(data.ai_decision_breakdown || {}).map(([key, val]) => ({
    name: key.replace('_suggested', '').replace('_', ' '),
    count: val
  }))

  return (

    <div className="space-y-6">

      <h2 className="text-xl font-bold text-gray-800">
        📊 Analytics Dashboard
      </h2>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">

        {[
          { label: 'Total Claims', value: data.total_claims, color: 'bg-blue-500' },
          { label: 'Approved', value: data.approved, color: 'bg-green-500' },
          { label: 'Rejected', value: data.rejected, color: 'bg-red-500' },
          { label: 'Partial', value: data.partial, color: 'bg-amber-500' },
          { label: 'Pending', value: data.pending_review, color: 'bg-purple-500' },
        ].map(card => (

          <div
            key={card.label}
            className="bg-white rounded-xl border border-gray-100 p-4 text-center shadow-sm"
          >

            <div className={`text-2xl font-bold text-white ${card.color} rounded-lg py-2 mb-2`}>
              {card.value}
            </div>

            <p className="text-xs text-gray-500">
              {card.label}
            </p>

          </div>

        ))}

      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Pie Chart — Claims Decision */}
        <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">

          <h3 className="font-bold text-gray-800 mb-4">
            🎯 Claims by Decision
          </h3>

          {decisionData.length > 0 ? (

            <ResponsiveContainer width="100%" height={250}>

              <PieChart>

                <Pie
                  data={decisionData}
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  dataKey="value"
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                >

                  {decisionData.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}

                </Pie>

                <Tooltip />
                <Legend />

              </PieChart>

            </ResponsiveContainer>

          ) : (

            <div className="text-center py-8 text-gray-400">
              No data yet
            </div>

          )}

        </div>

        {/* Bar Chart — Fault Breakdown */}
        <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">

          <h3 className="font-bold text-gray-800 mb-4">
            ⚠️ Fault Type Breakdown
          </h3>

          {faultData.length > 0 ? (

            <ResponsiveContainer width="100%" height={250}>

              <BarChart data={faultData}>

                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#f0f0f0"
                />

                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11 }}
                />

                <YAxis tick={{ fontSize: 11 }} />

                <Tooltip />

                <Bar
                  dataKey="count"
                  fill="#3b82f6"
                  radius={[4, 4, 0, 0]}
                />

              </BarChart>

            </ResponsiveContainer>

          ) : (

            <div className="text-center py-8 text-gray-400">
              No data yet
            </div>

          )}

        </div>

      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Bar Chart — AI Decisions */}
        <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">

          <h3 className="font-bold text-gray-800 mb-4">
            🤖 AI Decision Breakdown
          </h3>

          {aiData.length > 0 ? (

            <ResponsiveContainer width="100%" height={250}>

              <BarChart data={aiData}>

                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#f0f0f0"
                />

                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 10 }}
                />

                <YAxis tick={{ fontSize: 11 }} />

                <Tooltip />

                <Bar
                  dataKey="count"
                  radius={[4, 4, 0, 0]}
                >

                  {aiData.map((entry, index) => (

                    <Cell
                      key={index}
                      fill={
                        entry.name.includes('approve')
                          ? '#22c55e'
                          : entry.name.includes('reject')
                          ? '#ef4444'
                          : entry.name.includes('partial')
                          ? '#f59e0b'
                          : '#94a3b8'
                      }
                    />

                  ))}

                </Bar>

              </BarChart>

            </ResponsiveContainer>

          ) : (

            <div className="text-center py-8 text-gray-400">
              No data yet
            </div>

          )}

        </div>

        {/* Amount Summary */}
        <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">

          <h3 className="font-bold text-gray-800 mb-4">
            💰 Amount Summary
          </h3>

          <div className="space-y-4">

            <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">

              <span className="text-gray-600 text-sm">
                Total Claimed
              </span>

              <span className="font-bold text-gray-800">
                ₹{data.total_claimed_amount?.toLocaleString('en-IN')}
              </span>

            </div>

            <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">

              <span className="text-gray-600 text-sm">
                Total Approved
              </span>

              <span className="font-bold text-green-600">
                ₹{data.total_approved_amount?.toLocaleString('en-IN')}
              </span>

            </div>

            <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg">

              <span className="text-gray-600 text-sm">
                Savings
              </span>

              <span className="font-bold text-red-600">
                ₹{(
                  data.total_claimed_amount -
                  data.total_approved_amount
                )?.toLocaleString('en-IN')}
              </span>

            </div>

            <div className="flex justify-between items-center p-3 bg-amber-50 rounded-lg">

              <span className="text-gray-600 text-sm">
                Avg Fraud Score
              </span>

              <span className="font-bold text-amber-600">
                {data.avg_fraud_score}
              </span>

            </div>

          </div>

        </div>

      </div>

      {/* Pattern Analysis */}
      {patterns && (

        <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">

          <h3 className="font-bold text-gray-800 mb-4">
            🔍 Claim Pattern Analysis
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

            {/* Suspicious Customers */}
            <div>

              <p className="text-sm font-medium text-gray-600 mb-2">
                ⚠️ Frequent Claimants (
                {Object.keys(patterns.suspicious_customers).length}
                )
              </p>

              {Object.entries(patterns.suspicious_customers).length === 0 ? (

                <p className="text-xs text-gray-400">
                  No suspicious patterns detected
                </p>

              ) : (

                Object.entries(patterns.suspicious_customers)
                  .sort(([, a], [, b]) => b - a)
                  .map(([name, count]) => (

                    <div
                      key={name}
                      className="flex justify-between items-center py-1.5 border-b border-gray-50"
                    >

                      <span className="text-sm text-gray-700">
                        {name}
                      </span>

                      <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded-full text-xs font-medium">
                        {count} claims
                      </span>

                    </div>

                  ))

              )}

            </div>

            {/* High Risk Cities */}
            <div>

              <p className="text-sm font-medium text-gray-600 mb-2">
                📍 High Risk Locations (
                {Object.keys(patterns.high_risk_cities).length}
                )
              </p>

              {Object.entries(patterns.high_risk_cities).length === 0 ? (

                <p className="text-xs text-gray-400">
                  No high risk locations detected
                </p>

              ) : (

                Object.entries(patterns.high_risk_cities)
                  .sort(([, a], [, b]) => b - a)
                  .map(([city, count]) => (

                    <div
                      key={city}
                      className="flex justify-between items-center py-1.5 border-b border-gray-50"
                    >

                      <span className="text-sm text-gray-700">
                        {city}
                      </span>

                      <span className="bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full text-xs font-medium">
                        {count} claims
                      </span>

                    </div>

                  ))

              )}

            </div>

          </div>

        </div>

      )}

    </div>

  )
}

export default AnalyticsDashboard