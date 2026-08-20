import { useEffect, useRef, useState } from 'react'

/* ── the conversation that plays out in Fig. 02 ── */
const SCRIPT: { role: 'agent' | 'maker'; text: string; wait: number }[] = [
  { role: 'agent', text: 'Is the sourdough back this week, or still on pause?', wait: 1500 },
  { role: 'maker', text: "Not yet. But we sold out of chili oil by 11 — that never happens.", wait: 1900 },
  { role: 'agent', text: 'Sold out by 11. How many jars did you bring?', wait: 1500 },
  { role: 'maker', text: '40. Last month I made 60 and had 20 left, so I thought 40 was safe. Wrong.', wait: 2100 },
  { role: 'agent', text: 'Any idea what changed?', wait: 1300 },
  { role: 'maker', text: "Someone posted a video of me at the July demo. 90,000 views. I don't have TikTok.", wait: 2300 },
  { role: 'maker', text: 'My daughter made me watch it four times. She’s twelve.', wait: 2000 },
]

const HARVEST = [
  { k: 'Person', v: 'Mei — and her twelve-year-old' },
  { k: 'Stake', v: 'Sold out early, unexpectedly' },
  { k: 'Scene', v: 'A queue before setup finished' },
  { k: 'Quote', v: '“I don’t have TikTok.”' },
]

/* ── the two inboxes, dealt block by block ── */
type Blk = { slot: string; head: string; sub?: string; why?: string; own: boolean }

const SAM: Blk[] = [
  { slot: 'Slot 1 · Greeting', head: 'Week of August 12', own: false },
  { slot: 'Slot 2 · Story', head: "She's not famous. She's out of chili oil.", sub: 'Cedar Bakery · Ballard', why: 'Follows Cedar · scanned 3×', own: true },
  { slot: 'Slot 3 · Story', head: "A third of the tomatoes split. Now there's sauce.", sub: 'Hollow Ridge Farm', why: 'Follows Hollow Ridge · scanned 1×', own: true },
  { slot: 'Slot 4 · Sponsor', head: 'Ballard Hardware', own: false },
  { slot: 'Slot 5 · Story', head: 'The neighbours knocked to ask what was burning', sub: 'Cedar Bakery · Ballard', why: 'Follows Cedar · unseen', own: true },
  { slot: 'Slot 6 · This week', head: 'Three stalls you follow are out on Saturday', own: false },
]

const JO: Blk[] = [
  { slot: 'Slot 1 · Greeting', head: 'Week of August 12', own: false },
  { slot: 'Slot 2 · Story', head: "A third of the tomatoes split. Now there's sauce.", sub: 'Hollow Ridge Farm', why: 'Follows Hollow Ridge · scanned 4×', own: true },
  { slot: 'Slot 3 · Story', head: 'Twelve years of the same Saturday', sub: 'Fiber & Fawn · Ballard', why: 'Nearby · matches interests', own: true },
  { slot: 'Slot 4 · Sponsor', head: 'Ballard Hardware', own: false },
  { slot: 'Slot 5 · Story', head: "She's not famous. She's out of chili oil.", sub: 'Cedar Bakery · discovery', why: 'Discovery — a stall she hasn’t met', own: true },
  { slot: 'Slot 6 · This week', head: 'One stall you follow is out on Saturday', own: false },
]

const TICKER = [
  'She’s not famous. She’s out of chili oil.',
  'A third of the tomatoes split. Now there’s sauce.',
  'Twelve years of the same Saturday',
  'The neighbours knocked to ask what was burning',
  'He named the sourdough starter after his father',
  'Forty jars, and a queue before setup finished',
  'The dog got into the pumpkins again',
]

export function Landing() {
  const [dealt, setDealt] = useState(0)
  const [line, setLine] = useState(0)
  const [typing, setTyping] = useState(false)
  const [harvest, setHarvest] = useState(0)
  const dealRef = useRef<HTMLDivElement>(null)
  const chatRef = useRef<HTMLDivElement>(null)
  const scrapRef = useRef<HTMLDivElement>(null)

  /* fonts */
  useEffect(() => {
    const pre = document.createElement('link')
    pre.rel = 'preconnect'; pre.href = 'https://fonts.gstatic.com'; pre.crossOrigin = 'anonymous'
    document.head.appendChild(pre)
    const f = document.createElement('link')
    f.rel = 'stylesheet'
    f.href = 'https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300..600;1,6..72,300..500&family=Instrument+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap'
    document.head.appendChild(f)
  }, [])

  const reduced = typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  /* scroll reveals */
  useEffect(() => {
    if (reduced) {
      document.querySelectorAll('.rise').forEach(el => el.classList.add('shown'))
      setDealt(99); setLine(SCRIPT.length); setHarvest(HARVEST.length)
      return
    }
    const io = new IntersectionObserver(
      es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('shown'); io.unobserve(e.target) } }),
      { threshold: 0.1, rootMargin: '0px 0px -60px 0px' }
    )
    document.querySelectorAll('.rise').forEach(el => io.observe(el))
    return () => io.disconnect()
  }, [reduced])

  /* deal the blocks when Fig 01 arrives */
  useEffect(() => {
    if (reduced || !dealRef.current) return
    const io = new IntersectionObserver(es => {
      if (es[0].isIntersecting) {
        io.disconnect()
        let n = 0
        const tick = () => {
          n += 1; setDealt(n)
          if (n < 12) setTimeout(tick, 190)
        }
        setTimeout(tick, 260)
      }
    }, { threshold: 0.25 })
    io.observe(dealRef.current)
    return () => io.disconnect()
  }, [reduced])

  /* play the conversation when Fig 02 arrives */
  useEffect(() => {
    if (reduced || !chatRef.current) return
    const timers: number[] = []
    const io = new IntersectionObserver(es => {
      if (es[0].isIntersecting) {
        io.disconnect()
        let t = 400
        SCRIPT.forEach((s, i) => {
          timers.push(window.setTimeout(() => setTyping(true), t))
          t += 520
          timers.push(window.setTimeout(() => { setTyping(false); setLine(i + 1) }, t))
          t += s.wait
        })
        HARVEST.forEach((_, i) => {
          timers.push(window.setTimeout(() => setHarvest(i + 1), t + i * 320))
        })
      }
    }, { threshold: 0.3 })
    io.observe(chatRef.current)
    return () => { io.disconnect(); timers.forEach(clearTimeout) }
  }, [reduced])

  /* gentle parallax on the hero scraps */
  useEffect(() => {
    if (reduced || !scrapRef.current) return
    let raf = 0
    const onScroll = () => {
      if (raf) return
      raf = requestAnimationFrame(() => {
        const y = window.scrollY
        scrapRef.current?.style.setProperty('--py', `${y * 0.06}px`)
        scrapRef.current?.style.setProperty('--py2', `${y * -0.035}px`)
        raf = 0
      })
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => { window.removeEventListener('scroll', onScroll); if (raf) cancelAnimationFrame(raf) }
  }, [reduced])

  const chat = SCRIPT.slice(0, line)

  return (
    <>
      <style>{`
        :root {
          --paper:#F7F5F0; --paper2:#FFFFFF; --tint:#EFEBE2;
          --ink:#14130F; --ink2:#46433C; --dim:#8B877D;
          --rule:#DCD6C9; --rule2:#C6BEAC;
          --kraft:#8A6A45; --kraftbg:#F0E7D9; --moss:#6E7A55;
        }
        *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
        html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
        body{
          background:var(--paper);color:var(--ink2);
          font-family:'Instrument Sans',system-ui,sans-serif;
          font-size:16px;line-height:1.6;overflow-x:hidden;-webkit-font-smoothing:antialiased;
        }
        /* paper grain */
        body::before{
          content:'';position:fixed;inset:0;z-index:1;pointer-events:none;opacity:.5;
          background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='140' height='140' filter='url(%23n)' opacity='.045'/%3E%3C/svg%3E");
        }
        a{color:inherit}
        :focus-visible{outline:2px solid var(--kraft);outline-offset:3px}

        .mono{font-family:'IBM Plex Mono',ui-monospace,monospace;font-size:11px;letter-spacing:.18em;text-transform:uppercase}
        .serif{font-family:'Newsreader',Georgia,serif;font-weight:400;color:var(--ink);letter-spacing:-.015em;line-height:1.08}
        .serif em{font-style:italic;color:var(--kraft)}
        .wrap{max-width:1140px;margin:0 auto;padding:0 32px;position:relative;z-index:2}
        .rise{opacity:0;transform:translateY(22px);transition:opacity .8s ease,transform .8s ease}
        .rise.shown{opacity:1;transform:none}

        /* nav */
        .nav{position:fixed;inset:0 0 auto 0;z-index:60;display:flex;align-items:center;gap:26px;
          padding:18px 32px;background:rgba(247,245,240,.9);backdrop-filter:blur(12px);border-bottom:1px solid var(--rule)}
        .brandmark{font-family:'Newsreader',serif;font-weight:500;font-size:25px;color:var(--ink);text-decoration:none;letter-spacing:-.02em}
        .brandsub{border-left:1px solid var(--rule2);padding-left:22px;color:var(--dim)}
        .navspace{flex:1}
        .navlinks{display:flex;gap:26px;align-items:center}
        .navlinks a.mono{color:var(--ink2);text-decoration:none;transition:color .18s}
        .navlinks a.mono:hover{color:var(--kraft)}
        .navcta{background:var(--ink);color:var(--paper)!important;padding:11px 20px;border-radius:100px;
          text-decoration:none;display:inline-flex;align-items:center;gap:8px;transition:background .2s}
        .navcta:hover{background:var(--kraft)}

        /* hero */
        .frame{position:relative;padding:132px 0 70px}
        .corner{position:absolute;width:18px;height:18px;border:1px solid var(--rule2);z-index:2}
        .corner.tl{top:108px;left:32px;border-right:0;border-bottom:0}
        .corner.tr{top:108px;right:32px;border-left:0;border-bottom:0}
        .kicker{display:flex;align-items:center;justify-content:center;gap:18px;margin-bottom:40px}
        .kicker .mono{color:var(--dim)}
        .kicker i{display:block;width:54px;height:1px;background:var(--rule2)}
        .hero-inner{position:relative;text-align:center}
        .hero-inner h1{font-size:clamp(40px,7vw,84px);max-width:16ch;margin:0 auto}
        .subline{margin:30px auto 0;max-width:58ch;font-size:clamp(16px,1.6vw,19px);color:var(--ink2);line-height:1.62}
        .acts{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:36px}
        .btn{display:inline-flex;align-items:center;gap:9px;padding:13px 26px;border-radius:100px;
          font-size:14.5px;text-decoration:none;transition:background .2s,border-color .2s,color .2s,transform .2s}
        .btn-dark{background:var(--ink);color:var(--paper);font-weight:500}
        .btn-dark:hover{background:var(--kraft);transform:translateY(-2px)}
        .btn-line{border:1px solid var(--rule2);color:var(--ink)}
        .btn-line:hover{border-color:var(--ink);transform:translateY(-2px)}

        /* scraps */
        .scrap{position:absolute;width:208px;background:var(--paper2);border:1px solid var(--rule);
          border-radius:3px;padding:15px 16px 17px;box-shadow:0 12px 30px rgba(20,19,15,.07);
          text-align:left;pointer-events:none;animation:drop .9s cubic-bezier(.2,.7,.3,1) both}
        .scrap .mono{color:var(--kraft);font-size:9px;display:block;margin-bottom:8px}
        .scrap .st{font-family:'Newsreader',serif;font-size:16px;color:var(--ink);line-height:1.24}
        .scrap .sv{font-size:11px;color:var(--dim);margin-top:8px}
        .scrap .band{height:58px;border-radius:2px;margin-bottom:11px}
        @keyframes drop{from{opacity:0;transform:translateY(-26px) rotate(0deg)}}
        .s1{top:4px;left:-8px;transform:translateY(var(--py,0)) rotate(-6.5deg);animation-delay:.15s}
        .s2{top:250px;left:30px;transform:translateY(var(--py2,0)) rotate(3.5deg);animation-delay:.35s}
        .s3{top:30px;right:-6px;transform:translateY(var(--py2,0)) rotate(5.5deg);animation-delay:.25s}
        .s4{top:274px;right:26px;transform:translateY(var(--py,0)) rotate(-4deg);animation-delay:.45s}
        @media(max-width:1180px){.scrap{display:none}}

        /* ticker */
        .ticker{border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);
          padding:15px 0;overflow:hidden;background:var(--tint);position:relative;z-index:2}
        .ticker-track{display:flex;gap:0;width:max-content;animation:slide 46s linear infinite}
        .ticker:hover .ticker-track{animation-play-state:paused}
        @keyframes slide{to{transform:translateX(-50%)}}
        .tick{font-family:'Newsreader',serif;font-size:19px;color:var(--ink);
          padding:0 30px;white-space:nowrap;display:flex;align-items:center;gap:30px}
        .tick::after{content:'';width:5px;height:5px;border-radius:50%;background:var(--kraft);flex-shrink:0}

        /* sections */
        .sec{padding:92px 0;border-top:1px solid var(--rule);position:relative;z-index:2}
        .sechead{display:flex;align-items:center;gap:18px;margin-bottom:38px;flex-wrap:wrap}
        .sechead .mono{color:var(--dim)}
        .sechead .mono.k{color:var(--kraft)}
        .sechead i{flex:1;height:1px;background:var(--rule);min-width:20px}
        .sec h2{font-size:clamp(30px,4.4vw,50px);max-width:20ch;margin-bottom:20px}
        .note{color:var(--ink2);max-width:60ch;font-size:16.5px}

        /* inboxes */
        .split{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:40px}
        .inbox{background:var(--paper2);border:1px solid var(--rule);border-radius:4px;overflow:hidden}
        .inbox-top{display:flex;align-items:center;justify-content:space-between;padding:13px 17px;
          border-bottom:1px solid var(--rule);background:var(--tint)}
        .inbox-top .who{font-size:13px;color:var(--ink);font-weight:500}
        .inbox-top .mono{color:var(--dim)}
        .inbox-body{padding:16px 17px 20px;min-height:392px}
        .blk{border:1px solid var(--rule);border-radius:3px;padding:12px 14px;margin-bottom:9px;
          position:relative;opacity:0;transform:translateY(10px) scale(.98);
          transition:opacity .45s ease,transform .45s cubic-bezier(.2,.7,.3,1),box-shadow .2s}
        .blk.in{opacity:1;transform:none}
        .blk .mono{color:var(--dim);font-size:9px;display:block;margin-bottom:6px}
        .blk .h{font-family:'Newsreader',serif;font-size:16px;color:var(--ink);line-height:1.26;display:block}
        .blk .v{font-size:11.5px;color:var(--dim);margin-top:5px;display:block}
        .blk.same{background:var(--tint)}
        .blk.pers{background:var(--kraftbg);border-color:#E0CFB4;cursor:default}
        .blk.pers .mono{color:var(--kraft)}
        .blk.pers:hover{box-shadow:0 6px 18px rgba(20,19,15,.09)}
        .why{position:absolute;left:12px;right:12px;bottom:calc(100% + 7px);
          background:var(--ink);color:var(--paper);padding:8px 11px;border-radius:4px;
          font-size:11.5px;line-height:1.4;opacity:0;transform:translateY(5px);
          transition:opacity .2s,transform .2s;pointer-events:none;z-index:5}
        .why::after{content:'';position:absolute;top:100%;left:22px;border:5px solid transparent;border-top-color:var(--ink)}
        .blk.pers:hover .why{opacity:1;transform:none}
        .legend{display:flex;gap:26px;flex-wrap:wrap;margin-top:24px;align-items:center}
        .legend div{display:flex;align-items:center;gap:9px;font-size:13px;color:var(--ink2)}
        .sw{width:12px;height:12px;border-radius:2px;border:1px solid var(--rule2)}
        .sw.k{background:var(--kraftbg);border-color:#E0CFB4}
        .sw.n{background:var(--tint)}
        .mockmark{margin-top:16px;color:var(--dim);font-size:12.5px;font-style:italic}

        /* conversation demo */
        .demo{display:grid;grid-template-columns:1.1fr .85fr;gap:24px;margin-top:38px}
        .chatbox{background:var(--paper2);border:1px solid var(--rule);border-radius:4px;
          padding:20px;min-height:400px;display:flex;flex-direction:column;gap:11px}
        .chatbox .hd{display:flex;justify-content:space-between;align-items:center;
          padding-bottom:14px;border-bottom:1px solid var(--rule);margin-bottom:4px}
        .chatbox .hd .mono{color:var(--dim)}
        .live{display:flex;align-items:center;gap:7px;color:var(--moss)}
        .live i{width:6px;height:6px;border-radius:50%;background:var(--moss);animation:blip 1.6s ease infinite}
        @keyframes blip{0%,100%{opacity:1}50%{opacity:.25}}
        .bub{max-width:84%;padding:11px 14px;border-radius:12px;font-size:14.5px;line-height:1.5;
          animation:pop .4s cubic-bezier(.2,.7,.3,1) both}
        @keyframes pop{from{opacity:0;transform:translateY(8px)}}
        .bub.agent{background:var(--tint);color:var(--ink2);border-bottom-left-radius:3px;align-self:flex-start}
        .bub.maker{background:var(--kraftbg);color:var(--ink);border-bottom-right-radius:3px;align-self:flex-end}
        .dots{display:flex;gap:4px;padding:13px 15px;background:var(--tint);border-radius:12px;
          border-bottom-left-radius:3px;align-self:flex-start;width:fit-content}
        .dots i{width:5px;height:5px;border-radius:50%;background:var(--dim);animation:bob 1.1s ease infinite}
        .dots i:nth-child(2){animation-delay:.16s}
        .dots i:nth-child(3){animation-delay:.32s}
        @keyframes bob{0%,60%,100%{opacity:.3;transform:translateY(0)}30%{opacity:1;transform:translateY(-4px)}}
        .harvest{background:var(--paper2);border:1px solid var(--rule);border-radius:4px;padding:22px 22px 24px}
        .harvest .mono{color:var(--kraft);display:block;margin-bottom:16px}
        .hrow{display:flex;gap:14px;padding:12px 0;border-bottom:1px solid var(--rule);
          opacity:0;transform:translateX(-8px);transition:opacity .45s ease,transform .45s ease}
        .hrow.in{opacity:1;transform:none}
        .hrow:last-child{border-bottom:0}
        .hrow .k{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.14em;
          text-transform:uppercase;color:var(--dim);min-width:52px;padding-top:3px}
        .hrow .v{font-size:14.5px;color:var(--ink);line-height:1.42}
        .harvest .foot{margin-top:16px;padding-top:14px;border-top:1px solid var(--rule);
          font-size:12.5px;color:var(--dim)}

        /* pipeline */
        .pipe{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--rule);
          border-radius:4px;overflow:hidden;background:var(--paper2);margin-top:34px}
        .stage{padding:30px 26px 32px;border-right:1px solid var(--rule);transition:background .3s}
        .stage:last-child{border-right:0}
        .stage:hover{background:var(--tint)}
        .stage .mono{color:var(--kraft);display:block;margin-bottom:18px}
        .stage h3{font-family:'Newsreader',serif;font-weight:500;font-size:21px;color:var(--ink);margin-bottom:11px;line-height:1.2}
        .stage p{font-size:14px;color:var(--ink2);line-height:1.62}
        .stage .out{margin-top:18px;padding-top:14px;border-top:1px solid var(--rule);font-size:12px;color:var(--dim)}
        .stage .out b{color:var(--ink);font-weight:500}

        /* limits */
        .bounds{display:grid;grid-template-columns:repeat(3,1fr);gap:26px}
        .bound{border-top:2px solid var(--kraft);padding-top:20px;transition:transform .3s}
        .bound:hover{transform:translateY(-4px)}
        .bound p{font-family:'Newsreader',serif;font-size:22px;color:var(--ink);line-height:1.26;margin-bottom:12px}
        .bound span{font-size:14.5px;color:var(--ink2)}

        /* matching */
        .matchgrid{display:grid;grid-template-columns:1.02fr 1fr;gap:52px;align-items:start;margin-top:34px}
        .rules{border:1px solid var(--rule);border-radius:4px;overflow:hidden;background:var(--paper2)}
        .rule-row{padding:17px 20px;display:flex;gap:18px;align-items:baseline;
          border-bottom:1px solid var(--rule);transition:background .2s}
        .rule-row:last-child{border-bottom:0}
        .rule-row:hover{background:var(--kraftbg)}
        .rule-row .mono{color:var(--kraft);white-space:nowrap;min-width:82px}
        .rule-row .t{font-size:14.5px;color:var(--ink)}
        .rule-row .t em{font-style:normal;color:var(--dim);display:block;margin-top:4px;font-size:13px}
        .prose p{color:var(--ink2);margin-bottom:17px;font-size:16px}
        .prose p strong{color:var(--ink);font-weight:500}
        .prose p:last-child{margin-bottom:0}

        /* partners */
        .cols{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:34px}
        .card{background:var(--paper2);border:1px solid var(--rule);border-radius:4px;
          padding:32px 30px 34px;transition:transform .3s,box-shadow .3s}
        .card:hover{transform:translateY(-4px);box-shadow:0 14px 32px rgba(20,19,15,.07)}
        .card .mono{color:var(--kraft);display:block;margin-bottom:17px}
        .card h3{font-family:'Newsreader',serif;font-weight:500;font-size:24px;color:var(--ink);margin-bottom:12px;line-height:1.2}
        .card p{font-size:15px;color:var(--ink2);margin-bottom:18px}
        .facts{list-style:none;display:flex;flex-direction:column;gap:10px}
        .facts li{display:flex;gap:12px;font-size:14.5px;color:var(--ink);align-items:baseline}
        .facts li::before{content:'';width:5px;height:5px;border-radius:50%;background:var(--kraft);flex-shrink:0;transform:translateY(-2px)}

        /* close */
        .close{padding:100px 0 110px;border-top:1px solid var(--rule);text-align:center;position:relative;z-index:2}
        .close h2{font-size:clamp(30px,4.2vw,48px);max-width:21ch;margin:0 auto 24px}
        .close p{color:var(--ink2);max-width:54ch;margin:0 auto 32px;font-size:16.5px}

        footer{border-top:1px solid var(--rule);padding:32px 32px 48px;position:relative;z-index:2}
        .foot{max-width:1140px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap}
        .footlinks{display:flex;gap:24px;flex-wrap:wrap}
        .footlinks a{text-decoration:none;color:var(--dim);transition:color .18s}
        .footlinks a:hover{color:var(--ink)}
        .foot .mono{color:var(--dim)}

        @media(max-width:940px){
          .split,.bounds,.cols,.matchgrid,.demo{grid-template-columns:1fr}
          .pipe{grid-template-columns:1fr 1fr}
          .stage:nth-child(2){border-right:0}
          .stage:nth-child(1),.stage:nth-child(2){border-bottom:1px solid var(--rule)}
          .matchgrid{gap:36px}
          .inbox-body{min-height:0}
        }
        @media(max-width:620px){
          .navlinks a.mono:not(.navcta){display:none}
          .brandsub{display:none}
          .pipe{grid-template-columns:1fr}
          .stage{border-right:0;border-bottom:1px solid var(--rule)}
          .stage:last-child{border-bottom:0}
          .frame{padding-top:116px}
          .sec{padding:66px 0}
          .corner{display:none}
          .tick{font-size:16px;padding:0 20px}
        }
        @media(prefers-reduced-motion:reduce){
          *{animation:none!important;transition:none!important}
          .blk{opacity:1;transform:none}
          .hrow{opacity:1;transform:none}
        }
      `}</style>

      <nav className="nav">
        <a className="brandmark" href="/">Marlo</a>
        <span className="mono brandsub">The system behind Brown Bag</span>
        <span className="navspace" />
        <div className="navlinks">
          <a className="mono" href="#pipeline">Pipeline</a>
          <a className="mono" href="#limits">Limits</a>
          <a className="mono" href="#matching">Matching</a>
          <a className="mono" href="#partners">Partners</a>
          <a className="mono navcta" href="mailto:hello@marlo021.ai">Get in touch →</a>
        </div>
      </nav>

      {/* ── HERO ── */}
      <header className="frame">
        <span className="corner tl" /><span className="corner tr" />
        <div className="wrap">
          <div className="kicker"><i /><span className="mono">Seattle · Weekly · Est. 2026</span><i /></div>
          <div className="hero-inner" ref={scrapRef}>
            <div className="scrap s1">
              <span className="mono">Cedar Bakery</span>
              <div className="st">She's not famous. She's out of chili oil.</div>
              <div className="sv">Ballard · 187 words</div>
            </div>
            <div className="scrap s2">
              <div className="band" style={{ background: 'linear-gradient(150deg,#E8DFCD,#D9CDB4)' }} />
              <span className="mono">Hollow Ridge</span>
              <div className="st">A third of the tomatoes split. Now there's sauce.</div>
            </div>
            <div className="scrap s3">
              <div className="band" style={{ background: 'linear-gradient(150deg,#DFE3D5,#CBD2BE)' }} />
              <span className="mono">Fiber &amp; Fawn</span>
              <div className="st">Twelve years of the same Saturday</div>
            </div>
            <div className="scrap s4">
              <span className="mono">Pike Fish Co</span>
              <div className="st">The neighbours knocked to ask what was burning</div>
              <div className="sv">Ballard · 120 words</div>
            </div>

            <h1 className="serif">
              Vendors tell the stories.<br />
              Marlo works out <em>who should read them.</em>
            </h1>
            <p className="subline">
              Brown Bag is a weekly local newsletter. Marlo is the machinery underneath —
              it interviews makers, drafts what they said into a story, hands it to an editor,
              and builds a different issue for every reader.
            </p>
            <div className="acts">
              <a className="btn btn-dark" href="#pipeline">See how it works →</a>
              <a className="btn btn-line" href="mailto:hello@marlo021.ai">Talk to us</a>
            </div>
          </div>
        </div>
      </header>

      {/* ── TICKER ── */}
      <div className="ticker">
        <div className="ticker-track">
          {[...TICKER, ...TICKER].map((t, i) => <span className="tick" key={i}>{t}</span>)}
        </div>
      </div>

      {/* ── FIG 01 · TWO INBOXES ── */}
      <section className="sec rise" ref={dealRef}>
        <div className="wrap">
          <div className="sechead">
            <span className="mono k">Fig. 01</span>
            <span className="mono">One issue · Two readers</span><i />
          </div>
          <h2 className="serif">The same week. Two different emails.</h2>
          <p className="note">
            Sam scans the bakery's code most Saturdays. Jo scans the farm's. They both get
            Brown Bag No. 6, and the stories inside are not the same.
            <br /><span style={{ color: 'var(--dim)', fontSize: 14 }}>Hover a highlighted block to see why it was chosen.</span>
          </p>

          <div className="split">
            {[{ who: 'Sam · follows Cedar Bakery', rows: SAM, off: 0 },
              { who: 'Jo · follows Hollow Ridge Farm', rows: JO, off: 1 }].map((box, bi) => (
              <div className="inbox" key={bi}>
                <div className="inbox-top">
                  <span className="who">{box.who}</span>
                  <span className="mono">No. 06</span>
                </div>
                <div className="inbox-body">
                  {box.rows.map((b, i) => (
                    <div
                      key={i}
                      className={`blk ${b.own ? 'pers' : 'same'} ${dealt > i * 2 + box.off ? 'in' : ''}`}
                    >
                      {b.why && <span className="why">{b.why}</span>}
                      <span className="mono">{b.slot}</span>
                      <span className="h">{b.head}</span>
                      {b.sub && <span className="v">{b.sub}</span>}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="legend">
            <div><span className="sw k" /> Chosen for this reader</div>
            <div><span className="sw n" /> Same for everyone</div>
          </div>
          <p className="mockmark">Illustration. Real issues follow the same nine-slot structure and stay under 1,000 words.</p>
        </div>
      </section>

      {/* ── FIG 02 · THE INTERVIEW ── */}
      <section className="sec rise" id="pipeline" ref={chatRef}>
        <div className="wrap">
          <div className="sechead">
            <span className="mono k">Fig. 02</span>
            <span className="mono">Gathering · What an interview looks like</span><i />
          </div>
          <h2 className="serif">It asks about the week, not about the product.</h2>
          <p className="note">
            The interviewer holds what it already knows about a maker, so it can ask something
            specific. "Anything new?" gets nothing. "Is the sourdough back?" gets a conversation.
          </p>

          <div className="demo">
            <div className="chatbox">
              <div className="hd">
                <span className="mono">Cedar Bakery · Tuesday</span>
                <span className="mono live"><i />Live</span>
              </div>
              {chat.map((m, i) => (
                <div className={`bub ${m.role}`} key={i}>{m.text}</div>
              ))}
              {typing && <div className="dots"><i /><i /><i /></div>}
            </div>

            <div className="harvest">
              <span className="mono">What it kept</span>
              {HARVEST.map((h, i) => (
                <div className={`hrow ${harvest > i ? 'in' : ''}`} key={i}>
                  <span className="k">{h.k}</span>
                  <span className="v">{h.v}</span>
                </div>
              ))}
              <p className="foot">
                The transcript is stored word for word. Nothing published can say more than
                the maker said here.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── FIG 03 · PIPELINE ── */}
      <section className="sec rise">
        <div className="wrap">
          <div className="sechead">
            <span className="mono k">Fig. 03</span>
            <span className="mono">Pipeline · Conversation to inbox</span><i />
          </div>
          <h2 className="serif">Four stages. A person in the middle of every one.</h2>
          <p className="note">
            Marlo runs two separate agents on purpose. One is good at getting people to talk.
            The other is good at writing. Those are different jobs.
          </p>

          <div className="pipe">
            <div className="stage">
              <span className="mono">01 — Gather</span>
              <h3>Someone asks good questions</h3>
              <p>An agent talks to the maker about their week — what changed, what went wrong, what
                surprised them. Photos welcome. It never fishes for anything personal.</p>
              <div className="out">Output: <b>raw material</b>, kept word for word</div>
            </div>
            <div className="stage">
              <span className="mono">02 — Write</span>
              <h3>A second agent writes it up</h3>
              <p>It works only from what the maker actually said. It keeps their phrasing where it's
                good, uses one quote, and ends on a concrete detail rather than a moral.</p>
              <div className="out">Output: <b>a draft</b>, 120–200 words</div>
            </div>
            <div className="stage">
              <span className="mono">03 — Check</span>
              <h3>The maker sees it first</h3>
              <p>Before anyone else reads it, they can flag anything wrong. Then a human editor reads
                every draft and decides whether it runs.</p>
              <div className="out">Output: <b>approved</b>, or it doesn't go</div>
            </div>
            <div className="stage">
              <span className="mono">04 — Match</span>
              <h3>Each reader gets their own issue</h3>
              <p>Marlo builds one email per reader from the approved pool, led by the stalls they
                actually visit, with room kept for something they haven't met yet.</p>
              <div className="out">Output: <b>one issue</b>, many versions</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── FIG 04 · LIMITS ── */}
      <section className="sec rise" id="limits">
        <div className="wrap">
          <div className="sechead">
            <span className="mono k">Fig. 04</span>
            <span className="mono">Limits · What the system will not do</span><i />
          </div>
          <h2 className="serif">The rules matter more than the features.</h2>
          <p className="note" style={{ marginBottom: 40 }}>
            Three things are fixed. They're the reason a maker can hand us their story and a
            reader can keep opening the email.
          </p>
          <div className="bounds">
            <div className="bound">
              <p>Nothing is published without a person reading it first.</p>
              <span>Every story, every sponsor, every line. An editor approves it or it doesn't run.
                There is no automatic path to a reader's inbox.</span>
            </div>
            <div className="bound">
              <p>We never write a fact a maker didn't tell us.</p>
              <span>The transcript is kept unedited. Every published sentence traces back to something
                they actually said, and they can correct it at any point.</span>
            </div>
            <div className="bound">
              <p>We never tell a reader what we've worked out about them.</p>
              <span>Marlo says the cheese stall is back this week. It never says "because you keep
                buying bread." The targeting is invisible, and it stays that way.</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── FIG 05 · MATCHING ── */}
      <section className="sec rise" id="matching">
        <div className="wrap">
          <div className="sechead">
            <span className="mono k">Fig. 05</span>
            <span className="mono">Matching · How an issue gets built</span><i />
          </div>
          <h2 className="serif">Nobody fills in a form.</h2>

          <div className="matchgrid">
            <div className="rules">
              {[['Follows', 'Scanning a code at a stall', 'One scan starts it. More scans mean more weight.'],
                ['Interest', 'What those stalls sell', 'Bread, cheese, flowers — from where they stop.'],
                ['Nearby', 'Which part of town', 'Inferred from the stalls they visit, never asked.'],
                ['New', "A story they haven't seen", 'Once read, never sent again. Permanently.'],
                ['Variety', 'Not the same stall every week', 'A maker rests for a few issues after they appear.'],
                ['Discovery', "One stall they don't follow yet", "Held back on purpose, so the issue doesn't narrow."]
              ].map(([k, t, e], i) => (
                <div className="rule-row" key={i}>
                  <span className="mono">{k}</span>
                  <span className="t">{t}<em>{e}</em></span>
                </div>
              ))}
            </div>
            <div className="prose">
              <p>A reader never picks interests or sets preferences. They scan a code at a stall to
                subscribe, and every scan after that quietly says something about what they care about.</p>
              <p><strong>Most people follow one or two stalls</strong>, so most of an issue is made up
                of things they haven't chosen. That part matters more than the personalisation — it's
                how someone finds the cheese maker two rows over.</p>
              <p>And the seat kept for an unfamiliar maker is deliberate. Without it, a reader's issue
                narrows week by week until it only tells them what they already knew.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── FIG 06 · PARTNERS ── */}
      <section className="sec rise" id="partners">
        <div className="wrap">
          <div className="sechead">
            <span className="mono k">Fig. 06</span>
            <span className="mono">Working with Marlo</span><i />
          </div>
          <h2 className="serif">One market at a time, on purpose.</h2>
          <div className="cols">
            <div className="card">
              <span className="mono">For markets and platforms</span>
              <h3>Bring your makers, keep your relationship</h3>
              <p>A market gets one code to hand out. Makers sign themselves up with it and are live
                the same day — no account setup on your side, no data to hand over.</p>
              <ul className="facts">
                <li>Makers join with a code, not an approval queue</li>
                <li>Nobody sees anyone else's subscriber list</li>
                <li>Consent recorded at signup, unsubscribe is one click</li>
                <li>Every issue reports what ran and who opened it</li>
              </ul>
            </div>
            <div className="card">
              <span className="mono">For technical partners</span>
              <h3>The parts that could be an API</h3>
              <p>Marlo is built as separate stages, so any one of them can stand alone. Nothing is
                public yet — this is what we'd open first if there's a reason to.</p>
              <ul className="facts">
                <li>Interview → structured material from a conversation</li>
                <li>Draft → a story from material, with the source kept</li>
                <li>Match → a per-reader issue from an approved pool</li>
                <li>Deliver → sending, tracking, unsubscribes</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── CLOSE ── */}
      <section className="close rise">
        <div className="wrap">
          <h2 className="serif">If you make something and sell it near people, we'd like to talk.</h2>
          <p>Brown Bag is starting in Seattle. We're looking for makers and stallholders who have
            something to say and no good place to say it.</p>
          <div className="acts">
            <a className="btn btn-dark" href="mailto:hello@marlo021.ai">hello@marlo021.ai</a>
            <a className="btn btn-line" href="#pipeline">Read it again ↑</a>
          </div>
        </div>
      </section>

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