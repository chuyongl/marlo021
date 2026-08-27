import { useEffect } from 'react'

const SOURCES = [
  {
    n: '01',
    claim: 'Axios Local reports open rates between 30% and 55%.',
    pub: 'Editor & Publisher',
    date: 'March 2022',
    note: 'Figures given by Axios about its own network. Reported, not independently audited.',
    url: 'https://www.editorandpublisher.com/stories/axios-bringing-smart-brevity-to-a-town-near-you,221578',
  },
  {
    n: '02',
    claim: 'Axios states a 41% open rate across 22+ newsletters and 2.5 million subscribers.',
    pub: 'Compiled from public Axios and Axios HQ statements',
    date: 'April 2026',
    note: 'Network-wide figure, not local-only. Same caveat: self-reported.',
    url: 'https://www.readless.app/newsletters/axios',
  },
  {
    n: '03',
    claim: 'Axios Local has more than two million free subscribers across 35 cities, heading for 43 by the end of 2026.',
    pub: 'Press Gazette',
    date: 'May 2026',
    note: 'Also notes the division is not yet profitable. Scale is not the same as a working business.',
    url: 'https://pressgazette.co.uk/newsletters/axios-local-newsletters-scale-cities-profit/',
  },
  {
    n: '04',
    claim: 'The average newsletter open rate is either 21% or 49%, depending on which report you read.',
    pub: 'ClickMinded, newsletter benchmarks',
    date: 'April 2026',
    note: 'The gap is caused by Apple Mail Privacy Protection. This matters. See below.',
    url: 'https://www.clickminded.com/newsletter-statistics/',
  },
  {
    n: '05',
    claim: '6AM City, a local newsletter network, reported profitability in Q1 2026.',
    pub: 'A Media Operator',
    date: 'June 2026',
    note: 'Targets a 10 to 20% margin. Needs roughly 50,000 subscribers per market to work.',
    url: 'https://www.amediaoperator.com/news/6am-citys-secret-weapon-400-newsletters-with-no-staff/',
  },
]

export function WhyLocal() {
  useEffect(() => {
    const pre = document.createElement('link')
    pre.rel = 'preconnect'; pre.href = 'https://fonts.gstatic.com'; pre.crossOrigin = 'anonymous'
    document.head.appendChild(pre)
    const f = document.createElement('link')
    f.rel = 'stylesheet'
    f.href = 'https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300..600;1,6..72,300..500&family=Instrument+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap'
    document.head.appendChild(f)
  }, [])

  return (
    <>
      <style>{`
        :root{
          --paper:#F7F5F0;--paper2:#FFFFFF;--tint:#EFEBE2;
          --ink:#14130F;--ink2:#46433C;--dim:#8B877D;
          --rule:#DCD6C9;--rule2:#C6BEAC;
          --kraft:#8A6A45;--kraftbg:#F0E7D9;
        }
        *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
        html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
        body{background:var(--paper);color:var(--ink2);font-family:'Instrument Sans',system-ui,sans-serif;
          font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
        body::before{content:'';position:fixed;inset:0;z-index:1;pointer-events:none;opacity:.5;
          background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='140' height='140' filter='url(%23n)' opacity='.045'/%3E%3C/svg%3E")}
        a{color:inherit}
        :focus-visible{outline:2px solid var(--kraft);outline-offset:3px}

        .mono{font-family:'IBM Plex Mono',ui-monospace,monospace;font-size:11px;letter-spacing:.18em;text-transform:uppercase}
        .serif{font-family:'Newsreader',Georgia,serif;font-weight:400;color:var(--ink);letter-spacing:-.015em;line-height:1.12}
        .wrap{max-width:820px;margin:0 auto;padding:0 32px;position:relative;z-index:2}

        .nav{position:sticky;top:0;z-index:60;display:flex;align-items:center;gap:26px;padding:16px 32px;
          background:rgba(247,245,240,.92);backdrop-filter:blur(12px);border-bottom:1px solid var(--rule)}
        .brandmark{font-family:'Newsreader',serif;font-weight:500;font-size:25px;color:var(--ink);
          text-decoration:none;letter-spacing:-.02em}
        .brandsub{border-left:1px solid var(--rule2);padding-left:22px;color:var(--dim)}
        .navspace{flex:1}
        .backlink{color:var(--ink2);text-decoration:none;transition:color .18s}
        .backlink:hover{color:var(--kraft)}

        header.top{padding:72px 0 8px}
        .kick{display:flex;align-items:center;gap:14px;margin-bottom:24px}
        .kick .mono{color:var(--kraft)}
        .kick i{display:block;flex:1;height:1px;background:var(--rule)}
        header.top h1{font-size:clamp(31px,4.4vw,46px);margin-bottom:20px}
        header.top .stand{font-size:18px;color:var(--ink2);line-height:1.62}

        .body{padding:44px 0 0}
        .body h2{font-family:'Newsreader',serif;font-weight:500;font-size:26px;color:var(--ink);
          margin:52px 0 16px;line-height:1.2}
        .body h2:first-child{margin-top:0}
        .body p{margin-bottom:16px;font-size:16.5px;line-height:1.7}
        .body p b{color:var(--ink);font-weight:500}
        .body ul{list-style:none;display:flex;flex-direction:column;gap:11px;margin:0 0 18px}
        .body li{display:flex;gap:13px;align-items:baseline;font-size:16px}
        .body li::before{content:'';width:5px;height:5px;border-radius:50%;background:var(--kraft);
          flex-shrink:0;transform:translateY(-3px)}

        .pull{background:var(--kraftbg);border-left:2px solid var(--kraft);
          padding:22px 26px;margin:30px 0;border-radius:0 4px 4px 0}
        .pull p{margin:0;font-family:'Newsreader',serif;font-size:20px;color:var(--ink);line-height:1.4}

        .srcs{margin:26px 0 8px;border-top:1px solid var(--rule)}
        .src{border-bottom:1px solid var(--rule);padding:22px 0;display:grid;
          grid-template-columns:52px 1fr;gap:20px;align-items:start}
        .src .n{font-family:'IBM Plex Mono',monospace;font-size:12px;color:var(--kraft);
          letter-spacing:.1em;padding-top:4px}
        .src .claim{font-family:'Newsreader',serif;font-size:19px;color:var(--ink);
          line-height:1.32;margin-bottom:9px}
        .src .meta{font-size:13px;color:var(--dim);margin-bottom:9px}
        .src .note{font-size:14px;color:var(--ink2);line-height:1.55;margin-bottom:11px}
        .src a{font-size:13.5px;color:var(--kraft);text-decoration:none;
          border-bottom:1px solid rgba(138,106,69,.35);padding-bottom:1px;transition:border-color .2s}
        .src a:hover{border-color:var(--kraft)}

        .warn{background:var(--ink);color:var(--paper);border-radius:5px;padding:30px 30px 32px;margin:34px 0}
        .warn .mono{color:var(--kraft);display:block;margin-bottom:15px}
        .warn h3{font-family:'Newsreader',serif;font-weight:500;font-size:23px;color:#fff;
          margin-bottom:13px;line-height:1.24}
        .warn p{color:#C9C3B7;font-size:15.5px;line-height:1.68;margin-bottom:13px}
        .warn p:last-child{margin-bottom:0}
        .warn b{color:#fff;font-weight:500}

        .honest{border:1px solid var(--rule2);border-radius:5px;padding:30px 30px 32px;
          margin:34px 0;background:var(--paper2)}
        .honest .mono{color:var(--kraft);display:block;margin-bottom:15px}
        .honest h3{font-family:'Newsreader',serif;font-weight:500;font-size:23px;color:var(--ink);
          margin-bottom:13px;line-height:1.24}
        .honest ul{margin-bottom:0}

        .foot-cta{margin:56px 0 0;padding:38px 0 0;border-top:1px solid var(--rule);text-align:center}
        .foot-cta p{color:var(--ink2);margin-bottom:22px}
        .btn{display:inline-flex;align-items:center;gap:9px;padding:13px 26px;border-radius:100px;
          font-size:14.5px;text-decoration:none;background:var(--ink);color:var(--paper);
          font-weight:500;transition:background .2s,transform .2s}
        .btn:hover{background:var(--kraft);transform:translateY(-2px)}

        footer{border-top:1px solid var(--rule);padding:32px 32px 48px;margin-top:72px;position:relative;z-index:2}
        .foot{max-width:820px;margin:0 auto;display:flex;justify-content:space-between;
          align-items:center;gap:20px;flex-wrap:wrap}
        .footlinks{display:flex;gap:24px;flex-wrap:wrap}
        .footlinks a{text-decoration:none;color:var(--dim);transition:color .18s}
        .footlinks a:hover{color:var(--ink)}
        .foot .mono{color:var(--dim)}

        @media(max-width:620px){
          .brandsub{display:none}
          .src{grid-template-columns:1fr;gap:8px}
          .src .n{padding-top:0}
        }
      `}</style>

      <nav className="nav">
        <a className="brandmark" href="/">Marlo</a>
        <span className="mono brandsub">The system behind Brown Bag</span>
        <span className="navspace" />
        <a className="mono backlink" href="/">← Back to Marlo</a>
      </nav>

      <header className="top">
        <div className="wrap">
          <div className="kick">
            <span className="mono">Sources</span><i />
            <span className="mono" style={{ color: 'var(--dim)' }}>Updated Aug 2026</span>
          </div>
          <h1 className="serif">Where the numbers on our front page come from.</h1>
          <p className="stand">
            We say local roundup newsletters get opened 30 to 55% of the time. That's someone
            else's number, not ours. Here's whose it is, what it does prove, and what it doesn't.
          </p>
        </div>
      </header>

      <main className="body">
        <div className="wrap">

          <h2>The short version</h2>
          <p>
            Nobody has run Brown Bag yet, so we have no numbers of our own. What we can point to
            is that <b>the format works elsewhere.</b> Local roundup newsletters, the kind that
            cover a whole area rather than one business, get read at rates most brand email
            doesn't reach.
          </p>
          <p>
            Two networks are worth looking at. Axios Local now runs in 35 cities with more than
            two million subscribers. 6AM City runs a similar model and reported profitability
            earlier this year.
          </p>

          <div className="pull">
            <p>
              People who ignore brand email still open the one about their neighborhood.
              That's the whole bet, and it isn't ours alone.
            </p>
          </div>

          <h2>The sources</h2>
          <div className="srcs">
            {SOURCES.map((s) => (
              <div className="src" key={s.n}>
                <span className="n">{s.n}</span>
                <div>
                  <div className="claim">{s.claim}</div>
                  <div className="meta">{s.pub} · {s.date}</div>
                  <div className="note">{s.note}</div>
                  <a href={s.url} target="_blank" rel="noopener noreferrer">Read the source ↗</a>
                </div>
              </div>
            ))}
          </div>

          <div className="warn">
            <span className="mono">Read this before quoting the number</span>
            <h3>Open rates got less trustworthy in 2021.</h3>
            <p>
              Apple Mail Privacy Protection pre-loads images in email, including the invisible
              pixel that email tools use to count opens. For anyone reading in Apple Mail, an
              open gets counted whether or not a human looked at it.
            </p>
            <p>
              That's why the same year's benchmarks report an average open rate of either
              <b> 21% or 49%.</b> Both are correct. They're measuring different things.
            </p>
            <p>
              So treat any open rate published after 2021 as a ceiling, not a fact. That includes
              the ones on this page. <b>The comparison still holds</b> because the inflation
              applies to brand email and local newsletters equally, but the absolute numbers
              are softer than they look.
            </p>
          </div>

          <h2>What this proves</h2>
          <ul>
            <li>A newsletter about a whole area is something people will subscribe to and keep opening.</li>
            <li>The model scales past one city. Axios is heading for 43, and 6AM City runs hundreds of sends.</li>
            <li>It can be a business. 6AM City reports profitability, on roughly 50,000 subscribers per market.</li>
          </ul>

          <h2>What it doesn't prove</h2>
          <ul>
            <li>Nothing here is about Brown Bag. We haven't sent an issue yet.</li>
            <li>Axios and 6AM City write local news. We write about the businesses themselves. Different content, and the reading habit may not transfer.</li>
            <li>Axios Local still isn't profitable after four years. Scale and a working business are not the same thing.</li>
            <li>Every open rate on this page is self-reported by the company it flatters. None of it is audited.</li>
          </ul>

          <div className="honest">
            <span className="mono">What we'll replace this page with</span>
            <h3>Our own numbers, as soon as we have any.</h3>
            <ul>
              <li>Open rate per issue, and how it moves over time</li>
              <li>Unsubscribe rate, which is the number we actually watch</li>
              <li>How many readers click through to a business</li>
              <li>Whether a business's own list grows or shrinks while they're in Brown Bag</li>
            </ul>
          </div>

          <p style={{ marginTop: 26 }}>
            That last one matters most. The obvious worry is that we take subscribers a business
            would otherwise have won for themselves. <b>We think the opposite happens</b>, because
            the person who joins a neighborhood roundup was never going to join a single-shop list.
            But we think it. We haven't measured it. When we have, it goes here.
          </p>

          <div className="foot-cta">
            <p>Questions about any of this, or want to see the working?</p>
            <a className="btn" href="mailto:hello@marlo021.ai?subject=Question about your sources">
              hello@marlo021.ai →
            </a>
          </div>
        </div>
      </main>

      <footer>
        <div className="foot">
          <a className="brandmark" href="/" style={{ fontSize: 21 }}>Marlo</a>
          <div className="footlinks">
            <a className="mono" href="/privacy">Privacy</a>
            <a className="mono" href="/terms">Terms</a>
            <a className="mono" href="mailto:hello@marlo021.ai">Contact</a>
          </div>
          <span className="mono">© 2026 · Seattle</span>
        </div>
      </footer>
    </>
  )
}