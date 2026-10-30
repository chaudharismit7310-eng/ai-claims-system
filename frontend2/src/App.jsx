import { useState, useEffect } from 'react'
import axios from 'axios'
import Login from './Login'
import SubmitClaim from './SubmitClaim'
import ClaimTracking from './ClaimTracking'
import AgentDashboard from './AgentDashboard'
import AnalyticsDashboard from './AnalyticsDashboard'
import MyVehicles from './MyVehicles'
import AgentVehicleDashboard from './AgentVehicleDashboard'
import AdminPanel from './AdminPanel'
import { API_BASE_URL } from './config'
import './index.css'

// 1. Centralized Axios Instance with Token Interceptor
export const api = axios.create({
  baseURL: API_BASE_URL,
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

function App() {
  // 2. Restore User from LocalStorage on mount
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user')
    return saved ? JSON.parse(saved) : null
  })

  // Helper to determine default tab based on user role
  const getDefaultTab = (role) => {
    if (role === 'admin') return 'admin'
    if (role === 'agent') return 'verify-vehicles'
    return 'vehicles'
  }

  // 3. Restore Active Tab across page refreshes
  const [activeTab, setActiveTab] = useState(() => {
    const savedTab = localStorage.getItem('activeTab')
    if (savedTab) return savedTab
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      try {
        const parsed = JSON.parse(savedUser)
        return getDefaultTab(parsed.role)
      } catch (e) {
        return 'vehicles'
      }
    }
    return 'vehicles'
  })

  // Sync activeTab changes to localStorage
  useEffect(() => {
    if (activeTab) {
      localStorage.setItem('activeTab', activeTab)
    }
  }, [activeTab])

  const handleLogin = (userData) => {
    // Standardize token retrieval (supports access_token or token keys)
    const token = userData.access_token || userData.token

    localStorage.setItem('user', JSON.stringify(userData))
    if (token) {
      localStorage.setItem('token', token)
    }

    setUser(userData)
    const initialTab = getDefaultTab(userData.role)
    setActiveTab(initialTab)
    localStorage.setItem('activeTab', initialTab)
  }

  const handleLogout = () => {
    localStorage.removeItem('user')
    localStorage.removeItem('token')
    localStorage.removeItem('activeTab')

    setUser(null)
    setActiveTab('vehicles')
  }

  if (!user) {
    return <Login onLogin={handleLogin} />
  }

  const tabs = [
    {
      id: 'vehicles',
      label: '🚗 My Vehicles',
      roles: ['customer']
    },
    {
      id: 'submit',
      label: '📋 Submit Claim',
      roles: ['customer']
    },
    {
      id: 'my-claims',
      label: '📁 My Claims',
      roles: ['customer']
    },
    {
      id: 'verify-vehicles',
      label: '🔍 Verify Vehicles',
      roles: ['agent']
    },
    {
      id: 'agent',
      label: '🧑‍⚖️ Agent Dashboard',
      roles: ['agent']
    },
    {
      id: 'analytics',
      label: '📊 Executive Analytics',
      roles: ['agent']
    },
    {
      id: 'admin',
      label: '🛠️ Admin Panel',
      roles: ['admin']
    },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🚗</span>
            <div>
              <h1 className="text-lg font-bold text-gray-800">
                AI Claims Validation System
              </h1>
              <p className="text-xs text-gray-500">
                Insurance Validation Platform
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              👤 <strong>{user.name}</strong>
              <span
                className={`ml-2 px-2 py-0.5 rounded-full text-xs font-medium ${
                  user.role === 'admin'
                    ? 'bg-red-100 text-red-700'
                    : user.role === 'agent'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                {user.role}
              </span>
            </span>

            <button
              onClick={handleLogout}
              className="bg-red-500 hover:bg-red-600 text-white px-4 py-1.5 rounded-lg text-sm transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Tabs */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {tabs
            .filter((t) => t.roles.includes(user.role))
            .map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white shadow'
                    : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
        </div>

        {/* Page Components */}
        {activeTab === 'vehicles' && <MyVehicles />}
        {activeTab === 'submit' && <SubmitClaim />}
        {activeTab === 'my-claims' && <ClaimTracking />}
        {activeTab === 'verify-vehicles' && <AgentVehicleDashboard />}
        {activeTab === 'agent' && <AgentDashboard />}
        {activeTab === 'analytics' && <AnalyticsDashboard />}
        {activeTab === 'admin' && <AdminPanel />}
      </div>
    </div>
  )
}

export default App