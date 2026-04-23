import { useEffect } from 'react'

export function Landing() {
  useEffect(() => {
    // Inject Google Fonts
    const link1 = document.createElement('link')
    link1.rel = 'preconnect'
    link1.href = 'https://fonts.googleapis.com'
    document.head.appendChild(link1)

    const link2 = document.createElement('link')
    link2.rel = 'stylesheet'
    link2.href = 'https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap'
    document.head.appendChild(link2)

    // FAQ toggle function
    ;(window as any).toggleFaq = function(el: HTMLElement) {
      const item = el.closest('.faq-item') as HTMLElement
      const isOpen = item.classList.contains('open')
      document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'))
      if (!isOpen) item.classList.add('open')
    }

    // Scroll animations
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) e.target.classList.add('visible')
      })
    }, { threshold: 0.1 })
    document.querySelectorAll('.fade-in').forEach(el => observer.observe(el))

    return () => { observer.disconnect() }
  }, [])

  return (
    <>
      <style>{`
        :root {
          --bg: #0a0a0a; --bg2: #111111; --bg3: #181818;
          --border: rgba(255,255,255,0.08); --text: #f0ece4;
          --muted: #888; --accent: #c8f060; --accent2: #f5a623;
          --white: #ffffff; --card-bg: #141414;
        }
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        html { scroll-behavior: smooth; }
        body { background: var(--bg); color: var(--text); font-family: 'DM Sans', sans-serif; font-size: 16px; line-height: 1.6; overflow-x: hidden; }

        /* NAV */
        nav { position: fixed; top: 0; left: 0; right: 0; z-index: 100; display: flex; align-items: center; justify-content: space-between; padding: 20px 48px; background: rgba(10,10,10,0.85); backdrop-filter: blur(16px); border-bottom: 1px solid var(--border); }
        .logo { font-family: 'Instrument Serif', serif; font-size: 24px; color: var(--text); text-decoration: none; letter-spacing: -0.5px; }
        .logo span { color: var(--accent); }
        nav a.nav-link { color: var(--muted); text-decoration: none; font-size: 14px; font-weight: 500; transition: color 0.2s; }
        nav a.nav-link:hover { color: var(--text); }
        .nav-links { display: flex; gap: 32px; align-items: center; }
        .nav-cta { background: var(--accent); color: #0a0a0a; padding: 10px 22px; border-radius: 8px; font-size: 14px; font-weight: 600; text-decoration: none; transition: opacity 0.2s, transform 0.15s; }
        .nav-cta:hover { opacity: 0.88; transform: translateY(-1px); }

        /* HERO */
        .hero { min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 120px 24px 80px; position: relative; overflow: hidden; }
        .hero-glow { position: absolute; top: 20%; left: 50%; transform: translateX(-50%); width: 700px; height: 400px; background: radial-gradient(ellipse, rgba(200,240,96,0.12) 0%, transparent 70%); pointer-events: none; }
        .hero-badge { display: inline-flex; align-items: center; gap: 8px; background: rgba(200,240,96,0.1); border: 1px solid rgba(200,240,96,0.25); border-radius: 100px; padding: 6px 16px; font-size: 13px; font-weight: 500; color: var(--accent); margin-bottom: 32px; animation: fadeUp 0.6s ease both; }
        .badge-dot { width: 6px; height: 6px; background: var(--accent); border-radius: 50%; animation: pulse 2s ease infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        .hero h1 { font-family: 'Instrument Serif', serif; font-size: clamp(44px, 7vw, 88px); line-height: 1.05; letter-spacing: -2px; color: var(--white); max-width: 860px; margin-bottom: 28px; animation: fadeUp 0.7s 0.1s ease both; }
        .hero h1 em { font-style: italic; color: var(--accent); }
        .hero-sub { font-size: clamp(17px, 2.2vw, 20px); color: var(--muted); max-width: 520px; line-height: 1.6; margin-bottom: 44px; animation: fadeUp 0.7s 0.2s ease both; }
        .hero-actions { display: flex; gap: 14px; align-items: center; flex-wrap: wrap; justify-content: center; animation: fadeUp 0.7s 0.3s ease both; }
        .btn-primary { background: var(--accent); color: #0a0a0a; padding: 15px 32px; border-radius: 10px; font-size: 16px; font-weight: 600; text-decoration: none; transition: opacity 0.2s, transform 0.15s; }
        .btn-primary:hover { opacity: 0.88; transform: translateY(-2px); }
        .btn-ghost { color: var(--muted); font-size: 15px; font-weight: 500; text-decoration: none; display: flex; align-items: center; gap: 6px; transition: color 0.2s; }
        .btn-ghost:hover { color: var(--text); }
        .hero-social-proof { margin-top: 56px; animation: fadeUp 0.7s 0.4s ease both; display: flex; flex-direction: column; align-items: center; gap: 12px; }
        .hero-social-proof p { font-size: 13px; color: var(--muted); }
        .avatars { display: flex; align-items: center; }
        .avatar { width: 32px; height: 32px; border-radius: 50%; border: 2px solid var(--bg); margin-left: -8px; font-size: 13px; display: flex; align-items: center; justify-content: center; font-weight: 600; background: var(--bg3); color: var(--text); }
        .avatar:first-child { margin-left: 0; }
        .avatar-row { display: flex; align-items: center; gap: 10px; }

        /* PHONE SECTION */
        .phone-section { padding: 80px 24px 100px; display: flex; flex-direction: column; align-items: center; gap: 64px; }
        .section-label { font-size: 12px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; color: var(--accent); margin-bottom: 12px; }
        .section-title { font-family: 'Instrument Serif', serif; font-size: clamp(32px, 5vw, 54px); line-height: 1.1; letter-spacing: -1px; color: var(--white); text-align: center; max-width: 600px; margin: 0 auto 16px; }
        .section-sub { font-size: 17px; color: var(--muted); text-align: center; max-width: 480px; margin: 0 auto; }
        .phone-wrapper { position: relative; display: flex; align-items: flex-start; gap: 32px; flex-wrap: wrap; justify-content: center; }
        .phone-frame { width: 280px; background: #1a1a1a; border-radius: 40px; border: 2px solid rgba(255,255,255,0.12); overflow: hidden; box-shadow: 0 40px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.04); flex-shrink: 0; }
        .phone-notch { width: 100%; height: 32px; background: #1a1a1a; display: flex; align-items: center; justify-content: center; padding-top: 8px; }
        .phone-notch-pill { width: 80px; height: 18px; background: #0a0a0a; border-radius: 100px; }
        .phone-screen { background: #f5f5f0; padding: 0; min-height: 480px; }
        .email-header { background: white; padding: 16px 16px 12px; border-bottom: 1px solid #eee; }
        .email-from { font-size: 11px; color: #999; margin-bottom: 2px; font-family: 'DM Sans', sans-serif; }
        .email-subject { font-size: 13px; font-weight: 700; color: #1a1a1a; font-family: 'DM Sans', sans-serif; }
        .email-body { padding: 16px; background: #f9f9f6; }
        .email-greeting { font-size: 13px; color: #333; margin-bottom: 10px; font-family: 'DM Sans', sans-serif; line-height: 1.5; }
        .email-metric-row { display: flex; gap: 8px; margin-bottom: 12px; }
        .email-metric { flex: 1; background: white; border-radius: 8px; padding: 10px 8px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
        .email-metric-num { font-size: 16px; font-weight: 700; color: #1a1a1a; font-family: 'DM Sans', sans-serif; }
        .email-metric-num.green { color: #2d9654; }
        .email-metric-label { font-size: 9px; color: #999; font-family: 'DM Sans', sans-serif; margin-top: 2px; }
        .email-plan-title { font-size: 11px; font-weight: 600; color: #555; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; font-family: 'DM Sans', sans-serif; }
        .email-plan-item { background: white; border-radius: 8px; padding: 10px 12px; margin-bottom: 6px; font-size: 12px; color: #333; font-family: 'DM Sans', sans-serif; line-height: 1.4; box-shadow: 0 1px 3px rgba(0,0,0,0.06); display: flex; align-items: flex-start; gap: 8px; }
        .email-cta-row { display: flex; gap: 8px; margin-top: 14px; }
        .email-btn-approve { flex: 2; background: #1a1a1a; color: white; border: none; border-radius: 8px; padding: 12px 0; font-size: 13px; font-weight: 600; cursor: pointer; font-family: 'DM Sans', sans-serif; }
        .email-btn-decline { flex: 1; background: white; color: #999; border: 1px solid #ddd; border-radius: 8px; padding: 12px 0; font-size: 13px; cursor: pointer; font-family: 'DM Sans', sans-serif; }
        .phone-callouts { display: flex; flex-direction: column; gap: 20px; max-width: 280px; padding-top: 60px; }
        .callout { background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px; padding: 18px 20px; }
        .callout-emoji { font-size: 20px; margin-bottom: 6px; }
        .callout-title { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
        .callout-body { font-size: 12px; color: var(--muted); line-height: 1.5; }

        /* HOW IT WORKS */
        .how-section { padding: 80px 24px 100px; max-width: 1100px; margin: 0 auto; }
        .steps-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px; margin-top: 56px; background: var(--border); border-radius: 20px; overflow: hidden; }
        .step { background: var(--card-bg); padding: 40px 36px; position: relative; transition: background 0.3s; }
        .step:hover { background: var(--bg3); }
        .step-number { font-family: 'Instrument Serif', serif; font-size: 64px; color: rgba(255,255,255,0.04); position: absolute; top: 20px; right: 24px; line-height: 1; }
        .step-icon { width: 48px; height: 48px; background: rgba(200,240,96,0.1); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; margin-bottom: 20px; }
        .step h3 { font-family: 'Instrument Serif', serif; font-size: 22px; color: var(--white); margin-bottom: 10px; letter-spacing: -0.3px; }
        .step p { font-size: 14px; color: var(--muted); line-height: 1.65; }

        /* PHOTO FEATURE */
        .photo-section { padding: 80px 24px 100px; max-width: 1100px; margin: 0 auto; }
        .photo-feature-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 48px; align-items: center; margin-top: 56px; }
        .photo-demo { background: var(--card-bg); border: 1px solid var(--border); border-radius: 24px; padding: 32px; }
        .chat-bubble { border-radius: 18px; padding: 12px 16px; font-size: 14px; line-height: 1.5; max-width: 85%; margin-bottom: 10px; }
        .chat-bubble.outgoing { background: #1a1a1a; border: 1px solid rgba(255,255,255,0.08); color: var(--text); margin-left: auto; border-bottom-right-radius: 4px; }
        .chat-bubble.incoming { background: rgba(200,240,96,0.1); border: 1px solid rgba(200,240,96,0.2); color: var(--text); border-bottom-left-radius: 4px; }
        .chat-time { font-size: 11px; color: var(--muted); text-align: right; margin-bottom: 14px; }
        .timer-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(245,166,35,0.12); border: 1px solid rgba(245,166,35,0.25); border-radius: 100px; padding: 4px 12px; font-size: 12px; color: var(--accent2); font-weight: 500; margin-bottom: 12px; }
        .photo-copy h3 { font-family: 'Instrument Serif', serif; font-size: clamp(28px, 4vw, 42px); line-height: 1.1; letter-spacing: -1px; color: var(--white); margin-bottom: 16px; }
        .photo-copy p { font-size: 16px; color: var(--muted); line-height: 1.7; margin-bottom: 24px; }
        .feature-list { list-style: none; display: flex; flex-direction: column; gap: 12px; }
        .feature-list li { display: flex; align-items: flex-start; gap: 10px; font-size: 14px; color: var(--text); }
        .feature-list .check { width: 20px; height: 20px; background: rgba(200,240,96,0.1); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; flex-shrink: 0; margin-top: 1px; color: var(--accent); }

        /* METRICS BAR */
        .metrics-bar { border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); padding: 48px 24px; display: flex; justify-content: center; gap: 0; }
        .metric-item { flex: 1; max-width: 240px; text-align: center; padding: 0 32px; position: relative; }
        .metric-item + .metric-item::before { content: ''; position: absolute; left: 0; top: 10%; bottom: 10%; width: 1px; background: var(--border); }
        .metric-num { font-family: 'Instrument Serif', serif; font-size: 48px; color: var(--white); line-height: 1; letter-spacing: -2px; margin-bottom: 8px; }
        .metric-num span { color: var(--accent); }
        .metric-label { font-size: 14px; color: var(--muted); }

        /* INTEGRATIONS */
        .integrations-section { padding: 80px 24px; max-width: 900px; margin: 0 auto; text-align: center; }
        .integration-logos { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-top: 40px; }
        .integration-chip { display: flex; align-items: center; gap: 8px; background: var(--card-bg); border: 1px solid var(--border); border-radius: 100px; padding: 10px 20px; font-size: 14px; font-weight: 500; color: var(--text); transition: border-color 0.2s, background 0.2s; }
        .integration-chip:hover { border-color: rgba(255,255,255,0.2); background: var(--bg3); }
        .integration-chip .icon { font-size: 18px; }

        /* PRICING */
        .pricing-section { padding: 80px 24px 100px; max-width: 560px; margin: 0 auto; text-align: center; }
        .pricing-card { background: var(--card-bg); border: 1px solid rgba(200,240,96,0.25); border-radius: 24px; padding: 48px 40px; margin-top: 48px; position: relative; overflow: hidden; }
        .pricing-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, transparent, var(--accent), transparent); }
        .price-amount { font-family: 'Instrument Serif', serif; font-size: 72px; color: var(--white); letter-spacing: -3px; line-height: 1; }
        .price-period { font-size: 16px; color: var(--muted); margin-left: 4px; }
        .price-desc { font-size: 15px; color: var(--muted); margin-bottom: 36px; margin-top: 8px; }
        .price-features { list-style: none; text-align: left; display: flex; flex-direction: column; gap: 14px; margin-bottom: 40px; }
        .price-features li { display: flex; align-items: center; gap: 12px; font-size: 15px; color: var(--text); }
        .price-features .check { width: 22px; height: 22px; background: rgba(200,240,96,0.12); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; color: var(--accent); flex-shrink: 0; }
        .btn-cta-large { display: block; background: var(--accent); color: #0a0a0a; padding: 18px 0; border-radius: 12px; font-size: 17px; font-weight: 700; text-decoration: none; transition: opacity 0.2s, transform 0.15s; width: 100%; text-align: center; }
        .btn-cta-large:hover { opacity: 0.88; transform: translateY(-2px); }
        .pricing-note { font-size: 13px; color: var(--muted); margin-top: 16px; }

        /* FAQ */
        .faq-section { padding: 60px 24px 100px; max-width: 680px; margin: 0 auto; }
        .faq-item { border-bottom: 1px solid var(--border); padding: 24px 0; }
        .faq-question { font-size: 16px; font-weight: 600; color: var(--text); cursor: pointer; display: flex; justify-content: space-between; align-items: center; gap: 16px; user-select: none; }
        .faq-chevron { color: var(--muted); font-size: 18px; transition: transform 0.25s; flex-shrink: 0; }
        .faq-item.open .faq-chevron { transform: rotate(45deg); }
        .faq-answer { font-size: 14px; color: var(--muted); line-height: 1.7; max-height: 0; overflow: hidden; transition: max-height 0.3s ease, padding 0.3s ease; }
        .faq-item.open .faq-answer { max-height: 300px; padding-top: 14px; }

        /* FOOTER */
        footer { border-top: 1px solid var(--border); padding: 40px 48px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; }
        .footer-links { display: flex; gap: 24px; }
        .footer-links a { font-size: 13px; color: var(--muted); text-decoration: none; transition: color 0.2s; }
        .footer-links a:hover { color: var(--text); }

        /* ANIMATIONS */
        @keyframes fadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .fade-in { opacity: 0; transform: translateY(24px); transition: opacity 0.6s ease, transform 0.6s ease; }
        .fade-in.visible { opacity: 1; transform: translateY(0); }

        /* RESPONSIVE */
        @media (max-width: 768px) {
          nav { padding: 16px 20px; }
          .nav-links { display: none; }
          .steps-grid { grid-template-columns: 1fr; }
          .photo-feature-grid { grid-template-columns: 1fr; }
          .metrics-bar { flex-direction: column; align-items: center; gap: 32px; }
          .metric-item + .metric-item::before { display: none; }
          footer { flex-direction: column; text-align: center; }
        }
      `}</style>

      {/* NAV */}
      <nav>
        <a className="logo" href="/">marlo<span>.</span></a>
        <div className="nav-links">
          <a className="nav-link" href="#how">How it works</a>
          <a className="nav-link" href="#features">Features</a>
          <a className="nav-link" href="#pricing">Pricing</a>
          <a className="nav-cta" href="/signup">Start free trial</a>
        </div>
      </nav>

      {/* HERO */}
      <section className="hero">
        <div className="hero-glow"></div>
        <div className="hero-badge"><div className="badge-dot"></div>Now in beta — 14-day free trial</div>
        <h1>Your marketing,<br /><em>handled by email.</em></h1>
        <p className="hero-sub">No app. No dashboard. No learning curve.<br />Marlo runs your ads, posts, and emails — you just tap Approve every morning.</p>
        <div className="hero-actions">
          <a href="/signup" className="btn-primary">Start free trial →</a>
          <a href="#how" className="btn-ghost">See how it works ↓</a>
        </div>
        <div className="hero-social-proof">
          <div className="avatar-row">
            <div className="avatars">
              <div className="avatar" style={{background:'#2a3a2a'}}>🧁</div>
              <div className="avatar" style={{background:'#2a2a3a'}}>🌿</div>
              <div className="avatar" style={{background:'#3a2a2a'}}>🛍️</div>
              <div className="avatar" style={{background:'#2a3a3a'}}>☕</div>
            </div>
          </div>
          <p>Trusted by small business owners who'd rather be running their business</p>
        </div>
      </section>

      {/* METRICS BAR */}
      <div className="metrics-bar fade-in">
        <div className="metric-item"><div className="metric-num"><span>2</span> min</div><div className="metric-label">From photo to live ad</div></div>
        <div className="metric-item"><div className="metric-num"><span>1</span> tap</div><div className="metric-label">To approve your daily plan</div></div>
        <div className="metric-item"><div className="metric-num"><span>$99</span></div><div className="metric-label">Per month, everything included</div></div>
        <div className="metric-item"><div className="metric-num"><span>0</span></div><div className="metric-label">Apps to learn or log into</div></div>
      </div>

      {/* PHONE SECTION */}
      <section className="phone-section" id="how">
        <div style={{textAlign:'center'}}>
          <div className="section-label">Every morning at 8am</div>
          <h2 className="section-title">Your marketing brief,<br />straight to your inbox</h2>
          <p className="section-sub">Marlo reviews your metrics overnight and plans your day. You wake up to a briefing — approve it in one tap.</p>
        </div>
        <div className="phone-wrapper fade-in">
          <div className="phone-frame">
            <div className="phone-notch"><div className="phone-notch-pill"></div></div>
            <div className="phone-screen">
              <div className="email-header">
                <div className="email-from">From: Marlo &lt;hello@marlo021.ai&gt; · 8:02 AM</div>
                <div className="email-subject">☀️ Good morning, Sarah. Here's today's plan.</div>
              </div>
              <div className="email-body">
                <div className="email-greeting">Your latte ad is performing — CTR jumped to 4.2%. I've drafted 3 new posts and adjusted your Instagram budget. Here's the plan:</div>
                <div className="email-metric-row">
                  <div className="email-metric"><div className="email-metric-num green">4.2%</div><div className="email-metric-label">CTR ↑ 1.1%</div></div>
                  <div className="email-metric"><div className="email-metric-num">$12.40</div><div className="email-metric-label">CPC today</div></div>
                  <div className="email-metric"><div className="email-metric-num green">18</div><div className="email-metric-label">New followers</div></div>
                </div>
                <div className="email-plan-title">Today's plan</div>
                <div className="email-plan-item"><span>📸</span><span>Post latte art Reel on Instagram · 11am</span></div>
                <div className="email-plan-item"><span>📣</span><span>Boost Saturday special ad · $8 budget</span></div>
                <div className="email-plan-item"><span>📧</span><span>Send loyalty email to 340 subscribers</span></div>
                <div className="email-cta-row">
                  <button className="email-btn-approve">✓ Approve all</button>
                  <button className="email-btn-decline">Edit</button>
                </div>
              </div>
            </div>
          </div>
          <div className="phone-callouts">
            <div className="callout"><div className="callout-emoji">📊</div><div className="callout-title">Overnight analysis</div><div className="callout-body">Marlo checks your Google Ads, Instagram, and email stats while you sleep — so the plan is already optimized by morning.</div></div>
            <div className="callout"><div className="callout-emoji">✅</div><div className="callout-title">One-tap approve</div><div className="callout-body">No login required. Tap Approve in the email and everything goes live — posts, ads, emails. Done in 10 seconds.</div></div>
            <div className="callout"><div className="callout-emoji">💬</div><div className="callout-title">Reply in plain English</div><div className="callout-body">Not happy with the plan? Just reply. "Focus on the new menu item this week" — Marlo understands and adjusts.</div></div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="how-section fade-in">
        <div style={{textAlign:'center'}}>
          <div className="section-label">The setup</div>
          <h2 className="section-title">Up and running<br />in 10 minutes</h2>
        </div>
        <div className="steps-grid">
          <div className="step"><div className="step-number">1</div><div className="step-icon">✉️</div><h3>Sign up & connect</h3><p>Create your account and connect Google Ads, Meta, Instagram, and Mailchimp. Marlo walks you through everything via email — no tech skills needed.</p></div>
          <div className="step"><div className="step-number">2</div><div className="step-icon">🧠</div><h3>Marlo learns your business</h3><p>Answer 5 questions about your business over email. Marlo builds a marketing strategy around your goals, audience, and budget. No forms, no dashboards.</p></div>
          <div className="step"><div className="step-number">3</div><div className="step-icon">☀️</div><h3>Approve every morning</h3><p>Every day at 8am, Marlo sends your briefing. Review, tap approve, go make coffee. Your marketing runs itself for the rest of the day.</p></div>
        </div>
      </section>

      {/* PHOTO FEATURE */}
      <section className="photo-section" id="features">
        <div className="photo-feature-grid fade-in">
          <div className="photo-demo">
            <div className="timer-badge">⚡ Live in ~2 minutes</div>
            <div className="chat-bubble outgoing">
              <div style={{width:'100%',height:'120px',background:'linear-gradient(135deg,#2a2a1a,#1a2a1a)',borderRadius:'12px',marginBottom:'6px',display:'flex',alignItems:'center',justifyContent:'center',fontSize:'32px',border:'1px solid rgba(200,240,96,0.1)'}}>📸</div>
              <div>New seasonal latte — can you run an ad for this?</div>
            </div>
            <div className="chat-time">Sent 2:14 PM · replied to Marlo morning email</div>
            <div className="chat-bubble incoming">Got it! I've enhanced the photo and created 4 versions for Instagram Feed, Story, Facebook, and Google Display. Here's a preview — tap Approve to go live. 🚀</div>
            <div style={{marginTop:'14px',display:'flex',gap:'8px'}}>
              <div style={{flex:1,height:'70px',background:'linear-gradient(135deg,#1a2a1a,#2a1a2a)',borderRadius:'10px',display:'flex',alignItems:'center',justifyContent:'center',fontSize:'11px',color:'#666',border:'1px solid rgba(255,255,255,0.06)'}}>Instagram Feed</div>
              <div style={{flex:1,height:'70px',background:'linear-gradient(135deg,#2a1a1a,#1a1a2a)',borderRadius:'10px',display:'flex',alignItems:'center',justifyContent:'center',fontSize:'11px',color:'#666',border:'1px solid rgba(255,255,255,0.06)'}}>Story</div>
              <div style={{flex:1,height:'70px',background:'linear-gradient(135deg,#1a1a2a,#2a2a1a)',borderRadius:'10px',display:'flex',alignItems:'center',justifyContent:'center',fontSize:'11px',color:'#666',border:'1px solid rgba(255,255,255,0.06)'}}>Facebook</div>
            </div>
          </div>
          <div className="photo-copy">
            <div className="section-label">The photo feature</div>
            <h3>Text a photo.<br />Ads are live in 2 minutes.</h3>
            <p>Just reply to any Marlo email with a photo. Marlo enhances it, resizes for every platform, writes the caption, and sends you an approval email — with the images right there to preview.</p>
            <ul className="feature-list">
              <li><span className="check">✓</span>AI enhances photo quality automatically</li>
              <li><span className="check">✓</span>Sized for Instagram, Stories, Facebook & Google</li>
              <li><span className="check">✓</span>Captions written to match your brand voice</li>
              <li><span className="check">✓</span>One-tap to approve and post everywhere</li>
              <li><span className="check">✓</span>No apps, no uploading, no resizing manually</li>
            </ul>
          </div>
        </div>
      </section>

      {/* INTEGRATIONS */}
      <section className="integrations-section fade-in">
        <div className="section-label">Integrations</div>
        <h2 className="section-title" style={{fontSize:'clamp(28px,4vw,42px)'}}>Connects to the tools<br />you already use</h2>
        <div className="integration-logos">
          <div className="integration-chip"><span className="icon">📊</span>Google Ads</div>
          <div className="integration-chip"><span className="icon">📘</span>Meta Ads</div>
          <div className="integration-chip"><span className="icon">📸</span>Instagram</div>
          <div className="integration-chip"><span className="icon">📧</span>Mailchimp</div>
          <div className="integration-chip"><span className="icon">📈</span>Google Analytics</div>
        </div>
      </section>

      {/* PRICING */}
      <section className="pricing-section" id="pricing">
        <div className="section-label">Pricing</div>
        <h2 className="section-title">Simple, flat pricing.</h2>
        <p className="section-sub" style={{marginTop:'12px'}}>One plan. Everything included. Cancel anytime.</p>
        <div className="pricing-card fade-in">
          <div><span className="price-amount">$99</span><span className="price-period">/ month</span></div>
          <p className="price-desc">Full AI marketing agent for your business</p>
          <ul className="price-features">
            {['Daily morning briefing email','Google Ads & Meta ad management','Instagram post scheduling & publishing','Mailchimp email campaigns','Photo → ad pipeline (reply with a photo)','Weekly ROI performance report','Unlimited email replies & instructions','Budget guardrails — never overspends'].map((f,i) => (
              <li key={i}><span className="check">✓</span>{f}</li>
            ))}
          </ul>
          <a href="/signup" className="btn-cta-large">Start your free 14-day trial →</a>
          <p className="pricing-note">No credit card required to start. Cancel anytime.</p>
        </div>
      </section>

      {/* FAQ */}
      <section className="faq-section fade-in">
        <div style={{textAlign:'center',marginBottom:'48px'}}>
          <div className="section-label">FAQ</div>
          <h2 className="section-title" style={{fontSize:'clamp(28px,4vw,42px)'}}>Common questions</h2>
        </div>
        {[
          ['Do I need to know anything about marketing?', 'Not at all. Marlo is designed for small business owners who are great at their business but don\'t have time to learn Google Ads or Meta\'s ad manager. You answer a few questions about your business during setup, and Marlo handles the strategy and execution.'],
          ['What if I don\'t like the plan Marlo sends?', 'Just reply in plain English. "Skip the email today" or "Focus on our weekend special" — Marlo will adjust. You\'re always in control. You can also decline individual actions without approving everything.'],
          ['Will Marlo overspend my ad budget?', 'Never. Marlo has built-in budget guardrails that hard-cap your daily and monthly spend. Every ad action requires your approval before anything goes live. You set the limits, Marlo stays within them.'],
          ['How is this different from Hootsuite or Buffer?', 'Those tools let you schedule content — but you still have to create it, decide the strategy, and manage your ad spend separately. Marlo does all of that for you. It\'s not a scheduling tool, it\'s an autonomous agent that runs your whole marketing operation.'],
          ['What kind of businesses is Marlo best for?', 'Local service businesses, restaurants, cafes, retail shops, salons, studios — any small business that has a Google Ads or Meta presence and wants to stay active on social without hiring a marketing agency or spending hours doing it themselves.'],
        ].map(([q, a], i) => (
          <div className="faq-item" key={i}>
            <div className="faq-question" onClick={(e) => (window as any).toggleFaq(e.currentTarget)}>
              {q}<span className="faq-chevron">+</span>
            </div>
            <div className="faq-answer">{a}</div>
          </div>
        ))}
      </section>

      {/* FOOTER */}
      <footer>
        <a className="logo" href="/">marlo<span>.</span></a>
        <div className="footer-links">
          <a href="/help">Help & FAQ</a>
          <a href="/privacy">Privacy</a>
          <a href="/terms">Terms</a>
          <a href="mailto:hello@marlo021.ai">Contact</a>
        </div>
        <p style={{fontSize:'13px',color:'var(--muted)'}}>© 2026 Marlo. All rights reserved.</p>
      </footer>
    </>
  )
}
