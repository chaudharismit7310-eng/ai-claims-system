import { useState } from 'react'
import axios from 'axios'
import { API_BASE_URL } from './config'

function Login({ onLogin }) {
    const [isRegister, setIsRegister] = useState(false)
    const [form, setForm] = useState({ name: '', email: '', password: '', role: 'customer' })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

    const handleSubmit = async () => {
        setLoading(true)
        setError('')
        try {
            if (isRegister) {
                await axios.post(`${API_BASE_URL}/auth/register`, form)
                setIsRegister(false)
                setError('✅ Registered! Please login now.')
            } else {
                const res = await axios.post(`${API_BASE_URL}/auth/login`, {
                    email: form.email,
                    password: form.password
                })
                onLogin(res.data)
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Something went wrong!')
        }
        setLoading(false)
    }

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="text-5xl mb-3">🚗</div>
                    <h2 className="text-2xl font-bold text-gray-800">AI Claims System</h2>
                    <p className="text-gray-500 text-sm mt-1">Insurance Validation Platform</p>
                </div>

                <div className="flex bg-gray-100 rounded-lg p-1 mb-6">
                    <button onClick={() => setIsRegister(false)}
                        className={`flex-1 py-2 rounded-md text-sm font-medium transition-all ${!isRegister ? 'bg-white text-blue-600 shadow' : 'text-gray-500'}`}>
                        Login
                    </button>
                    <button onClick={() => setIsRegister(true)}
                        className={`flex-1 py-2 rounded-md text-sm font-medium transition-all ${isRegister ? 'bg-white text-blue-600 shadow' : 'text-gray-500'}`}>
                        Register
                    </button>
                </div>

                {error && (
                    <div className={`px-4 py-3 rounded-lg mb-4 text-sm ${error.startsWith('✅') ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                        {error}
                    </div>
                )}

                <div className="space-y-4">
                    {isRegister && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                            <input name="name" onChange={handleChange}
                                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" />
                        </div>
                    )}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                        <input name="email" type="email" onChange={handleChange}
                            className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                        <input name="password" type="password" onChange={handleChange}
                            className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" />
                    </div>
                    {isRegister && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                            <select name="role" onChange={handleChange}
                                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm">
                                <option value="customer">Customer</option>
                                <option value="agent">Agent</option>
                                <option value="admin">Admin</option>
                            </select>
                        </div>
                    )}
                    <button onClick={handleSubmit} disabled={loading}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-lg transition-colors disabled:opacity-50">
                        {loading ? 'Please wait...' : isRegister ? 'Create Account' : 'Login'}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default Login