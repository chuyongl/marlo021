import { useState } from 'react'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js'

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || '')

const INDUSTRIES = [
  'Food & Beverage', 'Retail', 'Health & Beauty', 'Fitness & Wellness',
  'Professional Services', 'Home Services', 'Arts & Entertainment',
  'Pet Services', 'Automotive', 'Other'
]

const CARD_ELEMENT_OPTIONS = {
  style: {
    base: {
      fontSize: '15px',
      color: '#f0ece4',
      fontFamily: "'DM Sans', sans-serif",
      '::placeholder': { color: '#555' },
      backgroundColor: 'transparent',
    },
    invalid: { color: '#f87171' },
  },
}

function SignupForm() {
  const stripe = useStripe()
  const elements = useElements()

  const [step, setStep] = useState<1 | 2 | 3>(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [businessId, setBusinessId] = useState('')

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    business_name: '',
    industry: '',
    monthly_ad_budget: 300,
  })

  const apiBase = process.env.REACT_APP_API_URL || 'https://api.marlo021.ai'
  const update = (key: string, value: any) =>
    setFormData(prev => ({ ...prev, [key]: value }))

  const handleStep1 = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.full_name || !formData.email || !formData.password) {
      setError('Please fill in all fields')
      return
    }
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }
    setError('')
    setStep(2)
  }

  const handleStep2 = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.business_name || !formData.industry) {
      setError('Please fill in all fields')
      return
    }
    setLoading(true)
    setError('')
    try {
      // 1. Register user
      const registerRes = await fetch(`${apiBase}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name,
        }),
      })
      if (!registerRes.ok) {
        const err = await registerRes.json()
        throw new Error(err.detail || 'Registration failed')
      }

      // 2. Login — backend expects form-urlencoded with 'username' field (OAuth2 standard)
      const loginParams = new URLSearchParams()
      loginParams.append('username', formData.email)
      loginParams.append('password', formData.password)
      const loginRes = await fetch(`${apiBase}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: loginParams,
      })
      if (!loginRes.ok) throw new Error('Login failed')
      const loginData = await loginRes.json()
      const token = loginData.access_token
      localStorage.setItem('token', token)

      // 3. Create business
      const bizRes = await fetch(`${apiBase}/businesses/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: formData.business_name,
          industry: formData.industry,
          monthly_ad_budget: formData.monthly_ad_budget,
        }),
      })
      if (!bizRes.ok) {
        const err = await bizRes.json()
        throw new Error(Array.isArray(err.detail) ? JSON.stringify(err.detail) : (err.detail || 'Business creation failed'))
      }
      const bizData = await bizRes.json()
      setBusinessId(bizData.id)
      setStep(3)
    } catch (err: any) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const handleStep3 = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!stripe || !elements) return
    setLoading(true)
    setError('')
    try {
      const cardElement = elements.getElement(CardElement)
      if (!cardElement) throw new Error('Card element not found')

      const { error: stripeError, paymentMethod } = await stripe.createPaymentMethod({
        type: 'card',
        card: cardElement,
        billing_details: { email: formData.email },
      })
      if (stripeError) throw new Error(stripeError.message)

      const subRes = await fetch(`${apiBase}/billing/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: businessId,
          payment_method_id: paymentMethod!.id,
        }),
      })
      if (!subRes.ok) {
        const err = await subRes.json()
        throw new Error(err.detail || 'Subscription setup failed')
      }

      window.location.href = '/setup'
    } catch (err: any) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const trialEndDate = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000)
    .toLocaleDateString('en-US', { month: 'long', day: 'numeric' })

  const budgetPct = ((formData.monthly_ad_budget - 50) / 1950) * 100

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
        .su-page { min-height:100vh; background:#0a0a0a; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:24px; font-family:'DM Sans',sans-serif; }
        .su-logo { font-family:'Instrument Serif',serif; font-size:22px; color:#f0ece4; text-decoration:none; margin-bottom:40px; letter-spacing:-0.5px; }
        .su-logo span { color:#c8f060; }
        .su-card { background:#141414; border:1px solid rgba(255,255,255,0.08); border-radius:24px; padding:40px; width:100%; max-width:440px; }
        .su-progress { display:flex; gap:6px; margin-bottom:28px; }
        .su-prog-step { height:2px; flex:1; border-radius:2px; background:rgba(255,255,255,0.08); transition:background 0.3s; }
        .su-prog-step.done { background:#c8f060; }
        .su-card h1 { font-family:'Instrument Serif',serif; font-size:28px; color:#fff; margin:0 0 6px 0; letter-spacing:-0.5px; }
        .su-subtitle { font-size:14px; color:#666; margin:0 0 28px 0; line-height:1.6; }
        .su-label { font-size:13px; font-weight:500; color:#888; margin-bottom:6px; display:block; }
        .su-input { width:100%; background:#1a1a1a; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:12px 14px; font-size:15px; color:#f0ece4; outline:none; font-family:'DM Sans',sans-serif; transition:border-color 0.2s; box-sizing:border-box; }
        .su-input:focus { border-color:rgba(200,240,96,0.4); }
        .su-select { width:100%; background:#1a1a1a; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:12px 14px; font-size:15px; color:#f0ece4; outline:none; font-family:'DM Sans',sans-serif; cursor:pointer; appearance:none; -webkit-appearance:none; box-sizing:border-box; }
        .su-select:focus { border-color:rgba(200,240,96,0.4); }
        .su-field { margin-bottom:16px; }
        .su-budget-display { text-align:center; margin:12px 0 8px; }
        .su-budget-amount { font-family:'Instrument Serif',serif; font-size:52px; color:#ffffff; letter-spacing:-2px; line-height:1; }
        .su-budget-period { font-size:14px; color:#666; margin-top:4px; }
        .su-budget-note { font-size:12px; color:#c8f060; margin-top:4px; }
        .su-range { width:100%; -webkit-appearance:none; appearance:none; height:4px; border-radius:2px; outline:none; margin:12px 0 6px; cursor:pointer; }
        .su-range::-webkit-slider-thumb { -webkit-appearance:none; width:20px; height:20px; border-radius:50%; background:#c8f060; cursor:pointer; border:3px solid #0a0a0a; box-shadow:0 0 0 1px rgba(200,240,96,0.3); }
        .su-range::-moz-range-thumb { width:20px; height:20px; border-radius:50%; background:#c8f060; cursor:pointer; border:3px solid #0a0a0a; }
        .su-range-labels { display:flex; justify-content:space-between; font-size:11px; color:#555; margin-bottom:16px; }
        .su-btn { width:100%; background:#c8f060; color:#0a0a0a; border:none; border-radius:10px; padding:15px; font-size:16px; font-weight:700; cursor:pointer; font-family:'DM Sans',sans-serif; transition:opacity 0.2s; margin-top:8px; }
        .su-btn:hover { opacity:0.88; }
        .su-btn:disabled { opacity:0.5; cursor:not-allowed; }
        .su-back { background:none; border:none; color:#666; font-size:13px; cursor:pointer; padding:0; font-family:'DM Sans',sans-serif; margin-bottom:20px; transition:color 0.2s; display:block; }
        .su-back:hover { color:#f0ece4; }
        .su-error { background:rgba(248,113,113,0.1); border:1px solid rgba(248,113,113,0.3); border-radius:8px; padding:12px 14px; font-size:13px; color:#f87171; margin-bottom:16px; }
        .su-trial-badge { background:rgba(200,240,96,0.06); border:1px solid rgba(200,240,96,0.15); border-radius:8px; padding:14px 16px; font-size:13px; color:#a3c040; margin-bottom:20px; line-height:1.7; }
        .su-trial-badge strong { color:#c8f060; }
        .su-card-field { background:#1a1a1a; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:14px; margin-bottom:16px; }
        .su-security { font-size:12px; color:#444; text-align:center; margin-top:16px; line-height:1.7; }
        .su-login { font-size:13px; color:#555; text-align:center; margin-top:20px; }
        .su-login a { color:#c8f060; text-decoration:none; }
      `}</style>

      <div className="su-page">
        <a className="su-logo" href="/">marlo<span>021.</span></a>

        <div className="su-card">
          <div className="su-progress">
            {([1, 2, 3] as const).map(s => (
              <div key={s} className={`su-prog-step ${step >= s ? 'done' : ''}`} />
            ))}
          </div>

          {step === 1 && (
            <form onSubmit={handleStep1}>
              <h1>Start your free trial</h1>
              <p className="su-subtitle">14 days free, then $99/month. Cancel anytime.</p>
              {error && <div className="su-error">{error}</div>}
              <div className="su-field">
                <label className="su-label">Your name</label>
                <input className="su-input" type="text" placeholder="Anna Liu"
                  value={formData.full_name} onChange={e => update('full_name', e.target.value)} required />
              </div>
              <div className="su-field">
                <label className="su-label">Email address</label>
                <input className="su-input" type="email" placeholder="you@yourbusiness.com"
                  value={formData.email} onChange={e => update('email', e.target.value)} required />
              </div>
              <div className="su-field">
                <label className="su-label">Password</label>
                <input className="su-input" type="password" placeholder="At least 8 characters"
                  value={formData.password} onChange={e => update('password', e.target.value)} required minLength={8} />
              </div>
              <button className="su-btn" type="submit">Continue →</button>
              <p className="su-login">Already have an account? <a href="/login">Log in</a></p>
            </form>
          )}

          {step === 2 && (
            <form onSubmit={handleStep2}>
              <button className="su-back" type="button" onClick={() => { setStep(1); setError('') }}>← Back</button>
              <h1>Your business</h1>
              <p className="su-subtitle">Tell Marlo what you do and your ad budget.</p>
              {error && <div className="su-error">{error}</div>}
              <div className="su-field">
                <label className="su-label">Business name</label>
                <input className="su-input" type="text" placeholder="Anna's Café"
                  value={formData.business_name} onChange={e => update('business_name', e.target.value)} required />
              </div>
              <div className="su-field">
                <label className="su-label">Industry</label>
                <select className="su-select" value={formData.industry}
                  onChange={e => update('industry', e.target.value)} required>
                  <option value="">Select your industry</option>
                  {INDUSTRIES.map(i => <option key={i} value={i}>{i}</option>)}
                </select>
              </div>
              <div className="su-field">
                <label className="su-label">Monthly ad budget</label>
                <div className="su-budget-display">
                  <div className="su-budget-amount">${formData.monthly_ad_budget}</div>
                  <div className="su-budget-period">per month</div>
                  <div className="su-budget-note">
                    ${(formData.monthly_ad_budget / 30).toFixed(0)}/day across all platforms
                  </div>
                </div>
                <input
                  type="range" min="50" max="2000" step="50"
                  className="su-range"
                  style={{
                    background: `linear-gradient(to right, #c8f060 ${budgetPct}%, rgba(255,255,255,0.1) ${budgetPct}%)`
                  }}
                  value={formData.monthly_ad_budget}
                  onChange={e => update('monthly_ad_budget', parseInt(e.target.value))}
                />
                <div className="su-range-labels"><span>$50/mo</span><span>$2,000/mo</span></div>
              </div>
              <button className="su-btn" type="submit" disabled={loading}>
                {loading ? 'Setting up...' : 'Continue →'}
              </button>
            </form>
          )}

          {step === 3 && (
            <form onSubmit={handleStep3}>
              <button className="su-back" type="button" onClick={() => { setStep(2); setError('') }}>← Back</button>
              <h1>Add your card</h1>
              <p className="su-subtitle">No charge today. Your trial starts now.</p>
              <div className="su-trial-badge">
                🎉 <strong>14-day free trial</strong> — your card won't be charged until {trialEndDate}.<br />
                We'll send you a reminder 3 days before your trial ends.
              </div>
              {error && <div className="su-error">{error}</div>}
              <label className="su-label">Card details</label>
              <div className="su-card-field">
                <CardElement options={CARD_ELEMENT_OPTIONS} />
              </div>
              <button className="su-btn" type="submit" disabled={loading || !stripe}>
                {loading ? 'Setting up...' : 'Start free trial →'}
              </button>
              <p className="su-security">
                🔒 Secured by Stripe. We never store your card details.<br />
                Cancel anytime by replying "Cancel my Marlo021 subscription"
              </p>
            </form>
          )}
        </div>
      </div>
    </>
  )
}

export function Signup() {
  return (
    <Elements stripe={stripePromise}>
      <SignupForm />
    </Elements>
  )
}