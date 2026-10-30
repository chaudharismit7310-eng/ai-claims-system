import { useState, useEffect } from 'react'
import axios from 'axios'
import { API_BASE_URL } from './config'

function ClaimTracking() {
    const [claims, setClaims] = useState([])
    const [loading, setLoading] = useState(true)
    const [expandedClaim, setExpandedClaim] = useState(null)
    const token = localStorage.getItem('token')
    const user = JSON.parse(localStorage.getItem('user') || '{}')

    useEffect(() => {
        axios.get(`${API_BASE_URL}/claims/my-claims`, {
            headers: { Authorization: `Bearer ${token}` }
        }).then(res => { setClaims(res.data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    const getStatusColor = (status) => {
        const colors = {
            submitted: 'bg-blue-500',
            under_review: 'bg-yellow-500',
            approved: 'bg-green-500',
            rejected: 'bg-red-500',
            partial: 'bg-amber-500',
            pending: 'bg-gray-400',
        }
        return colors[status] || 'bg-gray-400'
    }

    const getBadgeColor = (value) => {
        const colors = {
            approved: 'bg-green-100 text-green-700',
            rejected: 'bg-red-100 text-red-700',
            partial: 'bg-amber-100 text-amber-700',
            pending: 'bg-gray-100 text-gray-600',
            approve_suggested: 'bg-green-100 text-green-700',
            reject_suggested: 'bg-red-100 text-red-700',
            awaiting_review: 'bg-blue-100 text-blue-700',
            reviewed: 'bg-green-100 text-green-700',
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
        } catch { alert('Error downloading!') }
    }

    if (loading) return <div className="text-center py-12 text-gray-400">Loading...</div>

    return (
        <div>
            <h2 className="text-xl font-bold text-gray-800 mb-4">📋 My Claims</h2>

            {claims.length === 0 ? (
                <div className="bg-white rounded-2xl p-12 text-center border border-gray-100">
                    <div className="text-5xl mb-3">📋</div>
                    <p className="text-gray-500">No claims found</p>
                </div>
            ) : (
                claims.map(claim => (
                    <div key={claim.claim_id} className="bg-white rounded-xl border border-gray-100 mb-4 shadow-sm overflow-hidden">
                        {/* Header */}
                        <div className="p-4 flex items-start justify-between cursor-pointer"
                            onClick={() => setExpandedClaim(expandedClaim === claim.claim_id ? null : claim.claim_id)}>
                            <div>
                                <div className="flex items-center gap-2 mb-1 flex-wrap">
                                    <span className="font-bold text-gray-800">Claim #{claim.claim_id}</span>
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getBadgeColor(claim.final_decision)}`}>
                                        {claim.final_decision}
                                    </span>
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getBadgeColor(claim.review_status)}`}>
                                        {claim.review_status}
                                    </span>
                                    {claim.exif_fraud_flag && (
                                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                                            ⚠️ EXIF Flag
                                        </span>
                                    )}
                                </div>
                                <p className="text-sm text-gray-600">{claim.car_model} • {claim.city}</p>
                                <p className="text-sm font-medium text-gray-800">₹{claim.claim_amount?.toLocaleString('en-IN')}</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <button onClick={e => { e.stopPropagation(); downloadPDF(claim.claim_id) }}
                                    className="text-xs bg-blue-50 text-blue-600 px-3 py-1.5 rounded-lg hover:bg-blue-100">
                                    📄 PDF
                                </button>
                                <span className="text-gray-400">{expandedClaim === claim.claim_id ? '▲' : '▼'}</span>
                            </div>
                        </div>

                        {/* Timeline */}
                        {expandedClaim === claim.claim_id && (
                            <div className="border-t border-gray-100 p-4">
                                <h4 className="font-medium text-gray-700 mb-3">📍 Claim Timeline</h4>
                                <div className="space-y-3 mb-4">
                                    {(() => {
                                        try {
                                            const timeline = JSON.parse(claim.status_timeline || '[]')
                                            return timeline.map((item, i) => (
                                                <div key={i} className="flex items-start gap-3">
                                                    <div className={`w-3 h-3 rounded-full mt-1 flex-shrink-0 ${getStatusColor(item.status)}`} />
                                                    <div>
                                                        <p className="text-sm font-medium text-gray-700 capitalize">{item.status}</p>
                                                        <p className="text-xs text-gray-400">{item.note}</p>
                                                        <p className="text-xs text-gray-400">
                                                            {new Date(item.timestamp).toLocaleString('en-IN')}
                                                        </p>
                                                    </div>
                                                </div>
                                            ))
                                        } catch { return <p className="text-xs text-gray-400">No timeline data</p> }
                                    })()}
                                </div>

                                {/* Claim Details */}
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                    <div className="bg-gray-50 rounded-lg p-3">
                                        <p className="text-xs text-gray-400">AI Decision</p>
                                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getBadgeColor(claim.ai_decision)}`}>
                                            {claim.ai_decision}
                                        </span>
                                    </div>
                                    <div className="bg-gray-50 rounded-lg p-3">
                                        <p className="text-xs text-gray-400">Fault Type</p>
                                        <p className="text-sm font-medium">{claim.fault_type}</p>
                                    </div>
                                    <div className="bg-gray-50 rounded-lg p-3">
                                        <p className="text-xs text-gray-400">Fraud Score</p>
                                        <div className="flex items-center gap-2 mt-1">
                                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                                                <div className={`h-2 rounded-full ${claim.fraud_score > 0.6 ? 'bg-red-500' : claim.fraud_score > 0.3 ? 'bg-amber-500' : 'bg-green-500'}`}
                                                    style={{ width: `${claim.fraud_score * 100}%` }} />
                                            </div>
                                            <span className="text-xs">{claim.fraud_score}</span>
                                        </div>
                                    </div>
                                    <div className="bg-gray-50 rounded-lg p-3">
                                        <p className="text-xs text-gray-400">Estimated Cost</p>
                                        <p className="text-sm font-medium">₹{claim.estimated_cost?.toLocaleString('en-IN')}</p>
                                    </div>
                                    <div className="bg-gray-50 rounded-lg p-3">
                                        <p className="text-xs text-gray-400">Approved Amount</p>
                                        <p className="text-sm font-medium text-green-600">₹{claim.approved_amount?.toLocaleString('en-IN')}</p>
                                    </div>
                                    <div className="bg-gray-50 rounded-lg p-3">
                                        <p className="text-xs text-gray-400">Number Plate</p>
                                        <p className="text-sm font-medium">{claim.number_plate}</p>
                                    </div>
                                </div>

                                {/* AI Reason */}
                                <div className="mt-3 bg-blue-50 border border-blue-100 rounded-lg p-3">
                                    <p className="text-xs text-blue-600 font-medium mb-1">AI Reason</p>
                                    <p className="text-sm text-blue-800">{claim.ai_reason}</p>
                                </div>

                                {/* Agent Notes */}
                                {claim.agent_notes && (
                                    <div className="mt-3 bg-green-50 border border-green-100 rounded-lg p-3">
                                        <p className="text-xs text-green-600 font-medium mb-1">Agent Notes</p>
                                        <p className="text-sm text-green-800">{claim.agent_notes}</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ))
            )}
        </div>
    )
}

export default ClaimTracking