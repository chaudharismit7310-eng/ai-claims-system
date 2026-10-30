import { useState, useEffect } from 'react'
import axios from 'axios'
import { API_BASE_URL } from './config'

function AgentDashboard() {

    const [claims, setClaims] = useState([])
    const [loading, setLoading] = useState(true)
    const [selectedClaim, setSelectedClaim] = useState(null)
    const [agentNotes, setAgentNotes] = useState('')
    const [approvedAmount, setApprovedAmount] = useState('')
    const [submitting, setSubmitting] = useState(false)
    const [message, setMessage] = useState('')
    const [selectedKeyframe, setSelectedKeyframe] = useState(null)

    const token = localStorage.getItem('token')

    useEffect(() => {
        fetchClaims()
    }, [])

    const fetchClaims = () => {
        axios.get(`${API_BASE_URL}/claims/all-claims`, {
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

    const handleSettlement = async () => {
        if (!selectedClaim) return
        setSubmitting(true)

        try {
            const amount = parseFloat(approvedAmount) || 0
            await axios.post(
                `${API_BASE_URL}/claims/settle/${selectedClaim.claim_id}`,
                {
                    final_amount: amount,
                    notes: agentNotes || "No notes provided"
                },
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )

            setMessage(`✅ Settlement for Claim #${selectedClaim.claim_id} authorized at ₹${amount.toLocaleString('en-IN')}!`)
            setSelectedClaim(null)
            setAgentNotes('')
            setApprovedAmount('')
            fetchClaims()

        } catch {
            setMessage('❌ Error authorizing settlement!')
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

                            {/* DOWNLOAD PDF REPORT BUTTON */}
                            <a
                                href={`${API_BASE_URL}/claims/${selectedClaim.claim_id}/download-pdf`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="w-full bg-slate-800 hover:bg-slate-900 text-white py-2.5 px-4 rounded-xl text-xs font-bold shadow transition-all flex items-center justify-center gap-2 my-3"
                            >
                                <span>📄</span> Download Inspection Report / PDF
                            </a>

                             {/* DECLARED POST-TRANSIT INSPECTION CALLOUT CARD */}
                             {selectedClaim.is_post_transit && (
                               <div className="bg-indigo-50 border-2 border-indigo-200 rounded-xl p-4 my-4 shadow-sm">
                                 <div className="flex items-center justify-between mb-2">
                                   <h4 className="font-bold text-indigo-950 text-sm flex items-center gap-2">
                                     <span>📋</span> DECLARED POST-TRANSIT INSPECTION
                                   </h4>
                                   <span className="bg-indigo-100 text-indigo-800 text-[10px] font-bold px-2 py-0.5 rounded">
                                     STP Bypassed (Adjuster Sign-off Required)
                                   </span>
                                 </div>
                                 <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-indigo-900 bg-white/80 p-3 rounded-lg border border-indigo-100 mb-2">
                                   <div>
                                     <span className="font-medium text-indigo-600 block">Incident Site:</span>
                                     <span className="font-bold">{selectedClaim.incident_location || 'Declared Incident Location'}</span>
                                   </div>
                                   <div>
                                     <span className="font-medium text-indigo-600 block">Inspection Site:</span>
                                     <span className="font-bold">{selectedClaim.inspection_location || 'Current Inspection Site'}</span>
                                   </div>
                                   <div className="sm:col-span-2">
                                     <span className="font-medium text-indigo-600 block">Transit Rationale:</span>
                                     <span className="font-semibold">{selectedClaim.transit_reason || 'Vehicle towed directly to repair workshop / residence'}</span>
                                   </div>
                                 </div>
                                 <p className="text-[11px] text-indigo-700 font-medium flex items-center gap-1">
                                   <span>ℹ️</span> <strong>Audit Protocol:</strong> Verify damage profile &amp; 360° keyframes align with declared transit timeline.
                                 </p>
                               </div>
                             )}

                             {/* DECOUPLED TELEMETRY & EXIF GPS STATUS CARD */}
                             <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 my-3">
                               <div className="flex items-center justify-between mb-2">
                                 <h4 className="font-bold text-slate-800 text-xs flex items-center gap-1.5">
                                   <span>📡</span> Decoupled Location Telemetry Audit
                                 </h4>
                                 {selectedClaim.exif_gps_status === 'HARDWARE_VERIFIED' ? (
                                   <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded flex items-center gap-1">
                                     <span>✅</span> HARDWARE_VERIFIED
                                   </span>
                                 ) : (
                                   <span className="bg-amber-100 text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded flex items-center gap-1">
                                     <span>⚠️</span> METADATA_STRIPPED (Decoupled)
                                   </span>
                                 )}
                               </div>

                               <div className="grid grid-cols-2 gap-2 text-xs bg-white p-2.5 rounded-lg border border-slate-100">
                                 <div>
                                   <span className="text-slate-500 font-medium block">Photo Capture GPS (Camera EXIF):</span>
                                   <span className={`font-bold ${selectedClaim.photo_capture_lat ? 'text-emerald-700' : 'text-amber-600'}`}>
                                     {selectedClaim.photo_capture_lat ? `${selectedClaim.photo_capture_lat.toFixed(4)}°, ${selectedClaim.photo_capture_lon?.toFixed(4)}°` : 'METADATA_STRIPPED (No EXIF GPS)'}
                                   </span>
                                 </div>
                                 <div>
                                   <span className="text-slate-500 font-medium block">Submission Device GPS (Client Browser):</span>
                                   <span className="font-bold text-slate-800">
                                     {selectedClaim.submission_device_lat || selectedClaim.device_latitude ? `${(selectedClaim.submission_device_lat || selectedClaim.device_latitude).toFixed(4)}°, ${(selectedClaim.submission_device_lon || selectedClaim.device_longitude).toFixed(4)}°` : 'Not Provided'}
                                   </span>
                                 </div>
                               </div>
                             </div>

                             {/* 🚨 VLM GEOGRAPHIC INCONGRUITY ALERT CARD */}
                             {selectedClaim.geographic_incongruity && (
                               <div className="bg-red-50 border-2 border-red-300 rounded-xl p-4 my-3 shadow-sm">
                                 <div className="flex items-center gap-2 mb-1 text-red-900 font-bold text-sm">
                                   <span className="text-lg">🚨</span> GEOGRAPHIC INCONGRUITY DETECTED
                                 </div>
                                 <p className="text-xs text-red-800 font-semibold mb-2">
                                   Non-Indian roadway/vehicle infrastructure detected in photo! Automatic rejection recommended.
                                 </p>
                                 <div className="bg-white/80 border border-red-200 p-2.5 rounded-lg text-xs text-red-950 font-mono">
                                   <strong>VLM Evidence:</strong> {selectedClaim.geographic_incongruity_reason || 'Foreign roadway markers or left-hand drive configuration observed.'}
                                 </div>
                               </div>
                             )}

                            {/* Heatmap */}
                            {selectedClaim.heatmap_image && (
                              <div className="mt-3">
                                <p className="text-xs font-medium text-gray-600 mb-1">
                                  🌡️ Damage Heatmap
                                </p>
                                <img
                                  src={`${API_BASE_URL}/${selectedClaim.heatmap_image}`}
                                  alt="Heatmap"
                                  className="w-full rounded-lg"
                                />
                              </div>
                            )}

                            {/* Walkaround Video Verification */}
                            {selectedClaim.walkaround_video_url ? (
                              <div className="mt-4 bg-gray-50 border border-gray-200 rounded-lg p-3">
                                <p className="text-xs font-bold text-gray-700 mb-2 flex items-center gap-1">
                                  <span>✅</span> 360° Walkaround Video Verification
                                </p>
                                <video
                                  src={`${API_BASE_URL}/${selectedClaim.walkaround_video_url}`}
                                  controls
                                  className="w-full max-h-64 rounded-lg bg-black mb-3"
                                />

                                {/* Filmstrip Section */}
                                {selectedClaim.video_analysis_json && (() => {
                                  try {
                                    const analysis = JSON.parse(selectedClaim.video_analysis_json)
                                    if (analysis.keyframes && analysis.keyframes.length > 0) {
                                      return (
                                        <div className="mt-2 mb-3 bg-white border border-gray-100 rounded-lg p-3">
                                          <div className="flex items-center justify-between mb-2">
                                            <p className="text-xs font-bold text-indigo-900">🎞️ Auto-Extracted Keyframes</p>
                                            <div className="flex gap-2">
                                              {analysis.plate_verified_in_video ? 
                                                <span className="bg-emerald-100 text-emerald-700 text-[10px] px-2 py-0.5 rounded font-bold">✅ Plate Detected</span> : 
                                                <span className="bg-red-100 text-red-700 text-[10px] px-2 py-0.5 rounded font-bold">❌ Plate Missing</span>
                                              }
                                              {analysis.damage_verified_in_video ? 
                                                <span className="bg-emerald-100 text-emerald-700 text-[10px] px-2 py-0.5 rounded font-bold">✅ Damage Visible</span> : 
                                                <span className="bg-red-100 text-red-700 text-[10px] px-2 py-0.5 rounded font-bold">❌ No Damage</span>
                                              }
                                            </div>
                                          </div>
                                          <div className="grid grid-cols-4 gap-2">
                                            {analysis.keyframes.map((kf, i) => (
                                              <div 
                                                key={i} 
                                                className="cursor-pointer border border-gray-200 rounded overflow-hidden hover:border-indigo-400 hover:shadow-sm transition-all"
                                                onClick={() => setSelectedKeyframe(`${API_BASE_URL}/${kf}`)}
                                              >
                                                <img src={`${API_BASE_URL}/${kf}`} alt={`Keyframe ${i+1}`} className="w-full h-16 object-cover" />
                                              </div>
                                            ))}
                                          </div>
                                          <p className="text-[10px] text-gray-500 mt-2 font-medium">AI Summary: {analysis.summary}</p>
                                        </div>
                                      )
                                    }
                                  } catch (e) {
                                    return null
                                  }
                                })()}
                                
                                <div className="mt-2 text-xs text-gray-600 bg-white border border-gray-100 rounded p-2">
                                  <strong>Prompt for Adjuster:</strong> "Confirm license plate, car color, and scratch alignment match the primary claim photo."
                                </div>
                              </div>
                            ) : (
                              <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-800 flex items-center gap-2">
                                <span>⚠️</span> No 360° Video Provided (Photo Only)
                              </div>
                            )}

                            {/* GARAGE ESTIMATE AUDIT */}
                            {selectedClaim.garage_audit_json && (() => {
                                try {
                                    const audit = JSON.parse(selectedClaim.garage_audit_json)
                                    if (audit.flagged_items) {
                                        return (
                                            <div className="mt-4 bg-orange-50 border border-orange-200 rounded-xl p-4 shadow-sm mb-4">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="text-lg">📋</span>
                                                    <h4 className="font-bold text-orange-900 text-sm">Garage Estimate Forensic Audit</h4>
                                                </div>
                                                <div className="flex gap-2 mb-3">
                                                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${audit.audit_verdict === 'FAIR' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                                        {audit.audit_verdict.replace('_', ' ')}
                                                    </span>
                                                    <span className="bg-orange-100 text-orange-800 text-[10px] px-2 py-0.5 rounded font-bold">
                                                        Total Quoted: ₹{audit.total_quoted_cost?.toLocaleString('en-IN')}
                                                    </span>
                                                </div>
                                                <div className="overflow-x-auto">
                                                    <table className="w-full text-left border-collapse text-xs bg-white/50 rounded-lg overflow-hidden">
                                                        <thead>
                                                            <tr className="bg-orange-100/50 text-orange-900 border-b border-orange-200">
                                                                <th className="py-2 px-2 font-bold">Part/Labor</th>
                                                                <th className="py-2 px-2 font-bold text-right">Quoted</th>
                                                                <th className="py-2 px-2 font-bold text-right">AI Baseline</th>
                                                                <th className="py-2 px-2 font-bold text-center">Status</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {audit.flagged_items.map((item, i) => (
                                                                <tr key={i} className="border-b border-orange-100/50">
                                                                    <td className="py-2 px-2 text-orange-900 truncate max-w-[120px]" title={item.part_or_labor}>{item.part_or_labor}</td>
                                                                    <td className="py-2 px-2 text-right text-gray-700">₹{item.quoted_amount}</td>
                                                                    <td className="py-2 px-2 text-right text-gray-700">₹{item.ai_benchmark_amount}</td>
                                                                    <td className="py-2 px-2 text-center">
                                                                        {item.is_inflated ? (
                                                                            <span className="text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-bold">+{(item.inflation_percentage).toFixed(0)}%</span>
                                                                        ) : (
                                                                            <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-bold">FAIR</span>
                                                                        )}
                                                                    </td>
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                </div>
                                                <p className="text-[10px] text-orange-700 mt-2 font-medium italic">
                                                    AI Note: {audit.audit_reasoning}
                                                </p>
                                            </div>
                                        )
                                    }
                                } catch (e) {
                                    return null
                                }
                            })()}

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

                            {/* 🤝 AUTHORIZE FINAL SETTLEMENT CARD */}
                            <div className="mt-6 bg-white border-2 border-indigo-100 rounded-xl p-4 shadow-sm relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-400 to-purple-500"></div>
                                <h4 className="font-bold text-indigo-900 mb-3 flex items-center gap-2">
                                    <span className="text-xl">🤝</span> Authorize Final Settlement
                                </h4>

                                <div className="mb-4">
                                    <div className="flex justify-between items-end mb-2">
                                        <label className="text-sm font-semibold text-gray-700">
                                            Settlement Counter-Offer (₹)
                                        </label>
                                        <span className="text-lg font-bold text-indigo-700 bg-indigo-50 px-3 py-1 rounded-lg">
                                            ₹{Number(approvedAmount || 0).toLocaleString('en-IN')}
                                        </span>
                                    </div>
                                    <input
                                        type="range"
                                        min="0"
                                        max={selectedClaim.claim_amount || 0}
                                        step="500"
                                        value={approvedAmount}
                                        onChange={e => setApprovedAmount(e.target.value)}
                                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                                    />
                                    <div className="flex justify-between text-xs text-gray-500 mt-1 font-medium">
                                        <span>₹0</span>
                                        <span>Max: ₹{selectedClaim.claim_amount?.toLocaleString('en-IN')}</span>
                                    </div>
                                </div>

                                {/* Preset Buttons */}
                                <div className="flex flex-wrap gap-2 mb-4">
                                    <button
                                        onClick={() => setApprovedAmount(selectedClaim.claim_amount)}
                                        className="text-xs font-semibold bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded-full transition-colors"
                                    >
                                        Use Full Claim
                                    </button>
                                    <button
                                        onClick={() => {
                                            let cost = 0;
                                            if (selectedClaim.garage_audit_json) {
                                                try {
                                                    const audit = JSON.parse(selectedClaim.garage_audit_json);
                                                    cost = audit.ai_reconciled_cost;
                                                } catch(e) {}
                                            }
                                            if (!cost) cost = selectedClaim.estimated_cost;
                                            setApprovedAmount(cost || 0);
                                        }}
                                        className="text-xs font-semibold bg-blue-100 hover:bg-blue-200 text-blue-700 px-3 py-1.5 rounded-full transition-colors"
                                    >
                                        Use AI Estimate
                                    </button>
                                    <button
                                        onClick={() => setApprovedAmount((selectedClaim.claim_amount || 0) * 0.5)}
                                        className="text-xs font-semibold bg-amber-100 hover:bg-amber-200 text-amber-700 px-3 py-1.5 rounded-full transition-colors"
                                    >
                                        50% Fault Payout
                                    </button>
                                    <button
                                        onClick={() => setApprovedAmount(0)}
                                        className="text-xs font-semibold bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1.5 rounded-full transition-colors"
                                    >
                                        Reject (₹0)
                                    </button>
                                </div>

                                {/* Adjuster Notes */}
                                <div className="mb-4">
                                    <label className="block text-sm font-semibold text-gray-700 mb-1">
                                        Settlement Notes / Deductions
                                    </label>
                                    <textarea
                                        value={agentNotes}
                                        onChange={e => setAgentNotes(e.target.value)}
                                        rows={2}
                                        placeholder="e.g. Depreciation Applied, Non-OEM Parts Substituted..."
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50"
                                    />
                                </div>

                                {/* Submit Button */}
                                <button
                                    onClick={handleSettlement}
                                    disabled={submitting}
                                    className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white py-3 rounded-xl text-sm font-bold shadow-md transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    <span>💾</span> Commit & Authorize Settlement
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
                            ✅ Reviewed / Settled Claims
                        </h3>

                        <div className="space-y-2">
                            {claims
                                .filter(c => c.review_status === 'reviewed' || c.review_status === 'settled')
                                .map(claim => (
                                <div
                                    key={claim.claim_id}
                                    className={`bg-white rounded-lg border p-3 border-l-4 ${
                                        (claim.final_decision === 'approved' || claim.settlement_status === 'approved')
                                            ? 'border-l-green-400'
                                            : (claim.final_decision === 'rejected' || claim.settlement_status === 'rejected')
                                            ? 'border-l-red-400'
                                            : 'border-l-amber-400'
                                    }`}
                                >
                                    <div className="flex justify-between text-sm">
                                        <span className="font-medium">
                                            Claim #{claim.claim_id} — {claim.customer_name}
                                        </span>
                                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                            (claim.final_decision === 'approved' || claim.settlement_status === 'approved')
                                                ? 'bg-green-100 text-green-700'
                                                : (claim.final_decision === 'rejected' || claim.settlement_status === 'rejected')
                                                ? 'bg-red-100 text-red-700'
                                                : 'bg-amber-100 text-amber-700'
                                        }`}>
                                            {claim.settlement_status ? `SETTLED: ${claim.settlement_status.toUpperCase()}` : claim.final_decision}
                                        </span>
                                    </div>

                                    <p className="text-xs text-gray-500 mt-1 font-semibold">
                                        ₹{Number(claim.final_approved_amount || claim.approved_amount || 0).toLocaleString('en-IN')} authorized
                                    </p>

                                    {(claim.settlement_notes || claim.agent_notes) && (
                                        <p className="text-xs text-gray-400 mt-1 italic">
                                            Notes: {claim.settlement_notes || claim.agent_notes}
                                        </p>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                </div>
            </div>

            {/* LIGHTBOX MODAL */}
            {selectedKeyframe && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4" onClick={() => setSelectedKeyframe(null)}>
                    <div className="relative max-w-4xl w-full" onClick={e => e.stopPropagation()}>
                        <button 
                            className="absolute -top-10 right-0 text-white text-2xl font-bold hover:text-gray-300"
                            onClick={() => setSelectedKeyframe(null)}
                        >×</button>
                        <img src={selectedKeyframe} alt="Full Screen Keyframe" className="w-full rounded-lg shadow-2xl" />
                    </div>
                </div>
            )}
        </div>
    )
}

export default AgentDashboard