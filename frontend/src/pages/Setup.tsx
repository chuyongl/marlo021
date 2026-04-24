export function Setup() {
  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
        .setup-page {
          min-height: 100vh;
          background: #0a0a0a;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 24px;
          font-family: 'DM Sans', sans-serif;
        }
        .setup-logo {
          font-family: 'Instrument Serif', serif;
          font-size: 22px;
          color: #f0ece4;
          text-decoration: none;
          margin-bottom: 48px;
          letter-spacing: -0.5px;
        }
        .setup-logo span { color: #c8f060; }
        .setup-card {
          background: #141414;
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 24px;
          padding: 48px 40px;
          width: 100%;
          max-width: 420px;
          text-align: center;
        }
        .setup-emoji { font-size: 52px; margin-bottom: 24px; }
        .setup-card h1 {
          font-family: 'Instrument Serif', serif;
          font-size: 32px;
          color: #ffffff;
          letter-spacing: -0.5px;
          margin-bottom: 12px;
          line-height: 1.1;
        }
        .setup-card p {
          font-size: 15px;
          color: #666;
          line-height: 1.7;
          margin-bottom: 32px;
        }
        .setup-steps {
          background: #1a1a1a;
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 14px;
          padding: 20px;
          text-align: left;
          display: flex;
          flex-direction: column;
          gap: 14px;
          margin-bottom: 28px;
        }
        .setup-step {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 14px;
          color: #888;
        }
        .setup-step-num {
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: rgba(200,240,96,0.1);
          color: #c8f060;
          font-size: 11px;
          font-weight: 700;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .setup-footer {
          font-size: 13px;
          color: #444;
          line-height: 1.7;
        }
      `}</style>

      <div className="setup-page">
        <a className="setup-logo" href="/">marlo<span>021.</span></a>

        <div className="setup-card">
          <div className="setup-emoji">📧</div>
          <h1>Check your email!</h1>
          <p>
            Marlo just sent you the first setup email. Follow the steps
            to connect your accounts — the whole thing takes about 20 minutes.
          </p>

          <div className="setup-steps">
            {[
              'Connect Google Ads & Analytics',
              'Connect Facebook & Instagram',
              'Connect Mailchimp',
              'Tell Marlo about your business',
            ].map((step, i) => (
              <div className="setup-step" key={i}>
                <div className="setup-step-num">{i + 1}</div>
                {step}
              </div>
            ))}
          </div>

          <p className="setup-footer">
            After setup, just check your email every morning.<br />
            Tap approve — that's it.
          </p>
        </div>
      </div>
    </>
  )
}