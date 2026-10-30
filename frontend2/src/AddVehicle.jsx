import { useState } from 'react'
import axios from 'axios'
import { API_BASE_URL } from './config'

function AddVehicle({ onSuccess }) {
    const [form, setForm] = useState({
        vehicle_number: '', car_model: '',
        policy_number: '', policy_expiry_date: ''
    })
    const [rcFile, setRcFile] = useState(null)
    const [policyFile, setPolicyFile] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const token = localStorage.getItem('token')

    const handleSubmit = async () => {
        if (!rcFile || !policyFile) {
            setError('Please upload RC and Policy documents!')
            return
        }
        setLoading(true)
        setError('')
        try {
            const formData = new FormData()
            Object.entries(form).forEach(([k, v]) => formData.append(k, v))
            formData.append('rc_document', rcFile)
            formData.append('policy_document', policyFile)

            await axios.post(`${API_BASE_URL}/vehicles/add`, formData, {
                headers: { Authorization: `Bearer ${token}` }
            })
            onSuccess()
        } catch (err) {
            setError(err.response?.data?.detail || 'Error adding vehicle!')
        }
        setLoading(false)
    }

    return (
        <div className="bg-white rounded-2xl border border-gray-100 p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4">Add New Vehicle</h3>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                    { name: 'vehicle_number', label: 'Vehicle Number', placeholder: 'MH12AB1234' },
                    { name: 'car_model', label: 'Car Model', placeholder: 'Honda City' },
                    { name: 'policy_number', label: 'Policy Number', placeholder: 'POL001' },
                ].map(field => (
                    <div key={field.name}>
                        <label className="block text-sm font-medium text-gray-700 mb-1">{field.label}</label>
                        <input
                            placeholder={field.placeholder}
                            onChange={e => setForm({ ...form, [field.name]: e.target.value })}
                            className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                        />
                    </div>
                ))}

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Policy Expiry Date</label>
                    <input
                        type="date"
                        onChange={e => setForm({ ...form, policy_expiry_date: e.target.value })}
                        className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">RC Book (PDF/Image)</label>
                    <div className="border-2 border-dashed border-gray-200 rounded-lg p-4 text-center hover:border-blue-400 transition-colors">
                        <input type="file" accept=".pdf,.jpg,.jpeg,.png"
                            onChange={e => setRcFile(e.target.files[0])}
                            className="hidden" id="rc-upload" />
                        <label htmlFor="rc-upload" className="cursor-pointer">
                            <div className="text-2xl mb-1">📄</div>
                            <p className="text-xs text-gray-500">{rcFile ? rcFile.name : 'Upload RC Book'}</p>
                        </label>
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Insurance Policy Doc</label>
                    <div className="border-2 border-dashed border-gray-200 rounded-lg p-4 text-center hover:border-blue-400 transition-colors">
                        <input type="file" accept=".pdf,.jpg,.jpeg,.png"
                            onChange={e => setPolicyFile(e.target.files[0])}
                            className="hidden" id="policy-upload" />
                        <label htmlFor="policy-upload" className="cursor-pointer">
                            <div className="text-2xl mb-1">📋</div>
                            <p className="text-xs text-gray-500">{policyFile ? policyFile.name : 'Upload Policy Doc'}</p>
                        </label>
                    </div>
                </div>

                <div className="md:col-span-2">
                    <button onClick={handleSubmit} disabled={loading}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg transition-colors disabled:opacity-50">
                        {loading ? '⏳ Submitting...' : '🚗 Add Vehicle'}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default AddVehicle