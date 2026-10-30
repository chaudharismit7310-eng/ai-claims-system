import { useState, useEffect } from 'react'
import axios from 'axios'
import AddVehicle from './AddVehicle'
import { API_BASE_URL } from './config'

function MyVehicles() {
    const [vehicles, setVehicles] = useState([])
    const [loading, setLoading] = useState(true)
    const [showAdd, setShowAdd] = useState(false)
    const token = localStorage.getItem('token')

    useEffect(() => { fetchVehicles() }, [])

    const fetchVehicles = () => {
        axios.get(`${API_BASE_URL}/vehicles/my-vehicles`, {
            headers: { Authorization: `Bearer ${token}` }
        }).then(res => { setVehicles(res.data); setLoading(false) })
            .catch(() => setLoading(false))
    }

    const getStatusBadge = (status) => {
        const badges = {
            pending_verification: 'bg-yellow-100 text-yellow-700',
            verified: 'bg-green-100 text-green-700',
            rejected: 'bg-red-100 text-red-700',
            under_review: 'bg-blue-100 text-blue-700',
        }
        return badges[status] || 'bg-gray-100 text-gray-600'
    }

    const getStatusLabel = (status) => {
        const labels = {
            pending_verification: '🟡 Pending Verification',
            verified: '🟢 Verified',
            rejected: '🔴 Rejected',
            under_review: '🔵 Under Review',
        }
        return labels[status] || status
    }

    if (loading) return <div className="text-center py-12 text-gray-400">Loading vehicles...</div>

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-800">🚗 My Vehicles</h2>
                <button onClick={() => setShowAdd(!showAdd)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                    {showAdd ? '✕ Cancel' : '+ Add Vehicle'}
                </button>
            </div>

            {showAdd && (
                <div className="mb-6">
                    <AddVehicle onSuccess={() => { setShowAdd(false); fetchVehicles() }} />
                </div>
            )}

            {vehicles.length === 0 ? (
                <div className="bg-white rounded-2xl p-12 text-center border border-gray-100">
                    <div className="text-5xl mb-3">🚗</div>
                    <p className="text-gray-500 mb-2">No vehicles added yet</p>
                    <p className="text-gray-400 text-sm">Add a vehicle to start submitting claims</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {vehicles.map(vehicle => (
                        <div key={vehicle.vehicle_id} className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
                            <div className="flex items-start justify-between mb-3">
                                <div>
                                    <h3 className="font-bold text-gray-800">{vehicle.vehicle_number}</h3>
                                    <p className="text-sm text-gray-600">{vehicle.car_model}</p>
                                </div>
                                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadge(vehicle.status)}`}>
                                    {getStatusLabel(vehicle.status)}
                                </span>
                            </div>

                            <div className="space-y-1.5 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Policy Number</span>
                                    <span className="font-medium">{vehicle.policy_number}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Expiry Date</span>
                                    <span className="font-medium">{vehicle.policy_expiry_date}</span>
                                </div>
                            </div>

                            {vehicle.status === 'pending_verification' && (
                                <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded-lg p-2 text-xs text-yellow-700">
                                    ⏳ Waiting for agent verification
                                </div>
                            )}

                            {vehicle.status === 'rejected' && (
                                <div className="mt-3">
                                    <div className="bg-red-50 border border-red-200 rounded-lg p-2 text-xs text-red-700 mb-2">
                                        ❌ Rejected: {vehicle.agent_notes || 'Documents invalid'}
                                    </div>
                                    <button className="w-full bg-red-500 hover:bg-red-600 text-white py-1.5 rounded-lg text-xs font-medium transition-colors">
                                        🔄 Resubmit
                                    </button>
                                </div>
                            )}

                            {vehicle.status === 'verified' && (
                                <div className="mt-3 bg-green-50 border border-green-200 rounded-lg p-2 text-xs text-green-700">
                                    ✅ Vehicle verified — you can submit claims!
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default MyVehicles