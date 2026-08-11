import { useState, useEffect } from 'react'
import axios from 'axios'

function AgentDashboard() {

    const [claims, setClaims] = useState([])
    const [loading, setLoading] = useState(true)
    const [selectedClaim, setSelectedClaim] = useState(null)
    const [agentNotes, setAgentNotes] = useState('')
    const [approvedAmount, setApprovedAmount] = useState('')
    const [submitting, setSubmitting] = useState(false)
    const [message, setMessage] = useState('')

    const token = localStorage.getItem('token')

    useEffect(() => {
        fetchClaims()
    }, [])

    const fetchClaims = () => {
        axios.get('http://127.0.0.1:8000/claims/all-claims', {
            headers: {
                Authorization: `Bearer ${token}`
            }
        })
        .then(res => {
            setClaims(res.data)
            setLoading(false)
        })
        .catch(() => {
            setLoading(false)
        })
    }

    const getBadgeColor = (value) => {
        const colors = {
            approve_suggested: 'bg-green-100 text-green-700',
            reject_suggested: 'bg-red-100 text-red-700',
            partial_suggested: 'bg-amber-100 text-amber-700',
            manual_review_suggested: 'bg-gray-100 text-gray-600',
            approved: 'bg-green-100 text-green-700',
            rejected: 'bg-red-100 text-red-700',
            partial: 'bg-amber-100 text-amber-700',
        }
        return colors[value] || 'bg-gray-100 text-gray-600'
    }

    const handleReview = async (decision) => {
        if (!selectedClaim) return
        setSubmitting(true)

        try {
            await axios.put(
                `http://127.0.0.1:8000/claims/review/${selectedClaim.claim_id}`,
                {
                    final_decision: decision,
                    agent_notes: agentNotes,
                    approved_amount: parseFloat(approvedAmount) || 0
                },
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )

            setMessage(`✅ Claim #${selectedClaim.claim_id} marked as ${decision}!`)
            setSelectedClaim(null)
            setAgentNotes('')
            setApprovedAmount('')
            fetchClaims()

        } catch {
            setMessage('❌ Error submitting review!')
        }

        setSubmitting(false)
    }

    if (loading) {
        return (
            <div className="text-center py-12 text-gray-400">
                Loading...
            </div>
        )
    }

    return (
        <div>
            <h2 className="text-xl font-bold text-gray-800 mb-4">
                🧑‍⚖️ Agent Dashboard
            </h2>

            {message && (
                <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4 text-sm">
                    {message}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                {/* LEFT PANEL */}
                <div>
                    <h3 className="font-bold text-gray-700 mb-3">
                        📋 Awaiting Review
                    </h3>

                    <div className="space-y-3">
                        {claims
                            .filter(c => c.review_status === 'awaiting_review')
                            .map(claim => (
                            <div
                                key={claim.claim_id}
                                onClick={() => {
                                    setSelectedClaim(claim)
                                    setApprovedAmount(String(claim.approved_amount))
                                }}
                                className={`bg-white rounded-xl border p-4 cursor-pointer transition-all ${
                                    selectedClaim?.claim_id === claim.claim_id
                                        ? 'border-blue-400 shadow-md'
                                        : 'border-gray-100 hover:border-gray-300'
                                }`}
                            >
                                <div className="flex items-center justify-between mb-1">
                                    <span className="font-bold text-gray-800">
                                        Claim #{claim.claim_id}
                                    </span>
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getBadgeColor(claim.ai_decision)}`}>
                                        {claim.ai_decision}
                                    </span>
                                </div>

                                <p className="text-sm text-gray-600">
                                    {claim.customer_name} • {claim.car_model}
                                </p>

                                <p className="text-sm font-medium">
                                    ₹{claim.claim_amount?.toLocaleString('en-IN')}
                                </p>

                                <div className="mt-2 flex items-center gap-2">
                                    <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                                        <div
                                            className={`h-1.5 rounded-full ${
                                                claim.fraud_score > 0.6
                                                    ? 'bg-red-500'
                                                    : claim.fraud_score > 0.3
                                                    ? 'bg-amber-500'
                                                    : 'bg-green-500'
                                            }`}
                                            style={{
                                                width: `${claim.fraud_score * 100}%`
                                            }}
                                        />
                                    </div>
                                    <span className="text-xs text-gray-500">
                                        Fraud: {claim.fraud_score}
                                    </span>
                                </div>
                            </div>
                        ))}

                        {claims.filter(c => c.review_status === 'awaiting_review').length === 0 && (
                            <div className="bg-white rounded-xl p-8 text-center border border-gray-100">
                                <p className="text-gray-400 text-sm">
                                    ✅ No pending claims!
                                </p>
                            </div>
                        )}
                    </div>
                </div>

                {/* RIGHT PANEL */}
                <div>
                    {selectedClaim ? (
                        <div className="bg-white rounded-xl border border-gray-100 p-5">
                            <h3 className="font-bold text-gray-800 mb-4">
                                📝 Review Claim #{selectedClaim.claim_id}
                            </h3>

                            {/* Cleaned Details List (No duplicates) */}
                            <div className="space-y-2 mb-4">
                                {[
                                    ['Customer', selectedClaim.customer_name],
                                    ['Car Model', selectedClaim.car_model],
                                    ['City', selectedClaim.city],
                                    ['Claim Amount', `₹${selectedClaim.claim_amount?.toLocaleString('en-IN')}`],
                                    ['Fault Type', selectedClaim.fault_type],
                                    ['Fraud Score', selectedClaim.fraud_score],
                                    ['Number Plate', selectedClaim.number_plate],
                                    ['AI Decision', selectedClaim.ai_decision],
                                    ['AI Reason', selectedClaim.ai_reason],
                                    ['Estimated Cost', `₹${selectedClaim.estimated_cost?.toLocaleString('en-IN')}`],
                                    ['Cost Flag', selectedClaim.cost_flag],
                                    ['Cost Reason', selectedClaim.cost_flag_reason],
                                    ['ELA Score', selectedClaim.ela_score || 0],
                                    ['AI Image Check', selectedClaim.image_fraud_reason || '✅ Genuine'],
                                    ['Risk Level', selectedClaim.risk_level || 'LOW'],
                                    ['Consistency', selectedClaim.consistency_status || 'N/A']
                                ].map(([label, value]) => (
                                    <div
                                        key={label}
                                        className="flex justify-between py-1.5 border-b border-gray-50 text-sm"
                                    >
                                        <span className="text-gray-500 font-medium">
                                            {label}
                                        </span>
                                        <span className="text-gray-800 text-right max-w-xs font-semibold">
                                            {value}
                                        </span>
                                    </div>
                                ))}
                            </div>

                            {/* Heatmap */}
                            {selectedClaim.heatmap_image && (
                              <div className="mt-3">
                                <p className="text-xs font-medium text-gray-600 mb-1">
                                  🌡️ Damage Heatmap
                                </p>
                                <img
                                  src={`http://127.0.0.1:8000/${selectedClaim.heatmap_image}`}
                                  alt="Heatmap"
                                  className="w-full rounded-lg"
                                />
                              </div>
                            )}

                            {/* 🤖 GEMINI VLM VISUAL ANALYSIS CARD */}
                            {selectedClaim.vlm_damage_description && (
                              <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-4 shadow-sm my-4">
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="text-lg">🤖</span>
                                  <h4 className="font-bold text-purple-900 text-sm">Gemini VLM Multimodal Analysis</h4>
                                </div>
                                
                                <p className="text-xs text-purple-900 leading-relaxed mb-3">
                                  {selectedClaim.vlm_damage_description}
                                </p>

                                <div className="grid grid-cols-2 gap-2 bg-white/70 p-2.5 rounded-lg border border-purple-100 text-xs">
                                  <div>
                                    <p className="text-purple-600 font-medium">VLM Severity</p>
                                    <p className="font-bold text-purple-950 capitalize">{selectedClaim.vlm_severity || 'Moderate'}</p>
                                  </div>

                                  <div>
                                    <p className="text-purple-600 font-medium">Photo Genuineness</p>
                                    <p className={`font-bold ${selectedClaim.vlm_is_genuine ? 'text-green-600' : 'text-red-600'}`}>
                                      {selectedClaim.vlm_is_genuine ? '✅ Genuine Image' : '⚠️ Flagged'}
                                    </p>
                                  </div>

                                  <div>
                                    <p className="text-purple-600 font-medium">VLM Cost Range</p>
                                    <p className="font-bold text-purple-950">
                                      ₹{selectedClaim.vlm_estimated_cost_min?.toLocaleString('en-IN')} - ₹{selectedClaim.vlm_estimated_cost_max?.toLocaleString('en-IN')}
                                    </p>
                                  </div>

                                  <div>
                                    <p className="text-purple-600 font-medium">Detected Plate</p>
                                    <p className="font-bold text-purple-950 uppercase">{selectedClaim.vlm_number_plate || 'Not Visible'}</p>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* 📝 LLM EXECUTIVE CLAIM SUMMARY */}
                            {selectedClaim.vlm_claim_summary && (
                              <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 my-3">
                                <h4 className="text-xs font-bold text-blue-800 uppercase tracking-wider mb-1">
                                  📝 AI Executive Summary
                                </h4>
                                <p className="text-xs text-blue-900 leading-relaxed font-medium">
                                  {selectedClaim.vlm_claim_summary}
                                </p>
                              </div>
                            )}

                            {/* XAI Breakdown */}
                            {selectedClaim.xai_explanation && (() => {
                              try {
                                const factors = JSON.parse(selectedClaim.xai_explanation)
                                return factors.length > 0 ? (
                                  <div className="mt-3 bg-gray-50 rounded-lg p-3">
                                    <p className="text-xs font-bold text-gray-700 mb-2">
                                      🧠 AI Risk Factors
                                    </p>
                                    {factors.map((f, i) => (
                                      <div
                                        key={i}
                                        className="flex justify-between text-xs py-1 border-b border-gray-100"
                                      >
                                        <span>
                                          {f.icon} {f.factor}
                                        </span>
                                        <span className="text-red-600 font-bold">
                                          +{(f.contribution * 100).toFixed(0)}%
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                ) : null
                              } catch {
                                return null
                              }
                            })()}

                            {/* Approved Amount */}
                            <div className="mb-3 mt-4">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Approved Amount (₹)
                                </label>
                                <input
                                    type="number"
                                    value={approvedAmount}
                                    onChange={e => setApprovedAmount(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            {/* Agent Notes */}
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Agent Notes
                                </label>
                                <textarea
                                    value={agentNotes}
                                    onChange={e => setAgentNotes(e.target.value)}
                                    rows={2}
                                    placeholder="Add review notes..."
                                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            {/* Buttons */}
                            <div className="grid grid-cols-3 gap-2">
                                <button
                                    onClick={() => handleReview('approved')}
                                    disabled={submitting}
                                    className="bg-green-500 hover:bg-green-600 text-white py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                                >
                                    ✅ Approve
                                </button>
                                <button
                                    onClick={() => handleReview('partial')}
                                    disabled={submitting}
                                    className="bg-amber-500 hover:bg-amber-600 text-white py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                                >
                                    ⚠️ Partial
                                </button>
                                <button
                                    onClick={() => handleReview('rejected')}
                                    disabled={submitting}
                                    className="bg-red-500 hover:bg-red-600 text-white py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                                >
                                    ❌ Reject
                                </button>
                            </div>

                        </div>
                    ) : (
                        <div className="bg-white rounded-xl border border-gray-100 p-12 text-center">
                            <div className="text-4xl mb-3">
                                👈
                            </div>
                            <p className="text-gray-400 text-sm">
                                Select a claim to review
                            </p>
                        </div>
                    )}

                    {/* REVIEWED CLAIMS */}
                    <div className="mt-4">
                        <h3 className="font-bold text-gray-700 mb-3">
                            ✅ Reviewed Claims
                        </h3>

                        <div className="space-y-2">
                            {claims
                                .filter(c => c.review_status === 'reviewed')
                                .map(claim => (
                                <div
                                    key={claim.claim_id}
                                    className={`bg-white rounded-lg border p-3 border-l-4 ${
                                        claim.final_decision === 'approved'
                                            ? 'border-l-green-400'
                                            : claim.final_decision === 'rejected'
                                            ? 'border-l-red-400'
                                            : 'border-l-amber-400'
                                    }`}
                                >
                                    <div className="flex justify-between text-sm">
                                        <span className="font-medium">
                                            Claim #{claim.claim_id} — {claim.customer_name}
                                        </span>
                                        <span className={`px-2 py-0.5 rounded-full text-xs ${
                                            claim.final_decision === 'approved'
                                                ? 'bg-green-100 text-green-700'
                                                : claim.final_decision === 'rejected'
                                                ? 'bg-red-100 text-red-700'
                                                : 'bg-amber-100 text-amber-700'
                                        }`}>
                                            {claim.final_decision}
                                        </span>
                                    </div>

                                    <p className="text-xs text-gray-500 mt-1">
                                        ₹{claim.approved_amount?.toLocaleString('en-IN')} approved
                                    </p>

                                    {claim.agent_notes && (
                                        <p className="text-xs text-gray-400 mt-1">
                                            Notes: {claim.agent_notes}
                                        </p>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                </div>

            </div>
        </div>
    )
}

export default AgentDashboard