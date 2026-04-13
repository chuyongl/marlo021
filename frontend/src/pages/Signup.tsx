import { useState } from 'react'
import axios from 'axios'

const API = 'https://api.marlo021.ai'

const INDUSTRIES = [
  'Food & Beverage', 'Retail', 'Health & Beauty', 'Fitness & Wellness',
  'Professional Services', 'Home Services', 'Arts & Entertainment',
  'Pet Services', 'Automotive', 'Other'
]

export function Signup() {
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    full_name: '', email: '', password: '',
    business_name: '', industry: '',
    monthly_ad_budget: 300
  })

  const update = (key: string, value: any) =>
    setFormData(prev => ({...prev, [key]: value}))

  const handleSubmit = async () => {
    setLoading(true)
    setError('')
    try {
      // 1. Create user account
      await axios.post(`${API}/auth/register`, {
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name
      })

      // 2. Login
      const params = new URLSearchParams()
      params.append('username', formData.email)
      params.append('password', formData.password)
      const loginRes = await axios.post(`${API}/auth/login`, params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      const token = loginRes.data.access_token

      // 3. Create business (triggers onboarding email 1)
      await axios.post(`${API}/businesses/`, {
        name: formData.business_name,
        industry: formData.industry,
        description: '',
        tone_of_voice: '',
        target_audience: '',
        monthly_ad_budget: formData.monthly_ad_budget
      }, { headers: { Authorization: `Bearer ${token}` } })

      // 4. Show success
      window.location.href = '/setup'
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 w-full max-w-md">

        <div className="text-center mb-8">
          <div className="text-2xl font-bold text-blue-600 mb-1">Marlo</div>
          <p className="text-gray-500 text-sm">Your AI marketing team — just email</p>
        </div>

        {/* Progress dots */}
        <div className="flex justify-center gap-2 mb-8">
          {[1, 2, 3].map(s => (
            <div key={s} className={`h-2 w-8 rounded-full transition-all ${s <= step ? 'bg-blue-500' : 'bg-gray-200'}`} />
          ))}
        </div>

        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">Let's start with you</h2>
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">Your name</label>
              <input className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Mia Chen" value={formData.full_name}
                onChange={e => update('full_name', e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">Email</label>
              <input type="email" className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="mia@miasbakery.com" value={formData.email}
                onChange={e => update('email', e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">Password</label>
              <input type="password" className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="At least 8 characters" value={formData.password}
                onChange={e => update('password', e.target.value)} />
            </div>
            <button onClick={() => setStep(2)}
              disabled={!formData.full_name || !formData.email || formData.password.length < 8}
              className="w-full bg-blue-600 text-white rounded-xl py-3 font-medium hover:bg-blue-700 disabled:opacity-40 transition-colors mt-2">
              Continue →
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">Now your business</h2>
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">Business name</label>
              <input className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Mia's Bakery" value={formData.business_name}
                onChange={e => update('business_name', e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">Industry</label>
              <select className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                value={formData.industry} onChange={e => update('industry', e.target.value)}>
                <option value="">Select your industry</option>
                {INDUSTRIES.map(i => <option key={i} value={i}>{i}</option>)}
              </select>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setStep(1)} className="flex-1 border border-gray-200 rounded-xl py-3 text-sm font-medium text-gray-600 hover:bg-gray-50">← Back</button>
              <button onClick={() => setStep(3)} disabled={!formData.business_name || !formData.industry}
                className="flex-1 bg-blue-600 text-white rounded-xl py-3 font-medium hover:bg-blue-700 disabled:opacity-40 transition-colors">
                Continue →
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold">Set your monthly budget</h2>
            <p className="text-sm text-gray-500">Marlo will never spend more than this across all your ads. You can change it anytime by replying to any email.</p>

            <div className="text-center py-4">
              <div className="text-5xl font-bold text-gray-900">${formData.monthly_ad_budget}</div>
              <div className="text-gray-400 text-sm mt-1">per month</div>
              <div className="text-blue-600 text-sm mt-1">${(formData.monthly_ad_budget / 30).toFixed(0)}/day across all platforms</div>
            </div>

            <input type="range" min={50} max={2000} step={25}
              value={formData.monthly_ad_budget}
              onChange={e => update('monthly_ad_budget', parseInt(e.target.value))}
              className="w-full accent-blue-600" />

            <div className="flex justify-between text-xs text-gray-400">
              <span>$50/mo</span><span>$2,000/mo</span>
            </div>

            {error && <p className="text-red-500 text-sm text-center">{error}</p>}

            <div className="flex gap-3">
              <button onClick={() => setStep(2)} className="flex-1 border border-gray-200 rounded-xl py-3 text-sm font-medium text-gray-600 hover:bg-gray-50">← Back</button>
              <button onClick={handleSubmit} disabled={loading}
                className="flex-1 bg-blue-600 text-white rounded-xl py-3 font-medium hover:bg-blue-700 disabled:opacity-40 transition-colors">
                {loading ? 'Creating account...' : 'Start free trial →'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}