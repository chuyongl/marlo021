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
      await axios.post(`${API}/auth/register`, {
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name
      })

      const params = new URLSearchParams()
      params.append('username', formData.email)
      params.append('password', formData.password)
      const loginRes = await axios.post(`${API}/auth/login`, params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      const token = loginRes.data.access_token

      await axios.post(`${API}/businesses/`, {
        name: formData.business_name,
        industry: formData.industry,
        description: '',
        tone_of_voice: '',
        target_audience: '',
        monthly_ad_budget: formData.monthly_ad_budget
      }, { headers: { Authorization: `Bearer ${token}` } })

      window.location.href = '/setup'
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

        .signup-page {
          min-height: 100vh;
          background: #0a0a0a;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 24px;
          font-family: 'DM Sans', sans-serif;
        }
        .signup-logo {
          font-family: 'Instrument Serif', serif;
          font-size: 22px;
          color: #f0ece4;
          text-decoration: none;
          margin-bottom: 32px;
          letter-spacing: -0.5px;
        }
        .signup-logo span { color: #c8f060; }

        .signup-card {
          background: #141414;
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 24px;
          padding: 40px;
          width: 100%;
          max-width: 420px;
        }
        .signup-steps {
          display: flex;
          gap: 6px;
          margin-bottom: 32px;
        }
        .signup-step-dot {
          height: 3px;
          flex: 1;
          border-radius: 100px;
          background: rgba(255,255,255,0.1);
          transition: background 0.3s;
        }
        .signup-step-dot.active { background: #c8f060; }

        .signup-title {
          font-family: 'Instrument Serif', serif;
          font-size: 26px;
          color: #ffffff;
          margin-bottom: 6px;
          letter-spacing: -0.5px;
        }
        .signup-subtitle {
          font-size: 14px;
          color: #666;
          margin-bottom: 28px;
        }

        .signup-label {
          display: block;
          font-size: 13px;
          font-weight: 500;
          color: #888;
          margin-bottom: 6px;
        }
        .signup-input {
          width: 100%;
          background: #1a1a1a;
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 10px;
          padding: 12px 16px;
          font-size: 14px;
          color: #f0ece4;
          font-family: 'DM Sans', sans-serif;
          outline: none;
          transition: border-color 0.2s;
          margin-bottom: 16px;
        }
        .signup-input::placeholder { color: #444; }
        .signup-input:focus { border-color: rgba(200,240,96,0.4); }
        .signup-input option { background: #1a1a1a; color: #f0ece4; }

        .signup-btn-primary {
          width: 100%;
          background: #c8f060;
          color: #0a0a0a;
          border: none;
          border-radius: 10px;
          padding: 14px;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          font-family: 'DM Sans', sans-serif;
          transition: opacity 0.2s, transform 0.15s;
          margin-top: 4px;
        }
        .signup-btn-primary:hover:not(:disabled) { opacity: 0.88; transform: translateY(-1px); }
        .signup-btn-primary:disabled { opacity: 0.3; cursor: not-allowed; }

        .signup-btn-secondary {
          flex: 1;
          background: transparent;
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 10px;
          padding: 13px;
          font-size: 14px;
          font-weight: 500;
          color: #888;
          cursor: pointer;
          font-family: 'DM Sans', sans-serif;
          transition: border-color 0.2s, color 0.2s;
        }
        .signup-btn-secondary:hover { border-color: rgba(255,255,255,0.2); color: #f0ece4; }

        .signup-btn-row {
          display: flex;
          gap: 10px;
          margin-top: 4px;
        }
        .signup-btn-row .signup-btn-primary { flex: 2; margin-top: 0; }

        .budget-display {
          text-align: center;
          padding: 24px 0 16px;
        }
        .budget-amount {
          font-family: 'Instrument Serif', serif;
          font-size: 56px;
          color: #ffffff;
          letter-spacing: -2px;
          line-height: 1;
        }
        .budget-amount span { color: #c8f060; }
        .budget-period { font-size: 13px; color: #555; margin-top: 4px; }
        .budget-daily { font-size: 13px; color: #c8f060; margin-top: 4px; }

        .signup-range {
          width: 100%;
          accent-color: #c8f060;
          margin-bottom: 8px;
        }
        .budget-range-labels {
          display: flex;
          justify-content: space-between;
          font-size: 11px;
          color: #444;
          margin-bottom: 20px;
        }

        .signup-error {
          background: rgba(220,50,50,0.1);
          border: 1px solid rgba(220,50,50,0.2);
          border-radius: 8px;
          padding: 10px 14px;
          font-size: 13px;
          color: #ff6b6b;
          margin-bottom: 16px;
          text-align: center;
        }

        .signup-footer {
          text-align: center;
          margin-top: 20px;
          font-size: 12px;
          color: #444;
        }
        .signup-footer a { color: #666; text-decoration: underline; }
      `}</style>

      <div className="signup-page">
        <a className="signup-logo" href="/">marlo<span>.</span></a>

        <div className="signup-card">
          {/* Progress bar */}
          <div className="signup-steps">
            {[1, 2, 3].map(s => (
              <div key={s} className={`signup-step-dot ${s <= step ? 'active' : ''}`} />
            ))}
          </div>

          {step === 1 && (
            <div>
              <h2 className="signup-title">Let's start with you</h2>
              <p className="signup-subtitle">Create your Marlo account</p>
              <label className="signup-label">Your name</label>
              <input className="signup-input" placeholder="Mia Chen"
                value={formData.full_name} onChange={e => update('full_name', e.target.value)} />
              <label className="signup-label">Email</label>
              <input type="email" className="signup-input" placeholder="mia@miasbakery.com"
                value={formData.email} onChange={e => update('email', e.target.value)} />
              <label className="signup-label">Password</label>
              <input type="password" className="signup-input" placeholder="At least 8 characters"
                value={formData.password} onChange={e => update('password', e.target.value)} />
              <button className="signup-btn-primary"
                onClick={() => setStep(2)}
                disabled={!formData.full_name || !formData.email || formData.password.length < 8}>
                Continue →
              </button>
            </div>
          )}

          {step === 2 && (
            <div>
              <h2 className="signup-title">Now your business</h2>
              <p className="signup-subtitle">Tell Marlo who it's working for</p>
              <label className="signup-label">Business name</label>
              <input className="signup-input" placeholder="Mia's Bakery"
                value={formData.business_name} onChange={e => update('business_name', e.target.value)} />
              <label className="signup-label">Industry</label>
              <select className="signup-input"
                value={formData.industry} onChange={e => update('industry', e.target.value)}>
                <option value="">Select your industry</option>
                {INDUSTRIES.map(i => <option key={i} value={i}>{i}</option>)}
              </select>
              <div className="signup-btn-row">
                <button className="signup-btn-secondary" onClick={() => setStep(1)}>← Back</button>
                <button className="signup-btn-primary"
                  onClick={() => setStep(3)}
                  disabled={!formData.business_name || !formData.industry}>
                  Continue →
                </button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div>
              <h2 className="signup-title">Set your ad budget</h2>
              <p className="signup-subtitle">Marlo will never spend more than this. Change anytime by replying to any email.</p>

              <div className="budget-display">
                <div className="budget-amount"><span>$</span>{formData.monthly_ad_budget}</div>
                <div className="budget-period">per month</div>
                <div className="budget-daily">${(formData.monthly_ad_budget / 30).toFixed(0)}/day across all platforms</div>
              </div>

              <input type="range" min={50} max={2000} step={25}
                className="signup-range"
                value={formData.monthly_ad_budget}
                onChange={e => update('monthly_ad_budget', parseInt(e.target.value))} />
              <div className="budget-range-labels"><span>$50/mo</span><span>$2,000/mo</span></div>

              {error && <div className="signup-error">{error}</div>}

              <div className="signup-btn-row">
                <button className="signup-btn-secondary" onClick={() => setStep(2)}>← Back</button>
                <button className="signup-btn-primary" onClick={handleSubmit} disabled={loading}>
                  {loading ? 'Creating account...' : 'Start free trial →'}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="signup-footer">
          Already have an account? <a href="mailto:hello@marlo021.ai">Contact us</a>
        </div>
      </div>
    </>
  )
}