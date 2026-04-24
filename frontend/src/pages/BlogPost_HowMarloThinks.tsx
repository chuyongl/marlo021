export function BlogPost_HowMarloThinks() {
  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
        .post-page { min-height:100vh; background:#0a0a0a; color:#f0ece4; font-family:'DM Sans',sans-serif; }
        .post-nav { position:sticky; top:0; z-index:100; display:flex; align-items:center; justify-content:space-between; padding:20px 48px; background:rgba(10,10,10,0.9); backdrop-filter:blur(16px); border-bottom:1px solid rgba(255,255,255,0.08); }
        .post-logo { font-family:'Instrument Serif',serif; font-size:22px; color:#f0ece4; text-decoration:none; letter-spacing:-0.5px; }
        .post-logo span { color:#c8f060; }
        .post-nav-back { font-size:13px; color:#666; text-decoration:none; transition:color 0.2s; }
        .post-nav-back:hover { color:#f0ece4; }

        .post-body { max-width:680px; margin:0 auto; padding:80px 24px 120px; }

        .post-meta { display:flex; align-items:center; gap:12px; margin-bottom:32px; }
        .post-category { font-size:11px; font-weight:600; letter-spacing:2px; text-transform:uppercase; color:#c8f060; }
        .post-date { font-size:12px; color:#555; }
        .post-readtime { font-size:12px; color:#555; }

        .post-body h1 { font-family:'Instrument Serif',serif; font-size:clamp(36px,5vw,54px); line-height:1.05; letter-spacing:-1.5px; color:#ffffff; margin-bottom:20px; }
        .post-subtitle { font-size:19px; color:#888; line-height:1.6; margin-bottom:48px; padding-bottom:48px; border-bottom:1px solid rgba(255,255,255,0.08); }

        .post-body h2 { font-family:'Instrument Serif',serif; font-size:28px; color:#ffffff; margin:48px 0 16px; letter-spacing:-0.5px; line-height:1.2; }
        .post-body h3 { font-size:16px; font-weight:600; color:#f0ece4; margin:32px 0 12px; }
        .post-body p { font-size:16px; color:#aaa; line-height:1.8; margin-bottom:20px; }
        .post-body strong { color:#f0ece4; font-weight:500; }

        .post-divider { border:none; border-top:1px solid rgba(255,255,255,0.06); margin:48px 0; }

        .stage-card { background:#141414; border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:24px; margin-bottom:16px; display:grid; grid-template-columns:48px 1fr; gap:16px; align-items:start; }
        .stage-icon { width:48px; height:48px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:20px; flex-shrink:0; }
        .stage-title { font-size:15px; font-weight:600; color:#f0ece4; margin-bottom:4px; }
        .stage-subtitle { font-size:12px; color:#555; margin-bottom:8px; text-transform:uppercase; letter-spacing:1px; }
        .stage-desc { font-size:14px; color:#888; line-height:1.7; }

        .callout { background:#141414; border-left:3px solid #c8f060; border-radius:0 8px 8px 0; padding:16px 20px; margin:24px 0; }
        .callout p { font-size:14px; color:#aaa; line-height:1.7; margin:0; }
        .callout strong { color:#c8f060; }

        .timeline { position:relative; padding-left:32px; margin:24px 0; }
        .timeline::before { content:''; position:absolute; left:8px; top:8px; bottom:8px; width:1px; background:rgba(255,255,255,0.1); }
        .timeline-item { position:relative; margin-bottom:24px; }
        .timeline-item::before { content:''; position:absolute; left:-28px; top:6px; width:8px; height:8px; border-radius:50%; background:#c8f060; }
        .timeline-week { font-size:11px; font-weight:600; letter-spacing:1.5px; text-transform:uppercase; color:#c8f060; margin-bottom:4px; }
        .timeline-label { font-size:15px; font-weight:500; color:#f0ece4; margin-bottom:6px; }
        .timeline-desc { font-size:14px; color:#888; line-height:1.6; }
        .timeline-example { font-size:13px; color:#666; font-style:italic; margin-top:8px; padding:10px 14px; background:rgba(255,255,255,0.03); border-radius:6px; border:1px solid rgba(255,255,255,0.06); }

        .quality-bar { margin:8px 0 4px; }
        .quality-bar-track { height:4px; background:rgba(255,255,255,0.08); border-radius:2px; overflow:hidden; }
        .quality-bar-fill { height:100%; border-radius:2px; background:#c8f060; transition:width 0.6s ease; }

        .footer-nav { display:flex; justify-content:space-between; align-items:center; padding-top:48px; border-top:1px solid rgba(255,255,255,0.08); margin-top:48px; }
        .footer-nav a { font-size:14px; color:#666; text-decoration:none; transition:color 0.2s; }
        .footer-nav a:hover { color:#f0ece4; }

        @media (max-width:600px) { .post-nav { padding:16px 20px; } .post-body { padding:60px 20px 80px; } }
      `}</style>

      <div className="post-page">
        <nav className="post-nav">
          <a className="post-logo" href="/">marlo<span>021.</span></a>
          <a className="post-nav-back" href="/blog">← All articles</a>
        </nav>

        <div className="post-body">
          <div className="post-meta">
            <span className="post-category">Engineering</span>
            <span className="post-date">April 2026</span>
            <span className="post-readtime">6 min read</span>
          </div>

          <h1>How Marlo thinks: inside the content generation pipeline</h1>
          <p className="post-subtitle">
            A look at the multi-agent system behind every post Marlo creates —
            from triage to quality check to feedback loop.
          </p>

          <p>
            Every time Marlo generates a piece of content — whether it's an Instagram post,
            a Facebook ad, or a Google campaign — it runs through a six-stage pipeline of
            specialized AI agents. Each agent has a single job and passes its output to the next.
          </p>
          <p>
            This isn't one big prompt asking Claude to "write me a caption." It's a deliberate
            assembly line where each stage adds a layer of quality. Here's how it works.
          </p>

          <hr className="post-divider" />

          <h2>The six-stage pipeline</h2>

          <div className="stage-card">
            <div className="stage-icon" style={{background:'rgba(155,127,232,0.12)'}}>🔀</div>
            <div>
              <div className="stage-subtitle">Stage 1</div>
              <div className="stage-title">Triage router</div>
              <div className="stage-desc">
                Every content request gets classified first. Is this a promotional post? A seasonal
                campaign? A photo the user sent? The triage router reads the request and context,
                then routes it to the right pipeline configuration — different content types need
                different strategy and generation approaches.
              </div>
            </div>
          </div>

          <div className="stage-card">
            <div className="stage-icon" style={{background:'rgba(45,212,160,0.12)'}}>🧠</div>
            <div>
              <div className="stage-subtitle">Stage 2</div>
              <div className="stage-title">Strategy agent</div>
              <div className="stage-desc">
                Before writing anything, the strategy agent reads three inputs: your recent ad
                metrics (CTR, CPC, spend), your approval history (what you've approved vs skipped),
                and your business profile (industry, tone, target audience). It produces a strategy
                brief — hook approach, key message, tone guidance, what to avoid — that the content
                agent follows exactly.
              </div>
            </div>
          </div>

          <div className="callout">
            <p>
              <strong>Why a separate strategy step?</strong> Without it, content generation is
              stateless — every post starts from scratch. The strategy layer is what connects
              your business's history and performance to what gets written.
            </p>
          </div>

          <div className="stage-card">
            <div className="stage-icon" style={{background:'rgba(248,113,113,0.12)'}}>✍️</div>
            <div>
              <div className="stage-subtitle">Stage 3</div>
              <div className="stage-title">Content agent</div>
              <div className="stage-desc">
                Given the strategy brief, the content agent writes platform-specific captions and
                hashtags. It knows Instagram's character norms, Facebook's different tone, and
                Story's short-copy constraints. It also gives every piece of content a brand voice
                score (1–10) — an internal self-assessment that feeds the QA stage.
              </div>
            </div>
          </div>

          <div className="stage-card">
            <div className="stage-icon" style={{background:'rgba(251,191,36,0.12)'}}>✅</div>
            <div>
              <div className="stage-subtitle">Stage 4</div>
              <div className="stage-title">QA agent</div>
              <div className="stage-desc">
                Every piece of content gets a quality check before it reaches you. The QA agent
                checks brand voice consistency, platform spec compliance (caption length, hashtag
                count), and overall quality. If the score is below threshold, content is
                regenerated automatically — up to 2 retries. Only content that passes QA
                reaches your approval email.
              </div>
            </div>
          </div>

          <div className="stage-card">
            <div className="stage-icon" style={{background:'rgba(96,165,250,0.12)'}}>🖼️</div>
            <div>
              <div className="stage-subtitle">Stage 5</div>
              <div className="stage-title">Image agent</div>
              <div className="stage-desc">
                Using the strategy brief's visual direction, the image agent generates
                platform-sized images. Instagram feed (1080×1080), Stories (1080×1920),
                Facebook (1200×628). The visual direction comes from the strategy agent,
                so the image is coherent with the caption — same concept, same mood.
              </div>
            </div>
          </div>

          <div className="stage-card">
            <div className="stage-icon" style={{background:'rgba(163,230,53,0.12)'}}>🔁</div>
            <div>
              <div className="stage-subtitle">Stage 6 (ongoing)</div>
              <div className="stage-title">Feedback loop</div>
              <div className="stage-desc">
                When you approve or skip content in your morning email, Marlo records the
                decision. Over time it builds a picture of your preferences. When you skip,
                you can optionally tap a reason (wrong tone, not relevant, poor quality).
                The strategy agent reads this history before every generation cycle.
              </div>
            </div>
          </div>

          <hr className="post-divider" />

          <h2>How it gets smarter over time</h2>

          <p>
            The feedback loop is what separates Marlo from a static content generator.
            Every approve and skip decision gets stored and surfaced back to the strategy
            agent as a summary: approve rate, top decline reasons, best-performing content types.
          </p>

          <div className="timeline">
            <div className="timeline-item">
              <div className="timeline-week">Week 1</div>
              <div className="timeline-label">Getting started</div>
              <div className="timeline-desc">
                Marlo knows your industry and tone from setup. Content is solid but could
                work for any business in your category.
              </div>
              <div className="timeline-example">
                "Start your morning right ☕ Fresh pastries and coffee await. Come visit us!"
              </div>
              <div className="quality-bar">
                <div style={{fontSize:'11px',color:'#555',marginBottom:'4px'}}>Brand fit: 60%</div>
                <div className="quality-bar-track">
                  <div className="quality-bar-fill" style={{width:'60%',background:'#888'}} />
                </div>
              </div>
            </div>

            <div className="timeline-item">
              <div className="timeline-week">Week 4</div>
              <div className="timeline-label">Learning your preferences</div>
              <div className="timeline-desc">
                After 20+ approve/skip decisions, Marlo has learned you prefer specific
                details over generic claims, and that behind-the-scenes content performs well.
              </div>
              <div className="timeline-example">
                "Our head baker gets in at 4am every Thursday to make the sourdough from scratch.
                The line forms by 7. 🍞 See you tomorrow?"
              </div>
              <div className="quality-bar">
                <div style={{fontSize:'11px',color:'#555',marginBottom:'4px'}}>Brand fit: 78%</div>
                <div className="quality-bar-track">
                  <div className="quality-bar-fill" style={{width:'78%',background:'#c8a840'}} />
                </div>
              </div>
            </div>

            <div className="timeline-item">
              <div className="timeline-week">Week 12</div>
              <div className="timeline-label">Knowing your business</div>
              <div className="timeline-desc">
                Marlo has a clear picture of what you approve, when you engage most,
                and how your audience responds. Content feels like it was written by
                someone who's worked with your business for months.
              </div>
              <div className="timeline-example">
                "The fig and ricotta croissant is back. We made 18.
                We always run out before 9. Just saying. 🥐"
              </div>
              <div className="quality-bar">
                <div style={{fontSize:'11px',color:'#555',marginBottom:'4px'}}>Brand fit: 94%</div>
                <div className="quality-bar-track">
                  <div className="quality-bar-fill" style={{width:'94%'}} />
                </div>
              </div>
            </div>
          </div>

          <hr className="post-divider" />

          <h2>What this means for you</h2>

          <p>
            You don't need to configure any of this. You just approve what you like
            and skip what you don't. Marlo handles the rest.
          </p>
          <p>
            The practical implication: the more consistently you engage with your morning
            email — even just tapping skip on things that aren't right — the faster
            Marlo learns what works for your specific business.
          </p>
          <p>
            A tap that takes 2 seconds is worth more than you might think.
          </p>

          <div className="footer-nav">
            <a href="/blog">← All articles</a>
            <a href="/signup">Start free trial →</a>
          </div>
        </div>
      </div>
    </>
  )
}