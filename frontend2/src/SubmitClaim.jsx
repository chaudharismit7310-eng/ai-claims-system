import { useState, useEffect } from 'react'
import axios from 'axios'
import VoiceInput from './VoiceInput'

function SubmitClaim() {
  const [form, setForm] = useState({
    customer_name: '',
    car_model: '',
    vehicle_number: '',
    city: '',
    policy_type: 'comprehensive',
    claim_amount: '',
    description: ''
  })

  const [files, setFiles] = useState([])
  const [garagePdf, setGaragePdf] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [verifiedVehicles, setVerifiedVehicles] = useState([])
  const [selectedVehicle, setSelectedVehicle] = useState(null)

  const token = localStorage.getItem('token')

  useEffect(() => {
    axios
      .get('http://127.0.0.1:8000/vehicles/verified', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      .then((res) => setVerifiedVehicles(res.data))
      .catch(() => {})
  }, [token])

  const isPolicyExpired = (vehicle) => {
    if (!vehicle || !vehicle.policy_expiry_date) return false
    try {
      return new Date(vehicle.policy_expiry_date) < new Date()
    } catch {
      return false
    }
  }

  const handleVehicleSelect = (e) => {
    const vehicleId = parseInt(e.target.value)
    const vehicle = verifiedVehicles.find((v) => v.vehicle_id === vehicleId)

    setSelectedVehicle(vehicle || null)

    if (vehicle) {
      setForm((prevForm) => ({
        ...prevForm,
        car_model: vehicle.car_model,
        vehicle_number: vehicle.vehicle_number || vehicle.license_plate || ''
      }))
    }
  }

  const handleSubmit = async () => {
    if (files.length === 0) {
      alert('Please upload at least one image!')
      return
    }

    if (!selectedVehicle) {
      alert('Please select a verified vehicle!')
      return
    }

    if (isPolicyExpired(selectedVehicle)) {
      alert(`Policy expired on ${selectedVehicle.policy_expiry_date}! Please renew.`)
      return
    }

    if (!form.customer_name || !form.claim_amount || !form.city || !form.description) {
      alert('Please fill in all required fields!')
      return
    }

    setLoading(true)

    try {
      const formData = new FormData()

      Object.entries(form).forEach(([k, v]) => {
        if (v !== undefined && v !== null) {
          formData.append(k, v)
        }
      })

      files.forEach((f) => {
        formData.append('files', f)
      })

      if (garagePdf) {
        formData.append('garage_pdf', garagePdf)
      }

      const res = await axios.post(
        'http://127.0.0.1:8000/claims/submit-claim',
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      setResult(res.data)
    } catch (err) {
      alert(err.response?.data?.detail || 'Error submitting claim!')
    }

    setLoading(false)
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 max-w-4xl mx-auto my-6">
      <h2 className="text-xl font-bold text-gray-800 mb-6">Submit New Claim</h2>

      {!result ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Vehicle Selection */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Select Verified Vehicle <span className="text-red-500">*</span>
            </label>

            {verifiedVehicles.length === 0 ? (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm text-yellow-700">
                ⚠️ No verified vehicles found. Please add and verify a vehicle first!
              </div>
            ) : (
              <select
                onChange={handleVehicleSelect}
                value={selectedVehicle ? selectedVehicle.vehicle_id : ''}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              >
                <option value="">-- Select Vehicle --</option>
                {verifiedVehicles.map((v) => (
                  <option key={v.vehicle_id} value={v.vehicle_id}>
                    {v.vehicle_number || v.license_plate} — {v.car_model} ✅ Verified
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Policy Status */}
          {selectedVehicle && (
            <div
              className={`md:col-span-2 p-3 rounded-lg text-sm border ${
                isPolicyExpired(selectedVehicle)
                  ? 'bg-red-50 border-red-200 text-red-700'
                  : 'bg-green-50 border-green-200 text-green-700'
              }`}
            >
              {isPolicyExpired(selectedVehicle)
                ? `❌ Policy expired on ${selectedVehicle.policy_expiry_date}! Cannot submit claim.`
                : `✅ Policy valid until ${selectedVehicle.policy_expiry_date}`}
            </div>
          )}

          {/* Customer Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Customer Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              placeholder="e.g. Rahul Sharma"
              value={form.customer_name}
              onChange={(e) => setForm({ ...form, customer_name: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>

          {/* City */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              City <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              placeholder="e.g. Mumbai"
              value={form.city}
              onChange={(e) => setForm({ ...form, city: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>

          {/* Claim Amount */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Claim Amount (₹) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              placeholder="e.g. 25000"
              value={form.claim_amount}
              onChange={(e) => setForm({ ...form, claim_amount: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>

          {/* Policy Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Policy Type
            </label>
            <select
              value={form.policy_type}
              onChange={(e) => setForm({ ...form, policy_type: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option value="comprehensive">Comprehensive</option>
              <option value="third-party">Third Party</option>
              <option value="own-damage">Own Damage</option>
            </select>
          </div>

          {/* Incident Description */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Incident Description <span className="text-red-500">*</span>
            </label>

            <textarea
              rows={3}
              placeholder="Describe what happened in detail..."
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />

            <div className="mt-2">
              <VoiceInput
                onTranscript={(text) => {
                  setForm({
                    ...form,
                    description: (form.description ? form.description + ' ' : '') + text
                  })
                }}
              />
            </div>
          </div>

          {/* Upload Damage Images */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Upload Damage Images (Max 5) <span className="text-red-500">*</span>
            </label>

            <div className="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={(e) => setFiles(Array.from(e.target.files).slice(0, 5))}
                className="hidden"
                id="file-upload"
              />

              <label htmlFor="file-upload" className="cursor-pointer">
                <div className="text-3xl mb-2">📸</div>
                <p className="text-sm text-gray-500">
                  {files.length > 0
                    ? `✅ ${files.length} image(s): ${files.map((f) => f.name).join(', ')}`
                    : 'Click to upload damage images (max 5)'}
                </p>
              </label>
            </div>
          </div>

          {/* Garage Estimate PDF */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Garage Estimate PDF <span className="text-gray-400">(Optional)</span>
            </label>

            <div className="border-2 border-dashed border-gray-200 rounded-lg p-4 text-center hover:border-green-400 transition-colors">
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setGaragePdf(e.target.files[0] || null)}
                className="hidden"
                id="garage-upload"
              />

              <label htmlFor="garage-upload" className="cursor-pointer">
                <div className="text-2xl mb-1">📄</div>
                <p className="text-sm text-gray-500">
                  {garagePdf ? `✅ ${garagePdf.name}` : 'Upload garage repair estimate (PDF)'}
                </p>
              </label>
            </div>
          </div>

          {/* Submit Button */}
          <div className="md:col-span-2">
            <button
              onClick={handleSubmit}
              disabled={
                loading ||
                verifiedVehicles.length === 0 ||
                !selectedVehicle ||
                isPolicyExpired(selectedVehicle)
              }
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '⏳ Processing AI Analysis...' : '🚀 Submit Claim'}
            </button>

            {isPolicyExpired(selectedVehicle) && (
              <p className="text-xs text-red-500 text-center mt-2">
                ❌ Cannot submit — policy expired!
              </p>
            )}
          </div>
        </div>
      ) : (
        /* Results View */
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <h3 className="text-green-700 font-bold text-lg mb-1">
              ✅ Claim Submitted!
            </h3>

            <p className="text-green-600">
              Claim ID: <strong>#{result.claim_id}</strong>
            </p>

            {result.garage_estimate_pdf && (
              <p className="text-green-600 text-sm mt-1">
                📄 Garage estimate uploaded
              </p>
            )}
          </div>

          <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
            <p className="text-xs text-blue-600 font-medium mb-1">AI Reason</p>
            <p className="text-sm text-blue-800">{result.ai_reason}</p>
          </div>

          {/* Explainable AI Risk Breakdown */}
          {result.xai_explanation &&
            (() => {
              try {
                const factors = JSON.parse(result.xai_explanation)
                return factors.length > 0 ? (
                  <div className="bg-white border border-gray-200 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-3">
                      <p className="font-bold text-gray-800">
                        🧠 Explainable AI Risk Breakdown
                      </p>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-bold ${
                          result.risk_level === 'CRITICAL'
                            ? 'bg-red-100 text-red-700'
                            : result.risk_level === 'HIGH'
                            ? 'bg-orange-100 text-orange-700'
                            : result.risk_level === 'MEDIUM'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-green-100 text-green-700'
                        }`}
                      >
                        {result.risk_level} RISK
                      </span>
                    </div>

                    <div className="space-y-2">
                      {factors.map((factor, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                        >
                          <div className="flex items-center gap-2">
                            <span>{factor.icon}</span>
                            <div>
                              <p className="text-xs font-medium text-gray-800">
                                {factor.factor}
                              </p>
                              <p className="text-xs text-gray-500">{factor.detail}</p>
                            </div>
                          </div>

                          <span className="text-xs font-bold text-red-600">
                            +{(factor.contribution * 100).toFixed(0)}%
                          </span>
                        </div>
                      ))}
                    </div>

                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-500">Total Fraud Risk</span>
                        <span className="font-bold">
                          {(result.fraud_score * 100).toFixed(0)}%
                        </span>
                      </div>

                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                          className={`h-3 rounded-full transition-all ${
                            result.fraud_score > 0.6
                              ? 'bg-red-500'
                              : result.fraud_score > 0.3
                              ? 'bg-amber-500'
                              : 'bg-green-500'
                          }`}
                          style={{
                            width: `${result.fraud_score * 100}%`
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ) : null
              } catch {
                return null
              }
            })()}

          {/* Consistency Check */}
          {result.consistency_status && (
            <div
              className={`border rounded-lg p-3 ${
                result.consistency_status === 'CONSISTENT'
                  ? 'bg-green-50 border-green-200'
                  : result.consistency_status === 'HIGHLY_INCONSISTENT'
                  ? 'bg-red-50 border-red-200'
                  : 'bg-yellow-50 border-yellow-200'
              }`}
            >
              <p className="text-xs font-medium mb-1">
                🔍 Claim Consistency Check: {result.consistency_status}
              </p>

              {result.consistency_issues &&
                (() => {
                  try {
                    const issues = JSON.parse(result.consistency_issues)
                    return issues.map((issue, i) => (
                      <p key={i} className="text-xs mt-1">
                        ⚠️ {issue.message}
                      </p>
                    ))
                  } catch {
                    return null
                  }
                })()}
            </div>
          )}

          {/* Heatmap */}
          {result.heatmap_image && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <p className="text-xs font-medium text-gray-700 mb-2">
                🌡️ Damage Heatmap
              </p>

              <img
                src={`http://127.0.0.1:8000/${result.heatmap_image}`}
                alt="Damage Heatmap"
                className="w-full rounded-lg"
              />

              <p className="text-xs text-gray-500 mt-1">
                🔴 Severe &nbsp; 🟠 Moderate &nbsp; 🟢 Minor
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default SubmitClaim