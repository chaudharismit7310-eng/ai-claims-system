import { useState, useEffect } from 'react'
import axios from 'axios'
import { API_BASE_URL } from './config'

function AdminPanel() {
    const [stats, setStats] = useState(null)
    const [users, setUsers] = useState([])
    const [vehicles, setVehicles] = useState([])
    const [claims, setClaims] = useState([])
    const [activeTab, setActiveTab] = useState('dashboard')
    const [loading, setLoading] = useState(true)
    const token = localStorage.getItem('token')

    const headers = { Authorization: `Bearer ${token}` }

    useEffect(() => {
        fetchAll()
    }, [])

    const fetchAll = async () => {
        try {
            const [statsRes, usersRes, vehiclesRes, claimsRes] = await Promise.all([
                axios.get(`${API_BASE_URL}/admin/dashboard`, { headers }),
                axios.get(`${API_BASE_URL}/admin/users`, { headers }),
                axios.get(`${API_BASE_URL}/admin/vehicles`, { headers }),
                axios.get(`${API_BASE_URL}/admin/claims`, { headers }),
            ])
            setStats(statsRes.data)
            setUsers(usersRes.data)
            setVehicles(vehiclesRes.data)
            setClaims(claimsRes.data)
        } catch (err) {
            console.error(err)
        }
        setLoading(false)
    }

    const updateRole = async (userId, role) => {
        try {
            await axios.put(
                `${API_BASE_URL}/admin/users/${userId}/role?role=${role}`,
                {},
                { headers }
            )
            fetchAll()
        } catch { alert('Error updating role!') }
    }

    if (loading) return <div className="text-center py-12 text-gray-400">Loading admin panel...</div>

    const tabs = ['dashboard', 'users', 'vehicles', 'claims']

    return (
        <div>
            <h2 className="text-xl font-bold text-gray-800 mb-4">🛠️ Admin Panel</h2>

            {/* Sub tabs */}
            <div className="flex gap-2 mb-6 flex-wrap">
                {tabs.map(tab => (
                    <button key={tab} onClick={() => setActiveTab(tab)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all ${activeTab === tab ? 'bg-gray-800 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                            }`}>
                        {tab === 'dashboard' ? '📊 Dashboard' :
                            tab === 'users' ? '👥 Users' :
                                tab === 'vehicles' ? '🚗 Vehicles' : '📋 Claims'}
                    </button>
                ))}
            </div>

            {/* Dashboard Stats */}
            {activeTab === 'dashboard' && stats && (
                <div className="space-y-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[
                            { label: 'Total Users', value: stats.total_users, color: 'bg-blue-500' },
                            { label: 'Total Claims', value: stats.total_claims, color: 'bg-purple-500' },
                            { label: 'Total Vehicles', value: stats.total_vehicles, color: 'bg-teal-500' },
                            { label: 'Pending Vehicles', value: stats.pending_vehicles, color: 'bg-yellow-500' },
                            { label: 'Pending Claims', value: stats.pending_claims, color: 'bg-orange-500' },
                            { label: 'Approved Claims', value: stats.approved_claims, color: 'bg-green-500' },
                            { label: 'Rejected Claims', value: stats.rejected_claims, color: 'bg-red-500' },
                        ].map(card => (
                            <div key={card.label} className="bg-white rounded-xl border border-gray-100 p-4 text-center shadow-sm">
                                <div className={`text-2xl font-bold text-white ${card.color} rounded-lg py-2 mb-2`}>
                                    {card.value}
                                </div>
                                <p className="text-xs text-gray-500">{card.label}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Users */}
            {activeTab === 'users' && (
                <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                    <table className="w-full text-sm">
                        <thead className="bg-gray-50 border-b border-gray-100">
                            <tr>
                                <th className="text-left px-4 py-3 text-gray-600 font-medium">ID</th>
                                <th className="text-left px-4 py-3 text-gray-600 font-medium">Name</th>
                                <th className="text-left px-4 py-3 text-gray-600 font-medium">Email</th>
                                <th className="text-left px-4 py-3 text-gray-600 font-medium">Role</th>
                                <th className="text-left px-4 py-3 text-gray-600 font-medium">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(user => (
                                <tr key={user.id} className="border-b border-gray-50 hover:bg-gray-50">
                                    <td className="px-4 py-3 text-gray-500">#{user.id}</td>
                                    <td className="px-4 py-3 font-medium">{user.name}</td>
                                    <td className="px-4 py-3 text-gray-600">{user.email}</td>
                                    <td className="px-4 py-3">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${user.role === 'admin' ? 'bg-red-100 text-red-700' :
                                            user.role === 'agent' ? 'bg-blue-100 text-blue-700' :
                                                'bg-gray-100 text-gray-600'
                                            }`}>
                                            {user.role}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3">
                                        <select
                                            value={user.role}
                                            onChange={e => updateRole(user.id, e.target.value)}
                                            className="text-xs border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                        >
                                            <option value="customer">Customer</option>
                                            <option value="agent">Agent</option>
                                            <option value="admin">Admin</option>
                                        </select>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Vehicles */}
            {activeTab === 'vehicles' && (
                <div className="space-y-3">
                    {vehicles.map(vehicle => (
                        <div key={vehicle.vehicle_id} className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="font-bold text-gray-800">{vehicle.vehicle_number}</p>
                                    <p className="text-sm text-gray-600">{vehicle.car_model} • Policy: {vehicle.policy_number}</p>
                                    <p className="text-xs text-gray-400">User ID: {vehicle.user_id} • Expiry: {vehicle.policy_expiry_date}</p>
                                </div>
                                <span className={`px-3 py-1 rounded-full text-xs font-medium ${vehicle.status === 'verified' ? 'bg-green-100 text-green-700' :
                                    vehicle.status === 'rejected' ? 'bg-red-100 text-red-700' :
                                        'bg-yellow-100 text-yellow-700'
                                    }`}>
                                    {vehicle.status}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Claims */}
            {activeTab === 'claims' && (
                <div className="space-y-3">
                    {claims.map(claim => (
                        <div key={claim.claim_id} className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="font-bold text-gray-800">Claim #{claim.claim_id} — {claim.customer_name}</p>
                                    <p className="text-sm text-gray-600">{claim.car_model} • {claim.city} • ₹{claim.claim_amount?.toLocaleString('en-IN')}</p>
                                    <p className="text-xs text-gray-400">AI: {claim.ai_decision} • Fraud: {claim.fraud_score}</p>
                                </div>
                                <div className="text-right">
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${claim.final_decision === 'approved' ? 'bg-green-100 text-green-700' :
                                        claim.final_decision === 'rejected' ? 'bg-red-100 text-red-700' :
                                            'bg-gray-100 text-gray-600'
                                        }`}>
                                        {claim.final_decision}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default AdminPanel