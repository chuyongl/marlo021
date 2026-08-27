import { useEffect, useRef, useState } from 'react'

/*  ──────────────────────────────────────────────────────────────
    PHOTOS

    Every <Photo> below renders an on-brand placeholder until a real
    image is dropped in. To add one:

        1. Put the file in  frontend/public/photos/
        2. Set  src="/photos/your-file.jpg"  on the <Photo>

    What to shoot (phone is fine, natural light, no flash):

      hero-a     tall  3:4   hands doing the work — kneading, wrapping,
                             tying, weighing. Faces optional.
      hero-b     tall  3:4   a stall from the customer's side, mid-morning
      strip-1..5 wide  4:3   produce, bread, flowers, a hand exchanging
                             change, a chalkboard sign
      ask-1..3   wide  4:3   quieter moments — an empty stall at setup,
                             a half-packed crate, a dog under a table

    Avoid: anything that looks like stock. No smiling models, no
    perfectly styled flat-lays, no aerial market shots. Slightly
    imperfect and specific beats polished and generic.
   ────────────────────────────────────────────────────────────── */

function Photo({
  src, alt, tone = 'wheat', ratio = '4 / 3', className = '',
}: { src?: string; alt: string; tone?: 'wheat' | 'sage' | 'clay' | 'plum' | 'ash'; ratio?: string; className?: string }) {
  const tones: Record<string, string> = {
    wheat: 'linear-gradient(148deg,#EFE3CC 0%,#DCC9A6 55%,#CDB88F 100%)',
    sage:  'linear-gradient(148deg,#E3E7D9 0%,#C9D2BB 55%,#B6C2A5 100%)',
    clay:  'linear-gradient(148deg,#EEDCD1 0%,#D9BCA9 55%,#C9A891 100%)',
    plum:  'linear-gradient(148deg,#E4DBE2 0%,#C9BAC6 55%,#B7A5B4 100%)',
    ash:   'linear-gradient(148deg,#E6E4DF 0%,#CFCBC2 55%,#BDB8AD 100%)',
  }
  return (
    <div className={`ph ${className}`} style={{ aspectRatio: ratio }}>
      {src
        ? <img src={src} alt={alt} loading="lazy" />
        : <div className="ph-fill" style={{ background: tones[tone] }} aria-label={alt} role="img" />}
    </div>
  )
}

const SCRIPT: { role: 'agent' | 'maker'; text: string; wait: number }[] = [
  { role: 'agent', text: 'Is the sourdough back this week, or still on pause?', wait: 1500 },
  { role: 'maker', text: 'Not yet. But we sold out of chili oil by 11. That never happens.', wait: 1900 },
  { role: 'agent', text: 'Sold out by 11. How many jars did you bring?', wait: 1500 },
  { role: 'maker', text: '40. Last month I made 60 and had 20 left, so I thought 40 was safe. Wrong.', wait: 2100 },
  { role: 'agent', text: 'Any idea what changed?', wait: 1300 },
  { role: 'maker', text: "Someone posted a video of me at the July demo. 90,000 views. I don't have TikTok.", wait: 2300 },
  { role: 'maker', text: 'My daughter made me watch it four times. She’s twelve.', wait: 2000 },
]

const HARVEST = [
  { k: 'Person', v: 'Mei, and her twelve-year-old' },
  { k: 'Stake', v: 'Sold out early, out of nowhere' },
  { k: 'Scene', v: 'A queue before setup finished' },
  { k: 'Quote', v: '“I don’t have TikTok.”' },
]

type Blk = { slot: string; head: string; sub?: string; why?: string; own: boolean }

const SAM: Blk[] = [
  { slot: 'Slot 1 · Greeting', head: 'Week of August 12', own: false },
  { slot: 'Slot 2 · Story', head: "She's not famous. She's out of chili oil.", sub: 'Cedar Bakery · Ballard', why: 'Follows Cedar · scanned 3×', own: true },
  { slot: 'Slot 3 · Story', head: "A third of the tomatoes split. Now there's sauce.", sub: 'Hollow Ridge Farm', why: 'Follows Hollow Ridge · scanned 1×', own: true },
  { slot: 'Slot 4 · Sponsor', head: 'Ballard Hardware', own: false },
  { slot: 'Slot 5 · Story', head: 'The neighbors knocked to ask what was burning', sub: 'Cedar Bakery · Ballard', why: 'Follows Cedar · hasn’t seen it', own: true },
  { slot: 'Slot 6 · This week', head: 'Three shops you follow are out on Saturday', own: false },
]

const JO: Blk[] = [
  { slot: 'Slot 1 · Greeting', head: 'Week of August 12', own: false },
  { slot: 'Slot 2 · Story', head: "A third of the tomatoes split. Now there's sauce.", sub: 'Hollow Ridge Farm', why: 'Follows Hollow Ridge · scanned 4×', own: true },
  { slot: 'Slot 3 · Story', head: 'Twelve years of the same Saturday', sub: 'Fiber & Fawn · Ballard', why: 'Nearby · matches what she stops for', own: true },
  { slot: 'Slot 4 · Sponsor', head: 'Ballard Hardware', own: false },
  { slot: 'Slot 5 · Story', head: "She's not famous. She's out of chili oil.", sub: 'Cedar Bakery · new to her', why: 'A shop she hasn’t met yet', own: true },
  { slot: 'Slot 6 · This week', head: 'One shop you follow is out on Saturday', own: false },
]

const TICKER = [
  'She’s not famous. She’s out of chili oil.',
  'A third of the tomatoes split. Now there’s sauce.',
  'Twelve years of the same Saturday',
  'The neighbors knocked to ask what was burning',
  'He named the sourdough starter after his father',
  'Forty jars, and a queue before setup finished',
  'The dog got into the pumpkins again',
]

const ASKS = [
  { q: 'What went wrong this week?', a: 'Usually the best one. Things going wrong is how people find out you’re real.', tone: 'clay' as const },
  { q: 'What surprised you?', a: 'A customer, a delivery, the weather. Something you didn’t see coming.', tone: 'sage' as const },
  { q: 'What do people always ask you about?', a: 'You’ve answered it a hundred times at the counter. Nobody’s written it down.', tone: 'wheat' as const },
]

const STRIP: { tone: 'wheat' | 'sage' | 'clay' | 'plum' | 'ash'; cap: string }[] = [
  { tone: 'wheat', cap: 'Cedar Bakery' },
  { tone: 'sage', cap: 'Hollow Ridge Farm' },
  { tone: 'clay', cap: 'Fiber & Fawn' },
  { tone: 'plum', cap: 'Marigold Flowers' },
  { tone: 'ash', cap: 'Pike Fish Co' },
]

export function Landing() {
  const [dealt, setDealt] = useState(0)
  const [line, setLine] = useState(0)
  const [typing, setTyping] = useState(false)
  const [harvest, setHarvest] = useState(0)
  const dealRef = useRef<HTMLDivElement>(null)
  const chatRef = useRef<HTMLDivElement>(null)

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

  useEffect(() => {
    if (reduced || !dealRef.current) return
    const io = new IntersectionObserver(es => {
      if (es[0].isIntersecting) {
        io.disconnect()
        let n = 0
        const tick = () => { n += 1; setDealt(n); if (n < 12) setTimeout(tick, 190) }
        setTimeout(tick, 260)
      }
    }, { threshold: 0.25 })
    io.observe(dealRef.current)
    return () => io.disconnect()
  }, [reduced])

  useEffect(() => {
    if (reduced || !chatRef.current) return
    const timers: number[] = []
    const io = new IntersectionObserver(es => {
      if (es[0].isIntersecting) {
        io.disconnect()
        let t = 400
        SCRIPT.forEach((s, i) => {
          timers.push(window.setTimeout(() => setTyping(true), t)); t += 520
          timers.push(window.setTimeout(() => { setTyping(false); setLine(i + 1) }, t)); t += s.wait
        })
        HARVEST.forEach((_, i) => timers.push(window.setTimeout(() => setHarvest(i + 1), t + i * 320)))
      }
    }, { threshold: 0.3 })
    io.observe(chatRef.current)
    return () => { io.disconnect(); timers.forEach(clearTimeout) }
  }, [reduced])

  const chat = SCRIPT.slice(0, line)

  return (
    <>
      <style>{`
        :root{
          --paper:#F7F5F0;--paper2:#FFFFFF;--tint:#EFEBE2;
          --ink:#14130F;--ink2:#46433C;--dim:#8B877D;
          --rule:#DCD6C9;--rule2:#C6BEAC;
          --kraft:#8A6A45;--kraftbg:#F0E7D9;--moss:#6E7A55;
        }
        *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
        html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
        body{background:var(--paper);color:var(--ink2);font-family:'Instrument Sans',system-ui,sans-serif;
          font-size:16px;line-height:1.6;overflow-x:hidden;-webkit-font-smoothing:antialiased}
        body::before{content:'';position:fixed;inset:0;z-index:1;pointer-events:none;opacity:.5;
          background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='140' height='140' filter='url(%23n)' opacity='.045'/%3E%3C/svg%3E")}
        a{color:inherit}
        :focus-visible{outline:2px solid var(--kraft);outline-offset:3px}

        .mono{font-family:'IBM Plex Mono',ui-monospace,monospace;font-size:11px;letter-spacing:.18em;text-transform:uppercase}
        .serif{font-family:'Newsreader',Georgia,serif;font-weight:400;color:var(--ink);letter-spacing:-.015em;line-height:1.1}
        .serif em{font-style:italic;color:var(--kraft)}
        .wrap{max-width:1200px;margin:0 auto;padding:0 32px;position:relative;z-index:2}
        .rise{opacity:0;transform:translateY(22px);transition:opacity .8s ease,transform .8s ease}
        .rise.shown{opacity:1;transform:none}

        /* ── photo primitive ── */
        .ph{position:relative;overflow:hidden;border-radius:4px;background:var(--tint);
          border:1px solid var(--rule)}
        .ph img{width:100%;height:100%;object-fit:cover;display:block}
        .ph-fill{width:100%;height:100%;position:relative}
        .ph-fill::after{content:'';position:absolute;inset:0;opacity:.5;
          background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='g'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='120' height='120' filter='url(%23g)' opacity='.1'/%3E%3C/svg%3E")}

        /* ── stat bar ── */
        .statbar{background:var(--ink);color:var(--paper);position:relative;z-index:70}
        .statbar .wrap{display:flex;align-items:center;justify-content:center;gap:10px;
          padding-top:12px;padding-bottom:12px;flex-wrap:wrap;text-align:center}
        .statbar b{color:#fff;font-weight:600;font-size:14px}
        .statbar span{font-size:14px;color:#C3BDB1}
        .statbar a{color:#fff;font-size:14px;text-decoration:none;
          border-bottom:1px solid rgba(255,255,255,.4);padding-bottom:1px;white-space:nowrap;transition:border-color .2s}
        .statbar a:hover{border-color:#fff}

        /* ── nav ── */
        .nav{position:sticky;top:0;z-index:60;display:flex;align-items:center;gap:26px;
          padding:16px 32px;background:rgba(247,245,240,.92);backdrop-filter:blur(12px);
          border-bottom:1px solid var(--rule)}
        .brandmark{font-family:'Newsreader',serif;font-weight:500;font-size:25px;color:var(--ink);
          text-decoration:none;letter-spacing:-.02em}
        .brandsub{border-left:1px solid var(--rule2);padding-left:22px;color:var(--dim)}
        .navspace{flex:1}
        .navlinks{display:flex;gap:26px;align-items:center}
        .navlinks a.mono{color:var(--ink2);text-decoration:none;transition:color .18s}
        .navlinks a.mono:hover{color:var(--kraft)}
        .navcta{background:var(--ink);color:var(--paper)!important;padding:11px 20px;border-radius:100px;
          text-decoration:none;display:inline-flex;align-items:center;gap:8px;transition:background .2s}
        .navcta:hover{background:var(--kraft)}

        /* ── hero ── */
        .hero{padding:66px 0 0}
        .herogrid{display:grid;grid-template-columns:1.04fr .96fr;gap:58px;align-items:center}
        .hero h1{font-size:clamp(33px,3.7vw,50px);margin-bottom:24px}
        .lede{font-size:17px;color:var(--ink2);line-height:1.66;max-width:47ch}
        .lede p+p{margin-top:14px}
        .lede b{color:var(--ink);font-weight:500}
        .routes{display:flex;gap:12px;flex-wrap:wrap;margin-top:32px}
        .route{display:flex;flex-direction:column;gap:3px;text-decoration:none;
          padding:13px 22px;border-radius:8px;transition:transform .2s,background .2s,border-color .2s}
        .route .rk{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.16em;text-transform:uppercase;opacity:.62}
        .route .rt{font-size:15px;font-weight:500}
        .route.dark{background:var(--ink);color:var(--paper)}
        .route.dark:hover{background:var(--kraft);transform:translateY(-2px)}
        .route.light{border:1px solid var(--rule2);color:var(--ink)}
        .route.light:hover{border-color:var(--ink);transform:translateY(-2px)}

        /* ── HERO VISUAL — the interactive stack ── */
        .herovis{position:relative;padding:34px 0 40px;cursor:default;
          perspective:1400px}
        .stackhint{position:absolute;top:-2px;left:50%;transform:translateX(-50%);
          color:var(--dim);opacity:0;transition:opacity .35s ease;pointer-events:none;white-space:nowrap}
        .herovis:hover .stackhint{opacity:1}

        .mini{background:var(--paper2);border:1px solid var(--rule);border-radius:6px;
          box-shadow:0 18px 40px rgba(20,19,15,.10);overflow:hidden;position:relative;z-index:5;
          transform:rotate(-1.4deg);
          transition:transform .55s cubic-bezier(.2,.8,.25,1),box-shadow .55s ease;
          animation:drop .8s cubic-bezier(.2,.7,.3,1) both}
        .herovis:hover .mini{transform:rotate(0deg) translateY(-8px) scale(1.018);
          box-shadow:0 34px 68px rgba(20,19,15,.16)}
        .mini-top{display:flex;align-items:center;justify-content:space-between;padding:13px 17px;
          border-bottom:1px solid var(--rule);background:var(--tint)}
        .mini-top .t{font-family:'Newsreader',serif;font-size:17px;color:var(--ink)}
        .mini-top .mono{color:var(--dim)}
        .mini-body{padding:15px 16px 17px;display:flex;flex-direction:column;gap:8px}
        .mrow{border:1px solid var(--rule);border-radius:4px;padding:11px 13px;
          transition:transform .5s cubic-bezier(.2,.8,.25,1),box-shadow .4s ease,border-color .4s ease}
        .mrow .mono{font-size:9px;color:var(--dim);display:block;margin-bottom:5px}
        .mrow .h{font-family:'Newsreader',serif;font-size:15.5px;color:var(--ink);line-height:1.26;display:block}
        .mrow .v{font-size:11px;color:var(--dim);margin-top:4px;display:block}
        .mrow.k{background:var(--kraftbg);border-color:#E0CFB4}
        .mrow.k .mono{color:var(--kraft)}
        .mrow.n{background:var(--tint)}
        /* the picked rows push forward on hover — the personalisation, made physical */
        .herovis:hover .mrow.k{transform:translateX(9px);
          box-shadow:-4px 5px 16px rgba(138,106,69,.18);border-color:#CFB894}
        .herovis:hover .mrow.k:nth-of-type(3){transition-delay:.06s}

        .peek{position:absolute;background:var(--paper2);border:1px solid var(--rule);border-radius:4px;
          padding:13px 14px;width:196px;box-shadow:0 12px 26px rgba(20,19,15,.09);
          transition:transform .6s cubic-bezier(.2,.8,.25,1),box-shadow .5s ease;
          animation:drop .9s cubic-bezier(.2,.7,.3,1) both}
        .peek .mono{color:var(--kraft);font-size:9px;display:block;margin-bottom:7px}
        .peek .st{font-family:'Newsreader',serif;font-size:14.5px;color:var(--ink);line-height:1.24}
        .p1{top:-16px;right:-18px;transform:rotate(6deg);z-index:3;animation-delay:.2s}
        .p2{bottom:-8px;left:-26px;transform:rotate(-5deg);z-index:4;animation-delay:.34s}
        .p3{top:44%;right:-34px;transform:rotate(-2deg) scale(.94);z-index:2;animation-delay:.46s;opacity:.9}
        .herovis:hover .p1{transform:rotate(9.5deg) translate(26px,-24px);box-shadow:0 22px 40px rgba(20,19,15,.14)}
        .herovis:hover .p2{transform:rotate(-9deg) translate(-30px,18px);box-shadow:0 22px 40px rgba(20,19,15,.14)}
        .herovis:hover .p3{transform:rotate(2deg) translate(44px,10px) scale(.98);opacity:1}
        @keyframes drop{from{opacity:0;transform:translateY(-20px)}}
        @media(max-width:1080px){.peek{display:none}.stackhint{display:none}}

        /* ── photo strip ── */
        .pstrip{border-top:1px solid var(--rule);background:var(--tint);position:relative;z-index:2;
          padding:34px 0 38px;overflow:hidden}
        .pstrip .lab{display:flex;align-items:center;gap:16px;margin-bottom:22px}
        .pstrip .lab .mono{color:var(--kraft)}
        .pstrip .lab i{flex:1;height:1px;background:var(--rule2)}
        .prow{display:grid;grid-template-columns:repeat(5,1fr);gap:14px}
        .pcell{position:relative;transition:transform .4s cubic-bezier(.2,.8,.25,1)}
        .pcell:hover{transform:translateY(-6px)}
        .pcell .cap{margin-top:9px;font-size:12px;color:var(--dim);
          font-family:'IBM Plex Mono',monospace;letter-spacing:.1em;text-transform:uppercase}
        .pcell:nth-child(2){margin-top:20px}
        .pcell:nth-child(4){margin-top:20px}

        /* ── reassurance ── */
        .reassure{border-top:1px solid var(--rule);background:var(--paper);position:relative;z-index:2}
        .rgrid{display:grid;grid-template-columns:repeat(5,1fr)}
        .rcell{padding:30px 26px 32px;border-right:1px solid var(--rule)}
        .rcell:last-child{border-right:0}
        .rcell h4{font-family:'Newsreader',serif;font-weight:500;font-size:18px;color:var(--ink);
          margin-bottom:9px;line-height:1.22}
        .rcell p{font-size:13.5px;color:var(--ink2);line-height:1.58}

        /* ── dark claim ── */
        .claim{background:var(--ink);color:var(--paper);position:relative;z-index:2}
        .claim .wrap{padding-top:54px;padding-bottom:54px;display:grid;
          grid-template-columns:1.15fr 1fr;gap:52px;align-items:center}
        .claim .mono{color:var(--kraft);display:block;margin-bottom:16px}
        .claim h2{font-family:'Newsreader',serif;font-size:clamp(26px,3.2vw,40px);
          color:#fff;line-height:1.16;letter-spacing:-.015em}
        .claim h2 em{font-style:italic;color:var(--kraft)}
        .claim p{color:#C9C3B7;font-size:15.5px;line-height:1.68}
        .claim p+p{margin-top:14px}

        /* ── ticker ── */
        .ticker{border-bottom:1px solid var(--rule);padding:15px 0;overflow:hidden;
          background:var(--tint);position:relative;z-index:2}
        .ticker-track{display:flex;width:max-content;animation:slide 46s linear infinite}
        .ticker:hover .ticker-track{animation-play-state:paused}
        @keyframes slide{to{transform:translateX(-50%)}}
        .tick{font-family:'Newsreader',serif;font-size:19px;color:var(--ink);padding:0 30px;
          white-space:nowrap;display:flex;align-items:center;gap:30px}
        .tick::after{content:'';width:5px;height:5px;border-radius:50%;background:var(--kraft);flex-shrink:0}

        /* ── sections ── */
        .sec{padding:90px 0;border-top:1px solid var(--rule);position:relative;z-index:2}
        .sechead{display:flex;align-items:center;gap:18px;margin-bottom:36px;flex-wrap:wrap}
        .sechead .mono{color:var(--dim)}
        .sechead .mono.k{color:var(--kraft)}
        .sechead i{flex:1;height:1px;background:var(--rule);min-width:20px}
        .sec h2{font-size:clamp(29px,4.2vw,46px);max-width:20ch;margin-bottom:20px}
        .note{color:var(--ink2);max-width:60ch;font-size:16.5px}

        .vs{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:34px}
        .vscard{border:1px solid var(--rule);border-radius:4px;padding:28px 26px 30px;background:var(--paper2)}
        .vscard.ours{background:var(--kraftbg);border-color:#E0CFB4}
        .vscard .mono{color:var(--dim);display:block;margin-bottom:15px}
        .vscard.ours .mono{color:var(--kraft)}
        .vscard h3{font-family:'Newsreader',serif;font-weight:500;font-size:21px;color:var(--ink);margin-bottom:14px}
        .vslist{list-style:none;display:flex;flex-direction:column;gap:11px}
        .vslist li{font-size:14.5px;color:var(--ink2);display:flex;gap:11px;align-items:baseline}
        .vslist li::before{content:'';width:5px;height:5px;border-radius:50%;background:var(--rule2);flex-shrink:0;transform:translateY(-2px)}
        .vscard.ours .vslist li::before{background:var(--kraft)}

        .asks{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin-top:34px}
        .ask{border:1px solid var(--rule);border-radius:4px;overflow:hidden;background:var(--paper2);
          transition:transform .35s cubic-bezier(.2,.8,.25,1),box-shadow .35s}
        .ask:hover{transform:translateY(-5px);box-shadow:0 16px 34px rgba(20,19,15,.09)}
        .ask .ph{border:0;border-radius:0;border-bottom:1px solid var(--rule)}
        .ask .inner{padding:22px 24px 26px}
        .ask .mono{color:var(--kraft);display:block;margin-bottom:12px}
        .ask h3{font-family:'Newsreader',serif;font-weight:500;font-size:20px;color:var(--ink);
          margin-bottom:10px;line-height:1.24}
        .ask p{font-size:14px;color:var(--ink2);line-height:1.6}

        .split{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:38px}
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
        .blk.pers{background:var(--kraftbg);border-color:#E0CFB4}
        .blk.pers .mono{color:var(--kraft)}
        .blk.pers:hover{box-shadow:0 6px 18px rgba(20,19,15,.09)}
        .why{position:absolute;left:12px;right:12px;bottom:calc(100% + 7px);background:var(--ink);
          color:var(--paper);padding:8px 11px;border-radius:4px;font-size:11.5px;line-height:1.4;
          opacity:0;transform:translateY(5px);transition:opacity .2s,transform .2s;pointer-events:none;z-index:5}
        .why::after{content:'';position:absolute;top:100%;left:22px;border:5px solid transparent;border-top-color:var(--ink)}
        .blk.pers:hover .why{opacity:1;transform:none}
        .legend{display:flex;gap:26px;flex-wrap:wrap;margin-top:24px;align-items:center}
        .legend div{display:flex;align-items:center;gap:9px;font-size:13px;color:var(--ink2)}
        .sw{width:12px;height:12px;border-radius:2px;border:1px solid var(--rule2)}
        .sw.k{background:var(--kraftbg);border-color:#E0CFB4}
        .sw.n{background:var(--tint)}
        .mockmark{margin-top:16px;color:var(--dim);font-size:12.5px;font-style:italic}

        .demo{display:grid;grid-template-columns:1.1fr .85fr;gap:24px;margin-top:36px}
        .chatbox{background:var(--paper2);border:1px solid var(--rule);border-radius:4px;padding:20px;
          min-height:400px;display:flex;flex-direction:column;gap:11px}
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
        .dots i:nth-child(2){animation-delay:.16s}.dots i:nth-child(3){animation-delay:.32s}
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
        .harvest .foot{margin-top:16px;padding-top:14px;border-top:1px solid var(--rule);font-size:12.5px;color:var(--dim)}

        .bounds{display:grid;grid-template-columns:repeat(3,1fr);gap:26px}
        .bound{border-top:2px solid var(--kraft);padding-top:20px;transition:transform .3s}
        .bound:hover{transform:translateY(-4px)}
        .bound p{font-family:'Newsreader',serif;font-size:21px;color:var(--ink);line-height:1.28;margin-bottom:12px}
        .bound span{font-size:14.5px;color:var(--ink2)}

        .cols{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:34px}
        .card{background:var(--paper2);border:1px solid var(--rule);border-radius:4px;
          padding:32px 30px 34px;transition:transform .3s,box-shadow .3s}
        .card:hover{transform:translateY(-4px);box-shadow:0 14px 32px rgba(20,19,15,.07)}
        .card .mono{color:var(--kraft);display:block;margin-bottom:17px}
        .card h3{font-family:'Newsreader',serif;font-weight:500;font-size:23px;color:var(--ink);margin-bottom:12px;line-height:1.2}
        .card p{font-size:15px;color:var(--ink2);margin-bottom:18px}
        .facts{list-style:none;display:flex;flex-direction:column;gap:10px}
        .facts li{display:flex;gap:12px;font-size:14.5px;color:var(--ink);align-items:baseline}
        .facts li::before{content:'';width:5px;height:5px;border-radius:50%;background:var(--kraft);flex-shrink:0;transform:translateY(-2px)}

        /* ── vision, with photos ── */
        .vision{background:var(--ink);color:var(--paper);position:relative;z-index:2;overflow:hidden}
        .vision .wrap{padding-top:82px;padding-bottom:86px}
        .visgrid{display:grid;grid-template-columns:.86fr 1.14fr;gap:56px;align-items:center}
        .vision .mono{color:var(--kraft);display:block;margin-bottom:20px}
        .vision h2{font-family:'Newsreader',serif;font-size:clamp(27px,3.5vw,42px);color:#fff;
          line-height:1.2;letter-spacing:-.015em;margin-bottom:22px}
        .vision h2 em{font-style:italic;color:var(--kraft)}
        .vision p{color:#C9C3B7;font-size:16px;line-height:1.7}
        .vision p+p{margin-top:14px}
        .vispair{display:grid;grid-template-columns:1fr 1fr;gap:16px}
        .vispair .ph{border-color:rgba(255,255,255,.14)}
        .vispair .ph:first-child{margin-top:34px}

        .close{padding:92px 0 104px;border-top:1px solid var(--rule);text-align:center;position:relative;z-index:2}
        .close h2{font-size:clamp(29px,4vw,44px);max-width:22ch;margin:0 auto 22px}
        .close p{color:var(--ink2);max-width:52ch;margin:0 auto 30px;font-size:16.5px}
        .close .routes{justify-content:center}

        footer{border-top:1px solid var(--rule);padding:32px 32px 48px;position:relative;z-index:2}
        .foot{max-width:1200px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap}
        .footlinks{display:flex;gap:24px;flex-wrap:wrap}
        .footlinks a{text-decoration:none;color:var(--dim);transition:color .18s}
        .footlinks a:hover{color:var(--ink)}
        .foot .mono{color:var(--dim)}

        @media(max-width:1100px){
          .rgrid{grid-template-columns:repeat(3,1fr)}
          .rcell:nth-child(3){border-right:0}
          .rcell:nth-child(1),.rcell:nth-child(2),.rcell:nth-child(3){border-bottom:1px solid var(--rule)}
          .prow{grid-template-columns:repeat(3,1fr)}
          .pcell:nth-child(4),.pcell:nth-child(5){display:none}
        }
        @media(max-width:1000px){
          .herogrid{grid-template-columns:1fr;gap:44px}
          .claim .wrap,.visgrid{grid-template-columns:1fr;gap:32px}
        }
        @media(max-width:940px){
          .split,.vs,.cols,.demo,.asks,.bounds{grid-template-columns:1fr}
          .inbox-body{min-height:0}
        }
        @media(max-width:680px){
          .rgrid{grid-template-columns:1fr}
          .rcell{border-right:0;border-bottom:1px solid var(--rule)}
          .rcell:last-child{border-bottom:0}
          .prow{grid-template-columns:repeat(2,1fr)}
          .pcell:nth-child(3){display:none}
        }
        @media(max-width:620px){
          .navlinks a.mono:not(.navcta){display:none}
          .brandsub{display:none}
          .statbar span{display:none}
          .sec{padding:64px 0}
          .tick{font-size:16px;padding:0 20px}
          .routes{flex-direction:column}
          .route{width:100%}
        }
        @media(prefers-reduced-motion:reduce){
          *{animation:none!important;transition:none!important}
          .blk,.hrow{opacity:1;transform:none}
        }
      `}</style>

      <div className="statbar">
        <div className="wrap">
          <b>Local roundup newsletters are opened 30 to 55% of the time.</b>
          <span>People who ignore brand email still read the one about their neighborhood.</span>
          <a href="/why-local">Where these numbers come from ↗</a>
        </div>
      </div>

      <nav className="nav">
        <a className="brandmark" href="/">Marlo</a>
        <span className="mono brandsub">The system behind Brown Bag</span>
        <span className="navspace" />
        <div className="navlinks">
          <a className="mono" href="#different">Not a swap</a>
          <a className="mono" href="#asks">What we ask</a>
          <a className="mono" href="#limits">Limits</a>
          <a className="mono" href="#partners">Partners</a>
          <a className="mono navcta" href="mailto:hello@marlo021.ai">Get in touch →</a>
        </div>
      </nav>

      {/* ── HERO ── */}
      <header className="hero">
        <div className="wrap">
          <div className="herogrid">
            <div>
              <h1 className="serif">
                Some of your best customers will never join your mailing list.<br />
                <em>They'll read this one.</em>
              </h1>
              <div className="lede">
                <p>Brown Bag is a weekly newsletter about the shops and makers in one neighborhood.</p>
                <p>
                  Once a week we ask what's been going on. You can talk it through in a chat, or write
                  it up yourself if that's easier. We turn it into a short story. <b>You read it before
                  anyone else does.</b> Then it goes out to people who follow you here.
                </p>
              </div>
              <div className="routes">
                <a className="route dark" href="mailto:hello@marlo021.ai?subject=Joining Brown Bag">
                  <span className="rk">I sell things locally</span>
                  <span className="rt">Join the first issue →</span>
                </a>
                <a className="route light" href="#partners">
                  <span className="rk">I run a market or platform</span>
                  <span className="rt">Talk to us →</span>
                </a>
              </div>
            </div>

            <div className="herovis">
              <span className="mono stackhint">One issue · built for one reader</span>

              <div className="peek p1">
                <span className="mono">Fiber &amp; Fawn</span>
                <div className="st">Twelve years of the same Saturday</div>
              </div>
              <div className="peek p2">
                <span className="mono">Pike Fish Co</span>
                <div className="st">The neighbors knocked to ask what was burning</div>
              </div>
              <div className="peek p3">
                <span className="mono">Marigold Flowers</span>
                <div className="st">The dog got into the pumpkins again</div>
              </div>

              <div className="mini">
                <div className="mini-top">
                  <span className="t">Brown Bag</span>
                  <span className="mono">No. 06</span>
                </div>
                <div className="mini-body">
                  <div className="mrow n">
                    <span className="mono">Everyone</span>
                    <span className="h">Week of August 12</span>
                  </div>
                  <div className="mrow k">
                    <span className="mono">Picked for this reader</span>
                    <span className="h">She's not famous. She's out of chili oil.</span>
                    <span className="v">Cedar Bakery · Ballard</span>
                  </div>
                  <div className="mrow k">
                    <span className="mono">Picked for this reader</span>
                    <span className="h">A third of the tomatoes split. Now there's sauce.</span>
                    <span className="v">Hollow Ridge Farm · Ballard</span>
                  </div>
                  <div className="mrow n">
                    <span className="mono">Everyone</span>
                    <span className="h">Ballard Hardware</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* ── PHOTO STRIP ── */}
      <section className="pstrip">
        <div className="wrap">
          <div className="lab">
            <span className="mono">In the first issue</span><i />
            <span className="mono" style={{ color: 'var(--dim)' }}>Ballard, Seattle</span>
          </div>
          <div className="prow">
            {STRIP.map((s, i) => (
              <div className="pcell" key={i}>
                {/* src="/photos/strip-1.jpg" */}
                <Photo alt={s.cap} tone={s.tone} ratio="4 / 3" />
                <div className="cap">{s.cap}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── REASSURANCE ── */}
      <section className="reassure">
        <div className="rgrid">
          <div className="rcell">
            <h4>It's a different appetite</h4>
            <p>Lots of people love your brand and will never sign up for your newsletter.
              One email about the whole neighborhood? That they'll take.</p>
          </div>
          <div className="rcell">
            <h4>Your list stays yours</h4>
            <p>We don't see it. We don't import it. We don't email it.</p>
          </div>
          <div className="rcell">
            <h4>Talk it out or write it up</h4>
            <p>Whichever suits you. If you've got someone who writes well, even better.</p>
          </div>
          <div className="rcell">
            <h4>Nothing goes out unread</h4>
            <p>You see every story first. If something's wrong, you say so and we fix it.</p>
          </div>
          <div className="rcell">
            <h4>Free, and staying free</h4>
            <p>For you and for the people reading.</p>
          </div>
        </div>
      </section>

      {/* ── DARK CLAIM ── */}
      <section className="claim">
        <div className="wrap">
          <div>
            <span className="mono">The whole idea</span>
            <h2>One issue goes out.<br /><em>No two people get the same email.</em></h2>
          </div>
          <div>
            <p>Every story is written once. Then it's matched, reader by reader, against the shops
              they actually visit. Plus one they haven't met yet.</p>
            <p>Nobody picks a topic. Nobody fills in a form. They scan a code at a counter and the
              rest is worked out quietly from there.</p>
          </div>
        </div>
      </section>

      <div className="ticker">
        <div className="ticker-track">
          {[...TICKER, ...TICKER].map((t, i) => <span className="tick" key={i}>{t}</span>)}
        </div>
      </div>

      {/* ── NOT A SWAP ── */}
      <section className="sec rise" id="different">
        <div className="wrap">
          <div className="sechead">
            <span className="mono k">The question everyone asks</span>
            <span className="mono">Doesn't this compete with my own list?</span><i />
          </div>
          <h2 className="serif">It's a different job, and a different reader.</h2>
          <p className="note">
            Your newsletter is for people who already decided they want to hear from you.
            Brown Bag is for the ones who like you fine and are never going to make that decision.
          </p>
          <div className="vs">
            <div className="vscard">
              <span className="mono">Your newsletter</span>
              <h3>People who already said yes</h3>
              <ul className="vslist">
                <li>They chose you specifically</li>
                <li>You set the schedule and the message</li>
                <li>Sales, launches, anything you want</li>
                <li>Your list, your data, your rules</li>
              </ul>
            </div>
            <div className="vscard ours">
              <span className="mono">Brown Bag</span>
              <h3>People who'd never sign up for one shop</h3>
              <ul className="vslist">
                <li>They subscribed to a neighborhood, not a brand</li>
                <li>One email, once a week, several shops in it</li>
                <li>Stories only. Nothing to buy in there</li>
                <li>We never see or touch your list</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── WHAT WE ASK ── */}
      <section className="sec rise" id="asks">
        <div className="wrap">
          <div className="sechead">
            <span className="mono k">The part people worry about</span>
            <span className="mono">What would I even say?</span><i />
          </div>
          <h2 className="serif">We ask about the week, not about the product.</h2>
          <p className="note">
            Nobody has to come up with an idea. We ask, you answer, and it's usually more
            interesting than you think. Three of the questions we actually use:
          </p>
          <div className="asks">
            {ASKS.map((a, i) => (
              <div className="ask" key={i}>
                {/* src={`/photos/ask-${i + 1}.jpg`} */}
                <Photo alt="" tone={a.tone} ratio="16 / 9" />
                <div className="inner">
                  <span className="mono">Question {i + 1}</span>
                  <h3>{a.q}</h3>
                  <p>{a.a}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TWO INBOXES ── */}
      <section className="sec rise" ref={dealRef}>
        <div className="wrap">
          <div className="sechead">
            <span className="mono k">Fig. 01</span>
            <span className="mono">One issue · Two readers</span><i />
          </div>
          <h2 className="serif">The same week. Two different emails.</h2>
          <p className="note">
            Sam scans the bakery's code most Saturdays. Jo scans the farm's. They both get
            Brown Bag No. 6, and what's inside is not the same.
            <br /><span style={{ color: 'var(--dim)', fontSize: 14 }}>Hover a highlighted block to see why it was picked.</span>
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
                    <div key={i} className={`blk ${b.own ? 'pers' : 'same'} ${dealt > i * 2 + box.off ? 'in' : ''}`}>
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
            <div><span className="sw k" /> Picked for this reader</div>
            <div><span className="sw n" /> Same for everyone</div>
          </div>
          <p className="mockmark">Illustration. Real issues keep the same shape and stay under 1,000 words.</p>
        </div>
      </section>

      {/* ── INTERVIEW ── */}
      <section className="sec rise" id="interview" ref={chatRef}>
        <div className="wrap">
          <div className="sechead">
            <span className="mono k">Fig. 02</span>
            <span className="mono">What a conversation looks like</span><i />
          </div>
          <h2 className="serif">It remembers what you told it last time.</h2>
          <p className="note">
            That's the difference between a form and a conversation. "Anything new?" gets nothing.
            "Is the sourdough back?" gets a story.
          </p>
          <div className="demo">
            <div className="chatbox">
              <div className="hd">
                <span className="mono">Cedar Bakery · Tuesday</span>
                <span className="mono live"><i />Live</span>
              </div>
              {chat.map((m, i) => <div className={`bub ${m.role}`} key={i}>{m.text}</div>)}
              {typing && <div className="dots"><i /><i /><i /></div>}
            </div>
            <div className="harvest">
              <span className="mono">What we kept</span>
              {HARVEST.map((h, i) => (
                <div className={`hrow ${harvest > i ? 'in' : ''}`} key={i}>
                  <span className="k">{h.k}</span>
                  <span className="v">{h.v}</span>
                </div>
              ))}
              <p className="foot">
                We keep your words exactly as you said them. Nothing published can say more
                than you did here.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── LIMITS ── */}
      <section className="sec rise" id="limits">
        <div className="wrap">
          <div className="sechead">
            <span className="mono k">Fig. 03</span>
            <span className="mono">What the system will not do</span><i />
          </div>
          <h2 className="serif">The rules matter more than the features.</h2>
          <p className="note" style={{ marginBottom: 38 }}>
            Three things are fixed. They're why a business can hand us a story and a reader
            keeps opening the email.
          </p>
          <div className="bounds">
            <div className="bound">
              <p>Nothing is published without a person reading it first.</p>
              <span>Every story, every sponsor, every line. An editor approves it or it doesn't run.
                There is no automatic path to a reader's inbox.</span>
            </div>
            <div className="bound">
              <p>We never write a fact you didn't tell us.</p>
              <span>Your words are kept exactly as you said them. Every published sentence traces
                back to one of them, and you can correct it at any point.</span>
            </div>
            <div className="bound">
              <p>We never tell a reader what we've worked out about them.</p>
              <span>Brown Bag says the cheese shop is back this week. It never says "because you
                keep buying bread." The matching is invisible, and it stays that way.</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── PARTNERS ── */}
      <section className="sec rise" id="partners">
        <div className="wrap">
          <div className="sechead">
            <span className="mono k">Fig. 04</span>
            <span className="mono">Working with Marlo</span><i />
          </div>
          <h2 className="serif">One neighborhood at a time, on purpose.</h2>
          <div className="cols">
            <div className="card">
              <span className="mono">For markets and platforms</span>
              <h3>Bring your businesses, keep your relationship</h3>
              <p>You get one code to hand out. Businesses sign themselves up with it and are live
                the same day. No account setup on your side, and no data to hand over.</p>
              <ul className="facts">
                <li>They join with a code, not an approval queue</li>
                <li>Nobody sees anyone else's subscriber list</li>
                <li>Consent recorded at signup, unsubscribe is one click</li>
                <li>Every issue reports what ran and who opened it</li>
              </ul>
            </div>
            <div className="card">
              <span className="mono">For technical partners</span>
              <h3>The parts that could be an API</h3>
              <p>Marlo is built as separate stages, so any one of them can stand alone. Nothing is
                public yet. This is what we'd open first if there's a reason to.</p>
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

      {/* ── VISION ── */}
      <section className="vision">
        <div className="wrap">
          <div className="visgrid">
            <div>
              <span className="mono">Why we're doing this</span>
              <h2>Somebody made the thing you bought this week.<br />
                <em>You'll probably never know who.</em></h2>
              <p>
                Buying used to come with a person attached. You knew who baked it, who grew it,
                who stayed up late finishing it. Most of that has quietly gone.
              </p>
              <p>
                We think it can come back, and that it doesn't take much. One story a week, from
                someone a few streets away, told in their own words. That's the whole bet.
              </p>
            </div>
            <div className="vispair">
              {/* src="/photos/hero-a.jpg" */}
              <Photo alt="Hands at work" tone="clay" ratio="3 / 4" />
              {/* src="/photos/hero-b.jpg" */}
              <Photo alt="A stall on a Saturday" tone="sage" ratio="3 / 4" />
            </div>
          </div>
        </div>
      </section>

      {/* ── CLOSE ── */}
      <section className="close rise">
        <div className="wrap">
          <h2 className="serif">If you sell something near people, we'd like to hear from you.</h2>
          <p>Brown Bag is starting in Seattle. We're looking for businesses who have something
            to say and nowhere good to say it.</p>
          <div className="routes">
            <a className="route dark" href="mailto:hello@marlo021.ai?subject=Joining Brown Bag">
              <span className="rk">I sell things locally</span>
              <span className="rt">Join the first issue →</span>
            </a>
            <a className="route light" href="mailto:hello@marlo021.ai?subject=Market or platform">
              <span className="rk">I run a market or platform</span>
              <span className="rt">Start a conversation →</span>
            </a>
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