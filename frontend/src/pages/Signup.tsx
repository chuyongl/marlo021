import { useState } from 'react'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js'

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || '')

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

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [businessName, setBusinessName] = useState('')
  const [budget, setBudget] = useState('300')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [step, setStep] = useState<'account' | 'payment'>('account')

  const apiBase = process.env.REACT_APP_API_URL || 'https://api.marlo021.ai'

  const handleAccountSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password || !businessName) {
      setError('Please fill in all fields')
      return
    }
    setStep('payment')
    setError('')
  }

  const handlePaymentSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!stripe || !elements) return

    setLoading(true)
    setError('')

    try {
      // 1. Register user
      const registerRes = await fetch(`${apiBase}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: businessName })
      })

      if (!registerRes.ok) {
        const err = await registerRes.json()
        throw new Error(err.detail || 'Registration failed')
      }

      // 2. Login to get token
      const loginRes = await fetch(`${apiBase}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      const loginData = await loginRes.json()
      const token = loginData.access_token

      // 3. Create business
      const bizRes = await fetch(`${apiBase}/businesses/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: businessName,
          monthly_ad_budget: parseFloat(budget)
        })
      })
      const bizData = await bizRes.json()
      const businessId = bizData.id

      // 4. Create Stripe payment method
      const cardElement = elements.getElement(CardElement)
      if (!cardElement) throw new Error('Card element not found')

      const { error: stripeError, paymentMethod } = await stripe.createPaymentMethod({
        type: 'card',
        card: cardElement,
        billing_details: { email }
      })

      if (stripeError) throw new Error(stripeError.message)

      // 5. Create subscription
      const subRes = await fetch(`${apiBase}/billing/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: businessId,
          payment_method_id: paymentMethod!.id
        })
      })

      if (!subRes.ok) {
        const err = await subRes.json()
        throw new Error(err.detail || 'Subscription setup failed')
      }

      // 6. Redirect to setup page
      window.location.href = '/setup'

    } catch (err: any) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
        .signup-page { min-height:100vh; background:#0a0a0a; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:24px; font-family:'DM Sans',sans-serif; }
        .signup-logo { font-family:'Instrument Serif',serif; font-size:22px; color:#f0ece4; text-decoration:none; margin-bottom:48px; letter-spacing:-0.5px; }
        .signup-logo span { color:#c8f060; }
        .signup-card { background:#141414; border:1px solid rgba(255,255,255,0.08); border-radius:24px; padding:40px; width:100%; max-width:420px; }
        .signup-card h1 { font-family:'Instrument Serif',serif; font-size:28px; color:#fff; margin-bottom:8px; letter-spacing:-0.5px; }
        .signup-subtitle { font-size:14px; color:#666; margin-bottom:32px; line-height:1.6; }
        .signup-label { font-size:13px; font-weight:500; color:#888; margin-bottom:6px; display:block; }
        .signup-input { width:100%; background:#1a1a1a; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:12px 14px; font-size:15px; color:#f0ece4; outline:none; font-family:'DM Sans',sans-serif; transition:border-color 0.2s; box-sizing:border-box; }
        .signup-input:focus { border-color:rgba(200,240,96,0.4); }
        .signup-field { margin-bottom:16px; }
        .signup-card-field { background:#1a1a1a; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:14px; margin-bottom:16px; }
        .signup-btn { width:100%; background:#c8f060; color:#0a0a0a; border:none; border-radius:10px; padding:15px; font-size:16px; font-weight:700; cursor:pointer; font-family:'DM Sans',sans-serif; transition:opacity 0.2s; margin-top:8px; }
        .signup-btn:hover { opacity:0.88; }
        .signup-btn:disabled { opacity:0.5; cursor:not-allowed; }
        .signup-error { background:rgba(248,113,113,0.1); border:1px solid rgba(248,113,113,0.3); border-radius:8px; padding:12px 14px; font-size:13px; color:#f87171; margin-bottom:16px; }
        .signup-trial-badge { background:rgba(200,240,96,0.08); border:1px solid rgba(200,240,96,0.15); border-radius:8px; padding:12px 14px; font-size:13px; color:#c8f060; margin-bottom:24px; line-height:1.6; }
        .signup-security { font-size:12px; color:#444; text-align:center; margin-top:16px; line-height:1.6; }
        .signup-back { background:none; border:none; color:#666; font-size:13px; cursor:pointer; margin-bottom:20px; padding:0; font-family:'DM Sans',sans-serif; }
        .signup-back:hover { color:#f0ece4; }
        .signup-progress { display:flex; gap:8px; margin-bottom:28px; }
        .signup-step { height:2px; flex:1; border-radius:2px; background:rgba(255,255,255,0.08); }
        .signup-step.active { background:#c8f060; }
        .signup-login { font-size:13px; color:#555; text-align:center; margin-top:20px; }
        .signup-login a { color:#c8f060; text-decoration:none; }
      `}</style>

      <div className="signup-page">
        <a className="signup-logo" href="/">marlo<span>021.</span></a>

        <div className="signup-card">
          <div className="signup-progress">
            <div className={`signup-step ${step === 'account' || step === 'payment' ? 'active' : ''}`} />
            <div className={`signup-step ${step === 'payment' ? 'active' : ''}`} />
          </div>

          {step === 'account' ? (
            <form onSubmit={handleAccountSubmit}>
              <h1>Start your free trial</h1>
              <p className="signup-subtitle">14 days free, then $99/month. Cancel anytime.</p>

              {error && <div className="signup-error">{error}</div>}

              <div className="signup-field">
                <label className="signup-label">Business name</label>
                <input className="signup-input" type="text" placeholder="Anna's Café" value={businessName} onChange={e => setBusinessName(e.target.value)} required />
              </div>
              <div className="signup-field">
                <label className="signup-label">Email address</label>
                <input className="signup-input" type="email" placeholder="you@yourbusiness.com" value={email} onChange={e => setEmail(e.target.value)} required />
              </div>
              <div className="signup-field">
                <label className="signup-label">Password</label>
                <input className="signup-input" type="password" placeholder="At least 8 characters" value={password} onChange={e => setPassword(e.target.value)} required minLength={8} />
              </div>
              <div className="signup-field">
                <label className="signup-label">Monthly ad budget (USD)</label>
                <input className="signup-input" type="number" placeholder="300" value={budget} onChange={e => setBudget(e.target.value)} min="50" />
              </div>

              <button className="signup-btn" type="submit">Continue →</button>

              <p className="signup-login">Already have an account? <a href="/login">Log in</a></p>
            </form>
          ) : (
            <form onSubmit={handlePaymentSubmit}>
              <button className="signup-back" type="button" onClick={() => setStep('account')}>← Back</button>
              <h1>Add your card</h1>
              <p className="signup-subtitle">No charge today. Your trial starts now.</p>

              <div className="signup-trial-badge">
                🎉 <strong>14-day free trial</strong> — your card won't be charged until {new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}.<br />
                We'll send you a reminder 3 days before your trial ends.
              </div>

              {error && <div className="signup-error">{error}</div>}

              <label className="signup-label">Card details</label>
              <div className="signup-card-field">
                <CardElement options={CARD_ELEMENT_OPTIONS} />
              </div>

              <button className="signup-btn" type="submit" disabled={loading || !stripe}>
                {loading ? 'Setting up...' : 'Start free trial →'}
              </button>

              <p className="signup-security">
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