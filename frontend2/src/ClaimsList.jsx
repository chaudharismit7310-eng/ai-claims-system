import { useState, useEffect } from 'react'
import axios from 'axios'
import { API_BASE_URL } from './config'

function ClaimsList() {
    const [claims, setClaims] = useState([])
    const [loading, setLoading] = useState(true)
    const token = localStorage.getItem('token')
    const user = JSON.parse(localStorage.getItem('user') || '{}')

    useEffect(() => {
        axios.get(`${API_BASE_URL}/claims/all-claims`, {
            headers: { Authorization: `Bearer ${token}` }
        }).then(res => {
            let data = res.data
            // Customer sirf apni claims dekhe
            if (user.role === 'customer') {
                data = data.filter(c =>
                    c.customer_name?.toLowerCase() === user.name?.toLowerCase()
                )
            }
            setClaims(data)
            setLoading(false)
        }).catch(() => setLoading(false))
    }, [])

    const getBadgeColor = (value) => {
        const colors = {
            approved: 'bg-green-100 text-green-700',
            rejected: 'bg-red-100 text-red-700',
            partial: 'bg-amber-100 text-amber-700',
            pending: 'bg-gray-100 text-gray-600',
            approve_suggested: 'bg-green-100 text-green-700',
            reject_suggested: 'bg-red-100 text-red-700',
            driver_fault: 'bg-orange-100 text-orange-700',
            opponent_fault: 'bg-green-100 text-green-700',
            natural: 'bg-blue-100 text-blue-700',
            unclear: 'bg-gray-100 text-gray-600',
        }
        return colors[value] || 'bg-gray-100 text-gray-600'
    }

    const downloadPDF = async (id) => {
        try {
            const res = await axios.get(`${API_BASE_URL}/claims/report/${id}`, {
                responseType: 'blob',
                headers: { Authorization: `Bearer ${token}` }
            })
            const url = window.URL.createObjectURL(new Blob([res.data]))
            const a = document.createElement('a')
            a.href = url
            a.download = `claim_${id}_report.pdf`
            a.click()
        } catch { alert('Error downloading report!') }
    }

    if (loading) return (
        <div className="text-center py-12 text-gray-400">Loading claims...</div>
    )

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-gray-800">
                    {user.role === 'customer' ? '📋 My Claims' : '📋 All Claims'}
                </h2>
                <span className="text-sm text-gray-500">{claims.length} claims</span>
            </div>

            {claims.length === 0 ? (
                <div className="bg-white rounded-2xl p-12 text-center border border-gray-100">
                    <div className="text-5xl mb-3">📋</div>
                    <p className="text-gray-500">No claims found</p>
                    {user.role === 'customer' && (
                        <p className="text-gray-400 text-sm mt-1">
                            Submit a claim to see it here
                        </p>
                    )}
                </div>
            ) : (
                claims.map(claim => (
                    <div key={claim.claim_id}
                        className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
                        <div className="flex items-start justify-between">
                            <div>
                                <div className="flex items-center gap-2 mb-1 flex-wrap">
                                    <span className="font-bold text-gray-800">
                                        Claim #{claim.claim_id}
                                    </span>
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getBadgeColor(claim.final_decision)}`}>
                                        {claim.final_decision}
                                    </span>
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getBadgeColor(claim.ai_decision)}`}>
                                        AI: {claim.ai_decision}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-600">
                                    {claim.customer_name} • {claim.car_model} • {claim.city}
                                </p>
                                <p className="text-sm font-medium text-gray-800 mt-1">
                                    ₹{claim.claim_amount?.toLocaleString('en-IN')}
                                </p>
                            </div>
                            <button onClick={() => downloadPDF(claim.claim_id)}
                                className="text-xs bg-blue-50 text-blue-600 px-3 py-1.5 rounded-lg hover:bg-blue-100 transition-colors">
                                📄 PDF
                            </button>
                        </div>

                        <div className="mt-3 pt-3 border-t border-gray-50 grid grid-cols-2 md:grid-cols-4 gap-2">
                            <div>
                                <p className="text-xs text-gray-400">Fault</p>
                                <span className={`px-2 py-0.5 rounded-full text-xs ${getBadgeColor(claim.fault_type)}`}>
                                    {claim.fault_type}
                                </span>
                            </div>
                            <div>
                                <p className="text-xs text-gray-400">Fraud Score</p>
                                <p className="text-sm font-medium">{claim.fraud_score}</p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-400">Est. Cost</p>
                                <p className="text-sm font-medium">
                                    ₹{claim.estimated_cost?.toLocaleString('en-IN')}
                                </p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-400">Number Plate</p>
                                <p className="text-sm font-medium">{claim.number_plate}</p>
                            </div>
                        </div>

                        {/* Agent notes visible to customer */}
                        {claim.agent_notes && (
                            <div className="mt-2 bg-blue-50 rounded-lg p-2">
                                <p className="text-xs text-blue-600 font-medium">Agent Notes:</p>
                                <p className="text-xs text-blue-800">{claim.agent_notes}</p>
                            </div>
                        )}
                    </div>
                ))
            )}
        </div>
    )
}

export default ClaimsList