import { useState, useEffect } from 'react'
import axios from 'axios'
import { API_BASE_URL } from './config'

function AgentVehicleDashboard() {
    const [vehicles, setVehicles] = useState([])
    const [selectedVehicle, setSelectedVehicle] = useState(null)
    const [agentNotes, setAgentNotes] = useState('')
    const [loading, setLoading] = useState(true)
    const [message, setMessage] = useState('')
    const token = localStorage.getItem('token')

    useEffect(() => { fetchVehicles() }, [])

    const fetchVehicles = () => {
        axios.get(`${API_BASE_URL}/vehicles/pending`, {
            headers: { Authorization: `Bearer ${token}` }
        }).then(res => { setVehicles(res.data); setLoading(false) })
            .catch(() => setLoading(false))
    }

    const handleAction = async (action) => {
        if (!selectedVehicle) return
        try {
            const formData = new FormData()
            formData.append('action', action)
            formData.append('agent_notes', agentNotes)

            await axios.put(
                `${API_BASE_URL}/vehicles/verify/${selectedVehicle.vehicle_id}`,
                formData,
                { headers: { Authorization: `Bearer ${token}` } }
            )
            setMessage(`✅ Vehicle ${action}!`)
            setSelectedVehicle(null)
            setAgentNotes('')
            fetchVehicles()
        } catch {
            setMessage('❌ Error processing vehicle!')
        }
    }

    const getStatusBadge = (status) => {
        const badges = {
            pending_verification: 'bg-yellow-100 text-yellow-700',
            verified: 'bg-green-100 text-green-700',
            rejected: 'bg-red-100 text-red-700',
        }
        return badges[status] || 'bg-gray-100 text-gray-600'
    }

    if (loading) return <div className="text-center py-12 text-gray-400">Loading...</div>

    return (
        <div>
            <h2 className="text-xl font-bold text-gray-800 mb-4">🚗 Vehicle Verification Dashboard</h2>

            {message && (
                <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4 text-sm">
                    {message}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Left — Pending Vehicles */}
                <div>
                    <h3 className="font-bold text-gray-700 mb-3">⏳ Pending Verification</h3>
                    <div className="space-y-3">
                        {vehicles.map(vehicle => (
                            <div key={vehicle.vehicle_id}
                                onClick={() => { setSelectedVehicle(vehicle); setAgentNotes('') }}
                                className={`bg-white rounded-xl border p-4 cursor-pointer transition-all ${selectedVehicle?.vehicle_id === vehicle.vehicle_id
                                        ? 'border-blue-400 shadow-md'
                                        : 'border-gray-100 hover:border-gray-300'
                                    }`}>
                                <div className="flex items-center justify-between mb-1">
                                    <span className="font-bold text-gray-800">{vehicle.vehicle_number}</span>
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(vehicle.status)}`}>
                                        {vehicle.status}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-600">{vehicle.car_model}</p>
                                <p className="text-xs text-gray-400 mt-1">Policy: {vehicle.policy_number}</p>
                            </div>
                        ))}
                        {vehicles.length === 0 && (
                            <div className="bg-white rounded-xl p-8 text-center border border-gray-100">
                                <p className="text-gray-400 text-sm">✅ No pending vehicles!</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right — Review Panel */}
                <div>
                    {selectedVehicle ? (
                        <div className="bg-white rounded-xl border border-gray-100 p-5">
                            <h3 className="font-bold text-gray-800 mb-4">🔍 Review Vehicle</h3>

                            <div className="space-y-2 mb-4">
                                {[
                                    ['Vehicle Number', selectedVehicle.vehicle_number],
                                    ['Car Model', selectedVehicle.car_model],
                                    ['Policy Number', selectedVehicle.policy_number],
                                    ['Expiry Date', selectedVehicle.policy_expiry_date],
                                    ['User ID', selectedVehicle.user_id],
                                ].map(([label, value]) => (
                                    <div key={label} className="flex justify-between py-1.5 border-b border-gray-50 text-sm">
                                        <span className="text-gray-500 font-medium">{label}</span>
                                        <span className="text-gray-800">{value}</span>
                                    </div>
                                ))}
                            </div>

                            {/* Document Links */}
                            <div className="mb-4 space-y-2">
                                {selectedVehicle.rc_document && (
                                    <a href={`${API_BASE_URL}/${selectedVehicle.rc_document}`}
                                        target="_blank" rel="noreferrer"
                                        className="block bg-blue-50 text-blue-600 px-3 py-2 rounded-lg text-sm hover:bg-blue-100 transition-colors">
                                        📄 View RC Book
                                    </a>
                                )}
                                {selectedVehicle.policy_document && (
                                    <a href={`${API_BASE_URL}/${selectedVehicle.policy_document}`}
                                        target="_blank" rel="noreferrer"
                                        className="block bg-blue-50 text-blue-600 px-3 py-2 rounded-lg text-sm hover:bg-blue-100 transition-colors">
                                        📋 View Policy Document
                                    </a>
                                )}
                            </div>

                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700 mb-1">Agent Notes</label>
                                <textarea value={agentNotes}
                                    onChange={e => setAgentNotes(e.target.value)}
                                    rows={2} placeholder="Add notes (required for rejection)..."
                                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <button onClick={() => handleAction('verified')}
                                    className="bg-green-500 hover:bg-green-600 text-white py-2.5 rounded-lg text-sm font-medium transition-colors">
                                    ✅ Verify Vehicle
                                </button>
                                <button onClick={() => handleAction('rejected')}
                                    className="bg-red-500 hover:bg-red-600 text-white py-2.5 rounded-lg text-sm font-medium transition-colors">
                                    ❌ Reject Vehicle
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="bg-white rounded-xl border border-gray-100 p-12 text-center">
                            <div className="text-4xl mb-3">👈</div>
                            <p className="text-gray-400 text-sm">Select a vehicle to review</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default AgentVehicleDashboard