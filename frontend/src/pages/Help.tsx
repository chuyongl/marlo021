import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

const FAQS = [
  {
    id: 'why-facebook-page',
    category: 'Facebook & Instagram',
    q: 'Why do I need a Facebook Page just for Instagram?',
    a: `Meta's system requires Instagram Business accounts to be linked to a Facebook Page before the Instagram API works. Think of the Facebook Page as the "business license" that unlocks Instagram's business features — ad accounts, permissions, and API access all flow through it.\n\nThe Page doesn't need to be active or have any posts. It just needs to exist and be connected to your Instagram. Creating one takes about 2 minutes at facebook.com/pages/create.`,
  },
  {
    id: 'why-business-account',
    category: 'Facebook & Instagram',
    q: "Why can't Marlo post to my personal Instagram?",
    a: `Instagram only allows third-party tools to post to Business or Creator accounts. Personal accounts don't have API access — this is a rule set by Instagram, not Marlo.\n\nSwitching is free and takes about 2 minutes:\n\nStep A — Switch to Business account:\nInstagram → ☰ → Settings → Account type and tools → Switch to Professional Account → Business.\n\nStep B — Link your Instagram to Facebook (easiest on desktop):\nGo to accountscenter.facebook.com while logged into the Facebook account that owns your Facebook Page → Profiles and personal details → Add accounts → add your Instagram account.\n\n⚠️ Make sure you're logged into the Facebook account that owns your Facebook Page. Once your Instagram is in that Accounts Center, the Page link happens automatically.\n\nYour existing posts, followers, and username all stay exactly the same.`,
  },
  {
    id: 'meta-permissions',
    category: 'Facebook & Instagram',
    q: 'What permissions is Marlo asking for, and why?',
    a: `When you connect Facebook & Instagram, you'll see a list of permissions on Facebook's authorization page. Here's what each one means:\n\n• pages_show_list — Marlo needs to see which Facebook Pages you manage so you can select the right one.\n• pages_read_engagement — Lets Marlo read likes, comments, and reach on your posts for your weekly reports.\n• instagram_basic — Lets Marlo read basic info about your Instagram account (username, follower count).\n• instagram_content_publish — Lets Marlo post photos and videos to Instagram after you approve.\n\nMarlo cannot read your personal Facebook feed, private messages, or friends list.`,
  },
  {
    id: 'no-instagram',
    category: 'Facebook & Instagram',
    q: "I don't have Instagram yet. Can I still use Marlo?",
    a: `Absolutely. You can skip the Instagram connection during onboarding and Marlo will start with Google Ads and Facebook Ads only.\n\nWhen you're ready to add Instagram later, just reply to any Marlo email: "Connect my Instagram" and Marlo will send you the setup link.`,
  },
  {
    id: 'budget-overspend',
    category: 'Ad Budget',
    q: 'Will Marlo ever overspend my budget?',
    a: `Never. Marlo has hard budget guardrails built in — it tracks your daily and monthly spend in real time and will not submit any ad action that would exceed your set limit.\n\nEvery spending action also requires your approval before it goes live. You can change your budget anytime by replying to any Marlo email: "Change my monthly budget to $500."`,
  },
  {
    id: 'change-budget',
    category: 'Ad Budget',
    q: 'How do I change my ad budget?',
    a: `Just reply to any Marlo email in plain English:\n\n"Change my monthly ad budget to $400"\n"Reduce my daily spend to $10 this week"\n"Pause all ads until Monday"\n\nMarlo will confirm the change and apply it immediately.`,
  },
  {
    id: 'no-google-ads',
    category: 'Google',
    q: "I don't have a Google Ads account yet. Can I still sign up?",
    a: `Yes. When you click "Connect Google" in your onboarding email, just sign in with your Google account. If you don't have Google Ads yet, Google will walk you through creating a free account in about 3 minutes.\n\nWhen prompted, choose "Switch to Expert Mode" and then "Create account without a campaign." Marlo will set up your first campaign for you once you're connected.`,
  },
  {
    id: 'data-security',
    category: 'Privacy & Security',
    q: 'Is my data safe? What does Marlo store?',
    a: `Marlo stores your OAuth access tokens (the keys that let us post on your behalf) encrypted at rest using industry-standard encryption. We never store your passwords.\n\nWe store the content we generate for you and your performance metrics so we can improve recommendations over time. We do not sell your data or share it with third parties.\n\nYou can revoke Marlo's access at any time via Facebook Settings → Business Integrations, or Instagram Settings → Apps and Websites.`,
  },
  {
    id: 'what-if-i-decline',
    category: 'How Marlo Works',
    q: "What happens if I don't approve the morning plan?",
    a: `Nothing goes live. Marlo never takes action without your explicit approval — tapping Approve is what triggers everything.\n\nIf you decline or don't respond, Marlo adjusts the plan for the next day. You can also reply with specific instructions: "Skip the ad today but post the Instagram photo" and Marlo will act accordingly.`,
  },
  {
    id: 'morning-email-time',
    category: 'How Marlo Works',
    q: 'What time does the morning email arrive?',
    a: `Every day at 8:00 AM in your local timezone. Marlo analyzes your overnight performance data and prepares your daily plan before you wake up.\n\nTo change the time, reply to any Marlo email: "Send my morning briefing at 7am instead."`,
  },
  {
    id: 'cancel',
    category: 'Billing',
    q: 'How do I cancel?',
    a: `Reply to any Marlo email with "Cancel my account" and we'll take care of it immediately. No forms, no phone calls.\n\nYou can also email hello@marlo021.ai directly. We'll confirm cancellation within 24 hours and you won't be charged again.`,
  },
]

const CATEGORIES = Array.from(new Set(FAQS.map(f => f.category)))

export function Help() {
  const location = useLocation()

  useEffect(() => {
    if (location.hash) {
      const id = location.hash.replace('#', '')
      setTimeout(() => {
        const el = document.getElementById(id)
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' })
          el.classList.add('highlighted')
          setTimeout(() => el.classList.remove('highlighted'), 2000)
        }
      }, 100)
    }
  }, [location])

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
        .help-page { min-height:100vh; background:#0a0a0a; color:#f0ece4; font-family:'DM Sans',sans-serif; }
        .help-nav { position:sticky; top:0; z-index:100; display:flex; align-items:center; justify-content:space-between; padding:20px 48px; background:rgba(10,10,10,0.9); backdrop-filter:blur(16px); border-bottom:1px solid rgba(255,255,255,0.08); }
        .help-logo { font-family:'Instrument Serif',serif; font-size:22px; color:#f0ece4; text-decoration:none; letter-spacing:-0.5px; }
        .help-logo span { color:#c8f060; }
        .help-nav-back { font-size:13px; color:#666; text-decoration:none; transition:color 0.2s; }
        .help-nav-back:hover { color:#f0ece4; }
        .help-header { max-width:760px; margin:0 auto; padding:80px 24px 48px; text-align:center; }
        .help-header h1 { font-family:'Instrument Serif',serif; font-size:clamp(36px,5vw,56px); line-height:1.05; letter-spacing:-1.5px; color:#ffffff; margin-bottom:16px; }
        .help-header p { font-size:17px; color:#666; line-height:1.6; }
        .help-header a { color:#c8f060; text-decoration:none; }
        .help-header a:hover { text-decoration:underline; }
        .help-body { max-width:760px; margin:0 auto; padding:0 24px 100px; }
        .help-category { margin-bottom:48px; }
        .help-category-title { font-size:11px; font-weight:600; letter-spacing:2px; text-transform:uppercase; color:#c8f060; margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid rgba(255,255,255,0.06); }
        .faq-item { border-bottom:1px solid rgba(255,255,255,0.06); scroll-margin-top:100px; transition:background 0.4s; border-radius:8px; padding:0 12px; margin:0 -12px; cursor:pointer; }
        .faq-item.highlighted { background:rgba(200,240,96,0.06); }
        .faq-question { font-size:15px; font-weight:600; color:#f0ece4; display:flex; justify-content:space-between; align-items:center; gap:16px; padding:20px 0; user-select:none; }
        .faq-question:hover { color:#ffffff; }
        .faq-chevron { color:#444; font-size:20px; transition:transform 0.25s, color 0.2s; flex-shrink:0; line-height:1; }
        .faq-item.open .faq-chevron { transform:rotate(45deg); color:#c8f060; }
        .faq-answer { font-size:14px; color:#888; line-height:1.8; max-height:0; overflow:hidden; transition:max-height 0.35s ease, padding 0.35s ease; white-space:pre-line; }
        .faq-item.open .faq-answer { max-height:800px; padding-bottom:20px; }
        .help-cta { background:#141414; border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:36px; text-align:center; margin-top:48px; }
        .help-cta h3 { font-family:'Instrument Serif',serif; font-size:26px; color:#ffffff; margin-bottom:10px; letter-spacing:-0.5px; }
        .help-cta p { font-size:14px; color:#666; margin-bottom:20px; line-height:1.6; }
        .help-cta a { display:inline-block; background:#c8f060; color:#0a0a0a; padding:13px 28px; border-radius:8px; font-size:14px; font-weight:600; text-decoration:none; transition:opacity 0.2s; }
        .help-cta a:hover { opacity:0.85; }
        @media (max-width:600px) { .help-nav { padding:16px 20px; } .help-header { padding:60px 20px 32px; } }
      `}</style>

      <div className="help-page">
        <nav className="help-nav">
          <a className="help-logo" href="/">marlo<span>021.</span></a>
          <a className="help-nav-back" href="/">← Back to home</a>
        </nav>

        <div className="help-header">
          <h1>Help & FAQs</h1>
          <p>
            Can't find what you're looking for?{' '}
            <a href="mailto:hello@marlo021.ai">Email us</a> and we'll get back to you within a few hours.
          </p>
        </div>

        <div className="help-body">
          {CATEGORIES.map(category => (
            <div className="help-category" key={category}>
              <div className="help-category-title">{category}</div>
              {FAQS.filter(f => f.category === category).map(faq => (
                <div
                  className="faq-item"
                  key={faq.id}
                  id={faq.id}
                  onClick={e => {
                    const item = e.currentTarget as HTMLElement
                    const isOpen = item.classList.contains('open')
                    document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'))
                    if (!isOpen) item.classList.add('open')
                  }}
                >
                  <div className="faq-question">
                    {faq.q}
                    <span className="faq-chevron">+</span>
                  </div>
                  <div className="faq-answer">{faq.a}</div>
                </div>
              ))}
            </div>
          ))}

          <div className="help-cta">
            <h3>Still stuck?</h3>
            <p>Reply to any Marlo email or send us a message directly.<br />A real human will get back to you.</p>
            <a href="mailto:hello@marlo021.ai">Email hello@marlo021.ai</a>
          </div>
        </div>
      </div>
    </>
  )
}