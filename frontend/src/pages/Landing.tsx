import { useEffect, useRef, useState } from 'react'

/*  ──────────────────────────────────────────────────────────────
    PHOTOS  →  frontend/public/photos/

    DONE:  strip-1..3   ask-1..3

    STILL NEEDED — the two in the dark "Why we're doing this" section.
    They sit side by side against near-black, so they need to hold up
    at small size and read instantly.

    ── hero-a.jpg ── portrait 3:4, sits LOWER in the pair
       A pair of hands mid-task. Kneading, wrapping, tying string,
       weighing something out, counting change.

       Crop tight. Hands and the thing being made should fill most of
       the frame. A face is fine but not the point.

       This one carries "somebody made this." It should look like work,
       not like a product shot.

    ── hero-b.jpg ── portrait 3:4, sits HIGHER in the pair
       A stall or counter from where a customer would stand.
       Mid-morning, people around, slightly busy.

       Wider than hero-a on purpose. The two shouldn't be the same
       distance from the subject, or they read as a matched pair
       instead of two moments.

       This one carries "and they're a few streets away."

    ── For both ──
       Natural light. No flash.
       Slightly imperfect beats polished. Blur, a stray hand, a
       cluttered table are all fine and usually better.
       Warm tones sit best against the dark background.
       Avoid: posed smiles at the camera, styled flat-lays,
       anything that could pass for stock.

    KEEP EVERY FILE UNDER ~400KB. Around 1200px on the long edge is
    plenty for these two.

    To add: drop the file in, then set src="/photos/hero-a.jpg" on
    the matching <Photo> in the vision section.

    TYPOGRAPHY NOTE
    Plus Jakarta Sans is the site's voice: friendly, modern, round.
    Newsreader (serif) appears ONLY inside mocked Brown Bag content —
    the email preview and the story cards. That separation is
    deliberate: the newsletter has its own typography, and this site
    is not the newsletter.
   ────────────────────────────────────────────────────────────── */

type Tone = 'amber' | 'leaf' | 'coral' | 'sky' | 'plum'

function Photo({
  src, alt, tone = 'amber', ratio = '4 / 3', className = '',
}: { src?: string; alt: string; tone?: Tone; ratio?: string; className?: string }) {
  const tones: Record<Tone, string> = {
    amber: 'linear-gradient(148deg,#F6E2BE 0%,#E8C48A 100%)',
    leaf:  'linear-gradient(148deg,#DDE9D6 0%,#B3CDA9 100%)',
    coral: 'linear-gradient(148deg,#F8DCD5 0%,#EDB3A6 100%)',
    sky:   'linear-gradient(148deg,#D9E5EE 0%,#A9C4D8 100%)',
    plum:  'linear-gradient(148deg,#E7DCE9 0%,#C2A9CB 100%)',
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

type Blk = { slot: string; head: string; sub?: string; why?: string; own: boolean; tone?: Tone }

const SAM: Blk[] = [
  { slot: 'Everyone', head: 'Week of August 12', own: false },
  { slot: 'Picked for Sam', head: "She's not famous. She's out of chili oil.", sub: 'Cedar Bakery · Ballard', why: 'Follows Cedar · scanned 3×', own: true, tone: 'amber' },
  { slot: 'Picked for Sam', head: "A third of the tomatoes split. Now there's sauce.", sub: 'Hollow Ridge Farm', why: 'Follows Hollow Ridge · scanned 1×', own: true, tone: 'leaf' },
  { slot: 'Everyone', head: 'Ballard Hardware', own: false },
  { slot: 'Picked for Sam', head: 'The neighbors knocked to ask what was burning', sub: 'Cedar Bakery · Ballard', why: 'Follows Cedar · hasn’t seen it', own: true, tone: 'amber' },
  { slot: 'Everyone', head: 'Three shops you follow are out on Saturday', own: false },
]

const JO: Blk[] = [
  { slot: 'Everyone', head: 'Week of August 12', own: false },
  { slot: 'Picked for Jo', head: "A third of the tomatoes split. Now there's sauce.", sub: 'Hollow Ridge Farm', why: 'Follows Hollow Ridge · scanned 4×', own: true, tone: 'leaf' },
  { slot: 'Picked for Jo', head: 'Twelve years of the same Saturday', sub: 'Fiber & Fawn · Ballard', why: 'Nearby · matches what she stops for', own: true, tone: 'plum' },
  { slot: 'Everyone', head: 'Ballard Hardware', own: false },
  { slot: 'Picked for Jo', head: "She's not famous. She's out of chili oil.", sub: 'Cedar Bakery · new to her', why: 'A shop she hasn’t met yet', own: true, tone: 'amber' },
  { slot: 'Everyone', head: 'One shop you follow is out on Saturday', own: false },
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

const ASKS: { q: string; a: string; tone: Tone; src: string }[] = [
  { q: 'What went wrong this week?', a: 'Usually the best one. Things going wrong is how people find out you’re real.', tone: 'coral', src: '/photos/ask-1.jpg' },
  { q: 'What surprised you?', a: 'A customer, a delivery, the weather. Something you didn’t see coming.', tone: 'leaf', src: '/photos/ask-2.jpg' },
  { q: 'What do people always ask you about?', a: 'You’ve answered it a hundred times at the counter. Nobody’s written it down.', tone: 'amber', src: '/photos/ask-3.jpg' },
]

const STRIP: { src?: string; tone: Tone; cap: string }[] = [
  { src: '/photos/strip-1.jpg', tone: 'sky', cap: 'Pike Place' },
  { src: '/photos/strip-2.jpg', tone: 'coral', cap: 'Flower row' },
  { src: '/photos/strip-3.jpg', tone: 'plum', cap: 'Market Center' },
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
    f.href = 'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,500&family=Newsreader:ital,opsz,wght@0,6..72,400..600;1,6..72,400..500&display=swap'
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
          --paper:#FAF4ED;--white:#FFFFFF;--tint:#F3EBE0;
          --ink:#171512;--ink2:#4A463F;--dim:#8E8A80;
          --rule:#E3DED3;--rule2:#CDC6B7;

          /* vendor colours — drawn from what people actually sell */
          --amber:#D99A3C;  --amber-bg:#FBF0DC;  --amber-br:#EFD5A8;
          --leaf:#5E9464;   --leaf-bg:#E7F0E4;   --leaf-br:#C2DAB9;
          --coral:#DB7663;  --coral-bg:#FBE7E1;  --coral-br:#F0C4B6;
          --sky:#5B8CB0;    --sky-bg:#E3EDF4;    --sky-br:#B9D2E2;
          --plum:#96699F;   --plum-bg:#F0E7F2;   --plum-br:#D8C2DD;

          --brand:#C4622E;  /* the one loud accent */
          --brand-hi:#DB7639;
        }
        *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
        html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
        body{background:var(--paper);color:var(--ink2);
          font-family:'Plus Jakarta Sans',system-ui,sans-serif;
          font-size:16px;line-height:1.6;overflow-x:hidden;-webkit-font-smoothing:antialiased}
        a{color:inherit}
        :focus-visible{outline:2px solid var(--brand);outline-offset:3px;border-radius:6px}

        .mono{font-family:'Plus Jakarta Sans',sans-serif;font-size:11px;font-weight:700;
          letter-spacing:.14em;text-transform:uppercase}
        /* Newsreader is reserved for Brown Bag's own content */
        .bb{font-family:'Newsreader',Georgia,serif}
        h1,h2,h3,h4{font-family:'Plus Jakarta Sans',sans-serif;color:var(--ink);
          letter-spacing:-.028em;line-height:1.1;font-weight:800}
        .wrap{max-width:1200px;margin:0 auto;padding:0 32px;position:relative;z-index:2}
        .rise{opacity:0;transform:translateY(22px);transition:opacity .8s ease,transform .8s ease}
        .rise.shown{opacity:1;transform:none}

        .ph{position:relative;overflow:hidden;border-radius:16px;background:var(--tint)}
        .ph img{width:100%;height:100%;object-fit:cover;display:block}
        .ph-fill{width:100%;height:100%}

        /* ── stat bar ── */
        .statbar{background:var(--ink);color:#fff;position:relative;z-index:70}
        .statbar .wrap{display:flex;align-items:center;justify-content:center;gap:10px;
          padding-top:13px;padding-bottom:13px;flex-wrap:wrap;text-align:center}
        .statbar b{font-weight:700;font-size:14px}
        .statbar span{font-size:14px;color:#B8B2A6}
        .statbar a{color:#fff;font-size:14px;font-weight:600;text-decoration:none;
          border-bottom:1.5px solid rgba(255,255,255,.45);padding-bottom:1px;white-space:nowrap;
          transition:border-color .2s}
        .statbar a:hover{border-color:#fff}

        /* ── nav ── */
        .nav{position:sticky;top:0;z-index:60;display:flex;align-items:center;gap:26px;
          padding:15px 32px;background:var(--white);
          border-bottom:1px solid var(--rule)}
        .brandmark{font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:23px;
          color:var(--ink);text-decoration:none;letter-spacing:-.04em}
        .brandsub{border-left:1px solid var(--rule2);padding-left:20px;color:var(--dim);font-weight:600}
        .navspace{flex:1}
        .navlinks{display:flex;gap:24px;align-items:center}
        .navlinks a.mono{color:var(--ink2);text-decoration:none;transition:color .18s}
        .navlinks a.mono:hover{color:var(--brand)}
        .navcta{background:var(--brand);color:#fff!important;padding:12px 22px;border-radius:100px;
          text-decoration:none;display:inline-flex;align-items:center;gap:8px;
          transition:background .2s,transform .2s;box-shadow:0 4px 14px rgba(196,98,46,.28)}
        .navcta:hover{background:var(--brand-hi);transform:translateY(-1px)}

        /* ── hero ── */
        .hero{padding:74px 0 88px;background:var(--paper);position:relative;overflow:hidden}
        /* soft colour washes behind the hero, so it isn't a flat white box */
        .hero::before{content:'';position:absolute;width:640px;height:640px;right:-170px;top:-230px;
          background:radial-gradient(circle,rgba(217,154,60,.20) 0%,transparent 66%);pointer-events:none}
        .hero::after{content:'';position:absolute;width:540px;height:540px;left:-210px;bottom:-250px;
          background:radial-gradient(circle,rgba(94,148,100,.16) 0%,transparent 66%);pointer-events:none}
        .herogrid{display:grid;grid-template-columns:1.02fr .98fr;gap:56px;align-items:center}
        .hero h1{font-size:clamp(34px,3.9vw,53px);margin-bottom:24px}
        .hero h1 span{color:var(--brand)}
        .lede{font-size:17px;color:var(--ink2);line-height:1.68;max-width:47ch}
        .lede p+p{margin-top:14px}
        .lede b{color:var(--ink);font-weight:700}

        .routes{display:flex;gap:12px;flex-wrap:wrap;margin-top:34px}
        .route{display:flex;flex-direction:column;gap:2px;text-decoration:none;
          padding:14px 26px;border-radius:100px;transition:transform .2s,background .2s,border-color .2s,box-shadow .2s}
        .route .rk{font-size:10.5px;font-weight:700;letter-spacing:.13em;text-transform:uppercase;opacity:.72}
        .route .rt{font-size:15.5px;font-weight:700}
        .route.dark{background:var(--brand);color:#fff;box-shadow:0 6px 20px rgba(196,98,46,.3)}
        .route.dark:hover{background:var(--brand-hi);transform:translateY(-3px);box-shadow:0 12px 28px rgba(196,98,46,.36)}
        .route.light{border:2px solid var(--rule2);color:var(--ink)}
        .route.light:hover{border-color:var(--ink);transform:translateY(-3px)}

        /* ── hero visual ── */
        .herovis{position:relative;padding:38px 0 44px;perspective:1400px}
        .stackhint{position:absolute;top:4px;left:50%;transform:translateX(-50%);color:var(--dim);
          opacity:0;transition:opacity .35s ease;pointer-events:none;white-space:nowrap}
        .herovis:hover .stackhint{opacity:1}

        /* floating shapes — pure decoration, keeps it from feeling assembled */
        .blob{position:absolute;border-radius:50%;pointer-events:none;z-index:1;
          animation:float 7s ease-in-out infinite}
        .b1{width:22px;height:22px;background:var(--coral);opacity:.5;top:6%;left:-6%}
        .b2{width:13px;height:13px;background:var(--leaf);opacity:.55;bottom:16%;right:-3%;animation-delay:1.4s}
        .b3{width:30px;height:30px;background:var(--amber);opacity:.35;bottom:2%;left:16%;animation-delay:2.6s}
        .b4{width:9px;height:9px;background:var(--sky);opacity:.6;top:22%;right:6%;animation-delay:3.5s}
        @keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-13px)}}

        .mini{background:var(--white);border:1px solid var(--rule);border-radius:20px;
          box-shadow:0 20px 44px rgba(23,21,18,.11);overflow:hidden;position:relative;z-index:5;
          transform:rotate(-1.4deg);
          transition:transform .55s cubic-bezier(.2,.8,.25,1),box-shadow .55s ease;
          animation:drop .8s cubic-bezier(.2,.7,.3,1) both}
        .herovis:hover .mini{transform:rotate(0deg) translateY(-9px) scale(1.02);
          box-shadow:0 38px 74px rgba(23,21,18,.17)}
        .mini-top{display:flex;align-items:center;justify-content:space-between;padding:15px 18px;
          border-bottom:1px solid var(--rule);background:var(--tint)}
        .mini-top .t{font-family:'Newsreader',serif;font-size:19px;color:var(--ink);font-weight:500}
        .mini-top .mono{color:var(--dim)}
        .mini-body{padding:16px 17px 19px;display:flex;flex-direction:column;gap:9px}
        .mrow{border:1.5px solid var(--rule);border-radius:13px;padding:12px 14px;
          transition:transform .5s cubic-bezier(.2,.8,.25,1),box-shadow .4s ease}
        .mrow .mono{font-size:9.5px;color:var(--dim);display:block;margin-bottom:5px}
        .mrow .h{font-family:'Newsreader',serif;font-size:16.5px;color:var(--ink);line-height:1.26;
          display:block;font-weight:500}
        .mrow .v{font-size:11.5px;color:var(--dim);margin-top:5px;display:block;font-weight:600}
        .mrow.n{background:var(--tint)}
        .mrow.amber{background:var(--amber-bg);border-color:var(--amber-br)}
        .mrow.amber .mono{color:var(--amber)}
        .mrow.leaf{background:var(--leaf-bg);border-color:var(--leaf-br)}
        .mrow.leaf .mono{color:var(--leaf)}
        .herovis:hover .mrow.amber,.herovis:hover .mrow.leaf{transform:translateX(10px);
          box-shadow:-5px 6px 18px rgba(23,21,18,.11)}
        .herovis:hover .mrow.leaf{transition-delay:.07s}

        .peek{position:absolute;background:var(--white);border:1.5px solid var(--rule);border-radius:14px;
          padding:14px 15px;width:198px;box-shadow:0 12px 26px rgba(23,21,18,.10);
          transition:transform .6s cubic-bezier(.2,.8,.25,1),box-shadow .5s ease;
          animation:drop .9s cubic-bezier(.2,.7,.3,1) both}
        .peek .mono{font-size:9.5px;display:block;margin-bottom:7px}
        .peek .st{font-family:'Newsreader',serif;font-size:15px;color:var(--ink);line-height:1.26;font-weight:500}
        .peek.plum{border-color:var(--plum-br);background:var(--plum-bg)}
        .peek.plum .mono{color:var(--plum)}
        .peek.sky{border-color:var(--sky-br);background:var(--sky-bg)}
        .peek.sky .mono{color:var(--sky)}
        .peek.coral{border-color:var(--coral-br);background:var(--coral-bg)}
        .peek.coral .mono{color:var(--coral)}
        .p1{top:-18px;right:-20px;transform:rotate(6deg);z-index:3;animation-delay:.2s}
        .p2{bottom:-10px;left:-28px;transform:rotate(-5deg);z-index:4;animation-delay:.34s}
        .p3{top:46%;right:-38px;transform:rotate(-2deg) scale(.93);z-index:2;animation-delay:.46s}
        .herovis:hover .p1{transform:rotate(10deg) translate(28px,-26px);box-shadow:0 24px 42px rgba(23,21,18,.15)}
        .herovis:hover .p2{transform:rotate(-9.5deg) translate(-32px,20px);box-shadow:0 24px 42px rgba(23,21,18,.15)}
        .herovis:hover .p3{transform:rotate(2deg) translate(46px,12px) scale(.98)}
        @keyframes drop{from{opacity:0;transform:translateY(-20px)}}
        @media(max-width:1080px){.peek,.stackhint,.blob{display:none}}

        /* ── photo strip ── */
        .pstrip{border-top:1px solid var(--rule);background:var(--white);position:relative;z-index:2;
          padding:38px 0 42px}
        .pstrip .lab{display:flex;align-items:center;gap:16px;margin-bottom:24px}
        .pstrip .lab .mono{color:var(--brand)}
        .pstrip .lab i{flex:1;height:1px;background:var(--rule2)}
        .prow{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
        .pcell{position:relative;transition:transform .4s cubic-bezier(.2,.8,.25,1)}
        .pcell:hover{transform:translateY(-7px)}
        .pcell .ph{box-shadow:0 8px 22px rgba(23,21,18,.08);transition:box-shadow .4s ease}
        .pcell:hover .ph{box-shadow:0 20px 42px rgba(23,21,18,.15)}
        .pcell .ph img{transition:transform .8s cubic-bezier(.2,.8,.25,1)}
        .pcell:hover .ph img{transform:scale(1.06)}
        .pcell .cap{margin-top:11px;font-size:11.5px;color:var(--dim);font-weight:700;
          letter-spacing:.11em;text-transform:uppercase}
        .pcell:nth-child(2){margin-top:26px}

        /* ── reassurance ── */
        .reassure{border-top:1px solid var(--rule);background:var(--paper);position:relative;z-index:2}
        .rgrid{display:grid;grid-template-columns:repeat(5,1fr)}
        .rcell{padding:32px 26px 34px;border-right:1px solid var(--rule)}
        .rcell:last-child{border-right:0}
        .rcell .dot{width:32px;height:32px;border-radius:11px;margin-bottom:16px}
        .rcell h4{font-size:16.5px;margin-bottom:9px;line-height:1.26;letter-spacing:-.02em}
        .rcell p{font-size:13.5px;color:var(--ink2);line-height:1.6}

        /* ── dark claim ── */
        .claim{background:var(--ink);color:#fff;position:relative;z-index:2;overflow:hidden}
        .claim::before{content:'';position:absolute;width:460px;height:460px;right:-120px;top:-180px;
          background:radial-gradient(circle,rgba(196,98,46,.28) 0%,transparent 68%)}
        .claim .wrap{padding-top:58px;padding-bottom:58px;display:grid;
          grid-template-columns:1.15fr 1fr;gap:52px;align-items:center}
        .claim .mono{color:var(--brand-hi);display:block;margin-bottom:16px}
        .claim h2{font-size:clamp(27px,3.3vw,42px);color:#fff;line-height:1.16}
        .claim h2 span{color:var(--brand-hi)}
        .claim p{color:#BEB8AC;font-size:15.5px;line-height:1.7}
        .claim p+p{margin-top:14px}

        /* ── ticker ── */
        .ticker{border-bottom:1px solid var(--rule);padding:16px 0;overflow:hidden;
          background:var(--tint);position:relative;z-index:2}
        .ticker-track{display:flex;width:max-content;animation:slide 46s linear infinite}
        .ticker:hover .ticker-track{animation-play-state:paused}
        @keyframes slide{to{transform:translateX(-50%)}}
        .tick{font-family:'Newsreader',serif;font-size:19px;color:var(--ink);padding:0 30px;
          white-space:nowrap;display:flex;align-items:center;gap:30px;font-weight:500}
        .tick::after{content:'';width:6px;height:6px;border-radius:50%;background:var(--brand);flex-shrink:0}

        /* ── sections ── */
        .sec{padding:92px 0;border-top:1px solid var(--rule);position:relative;z-index:2}
        .sechead{display:flex;align-items:center;gap:18px;margin-bottom:36px;flex-wrap:wrap}
        .sechead .mono{color:var(--dim)}
        .sechead .mono.k{color:var(--brand)}
        .sechead i{flex:1;height:1px;background:var(--rule);min-width:20px}
        .sec h2{font-size:clamp(29px,4.1vw,46px);max-width:20ch;margin-bottom:20px}
        .note{color:var(--ink2);max-width:60ch;font-size:16.5px}

        .vs{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:34px}
        .vscard{border:1.5px solid var(--rule);border-radius:20px;padding:30px 28px 32px;background:var(--white)}
        .vscard.ours{background:var(--amber-bg);border-color:var(--amber-br)}
        .vscard .mono{color:var(--dim);display:block;margin-bottom:15px}
        .vscard.ours .mono{color:var(--amber)}
        .vscard h3{font-size:20px;margin-bottom:15px;letter-spacing:-.022em}
        .vslist{list-style:none;display:flex;flex-direction:column;gap:11px}
        .vslist li{font-size:14.5px;color:var(--ink2);display:flex;gap:11px;align-items:baseline}
        .vslist li::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--rule2);flex-shrink:0;transform:translateY(-2px)}
        .vscard.ours .vslist li::before{background:var(--amber)}

        .asks{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin-top:34px}
        .ask{border:1.5px solid var(--rule);border-radius:20px;overflow:hidden;background:var(--white);
          transition:transform .35s cubic-bezier(.2,.8,.25,1),box-shadow .35s}
        .ask:hover{transform:translateY(-6px);box-shadow:0 18px 38px rgba(23,21,18,.1)}
        .ask .ph{border-radius:0}
        .ask .inner{padding:24px 26px 28px}
        .ask .mono{display:block;margin-bottom:12px}
        .ask h3{font-size:19px;margin-bottom:10px;line-height:1.26;letter-spacing:-.022em}
        .ask p{font-size:14px;color:var(--ink2);line-height:1.6}

        .split{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:38px}
        .inbox{background:var(--white);border:1.5px solid var(--rule);border-radius:20px;overflow:hidden}
        .inbox-top{display:flex;align-items:center;justify-content:space-between;padding:15px 18px;
          border-bottom:1px solid var(--rule);background:var(--tint)}
        .inbox-top .who{font-size:13.5px;color:var(--ink);font-weight:700}
        .inbox-top .mono{color:var(--dim)}
        .inbox-body{padding:16px 17px 20px;min-height:402px}
        .blk{border:1.5px solid var(--rule);border-radius:13px;padding:13px 15px;margin-bottom:9px;
          position:relative;opacity:0;transform:translateY(10px) scale(.98);
          transition:opacity .45s ease,transform .45s cubic-bezier(.2,.7,.3,1),box-shadow .2s}
        .blk.in{opacity:1;transform:none}
        .blk .mono{font-size:9.5px;color:var(--dim);display:block;margin-bottom:6px}
        .blk .h{font-family:'Newsreader',serif;font-size:16.5px;color:var(--ink);line-height:1.26;
          display:block;font-weight:500}
        .blk .v{font-size:11.5px;color:var(--dim);margin-top:5px;display:block;font-weight:600}
        .blk.n{background:var(--tint)}
        .blk.amber{background:var(--amber-bg);border-color:var(--amber-br)}
        .blk.amber .mono{color:var(--amber)}
        .blk.leaf{background:var(--leaf-bg);border-color:var(--leaf-br)}
        .blk.leaf .mono{color:var(--leaf)}
        .blk.plum{background:var(--plum-bg);border-color:var(--plum-br)}
        .blk.plum .mono{color:var(--plum)}
        .blk.own:hover{box-shadow:0 8px 20px rgba(23,21,18,.1)}
        .why{position:absolute;left:12px;right:12px;bottom:calc(100% + 7px);background:var(--ink);
          color:#fff;padding:9px 12px;border-radius:9px;font-size:11.5px;line-height:1.4;font-weight:600;
          opacity:0;transform:translateY(5px);transition:opacity .2s,transform .2s;pointer-events:none;z-index:5}
        .why::after{content:'';position:absolute;top:100%;left:22px;border:5px solid transparent;border-top-color:var(--ink)}
        .blk.own:hover .why{opacity:1;transform:none}
        .legend{display:flex;gap:26px;flex-wrap:wrap;margin-top:24px;align-items:center}
        .legend div{display:flex;align-items:center;gap:9px;font-size:13px;color:var(--ink2);font-weight:600}
        .sw{width:14px;height:14px;border-radius:5px;border:1.5px solid var(--rule2)}
        .sw.k{background:var(--amber-bg);border-color:var(--amber-br)}
        .sw.n{background:var(--tint)}
        .mockmark{margin-top:16px;color:var(--dim);font-size:12.5px}

        .demo{display:grid;grid-template-columns:1.1fr .85fr;gap:24px;margin-top:36px}
        .chatbox{background:var(--white);border:1.5px solid var(--rule);border-radius:20px;padding:22px;
          min-height:410px;display:flex;flex-direction:column;gap:11px}
        .chatbox .hd{display:flex;justify-content:space-between;align-items:center;
          padding-bottom:15px;border-bottom:1px solid var(--rule);margin-bottom:4px}
        .chatbox .hd .mono{color:var(--dim)}
        .live{display:flex;align-items:center;gap:7px;color:var(--leaf)}
        .live i{width:7px;height:7px;border-radius:50%;background:var(--leaf);animation:blip 1.6s ease infinite}
        @keyframes blip{0%,100%{opacity:1}50%{opacity:.25}}
        .bub{max-width:84%;padding:12px 15px;border-radius:16px;font-size:14.5px;line-height:1.52;
          animation:pop .4s cubic-bezier(.2,.7,.3,1) both}
        @keyframes pop{from{opacity:0;transform:translateY(8px)}}
        .bub.agent{background:var(--tint);color:var(--ink2);border-bottom-left-radius:5px;align-self:flex-start}
        .bub.maker{background:var(--amber-bg);color:var(--ink);border-bottom-right-radius:5px;align-self:flex-end}
        .dots{display:flex;gap:4px;padding:14px 16px;background:var(--tint);border-radius:16px;
          border-bottom-left-radius:5px;align-self:flex-start;width:fit-content}
        .dots i{width:6px;height:6px;border-radius:50%;background:var(--dim);animation:bob 1.1s ease infinite}
        .dots i:nth-child(2){animation-delay:.16s}.dots i:nth-child(3){animation-delay:.32s}
        @keyframes bob{0%,60%,100%{opacity:.3;transform:translateY(0)}30%{opacity:1;transform:translateY(-4px)}}
        .harvest{background:var(--white);border:1.5px solid var(--rule);border-radius:20px;padding:24px}
        .harvest .mono{color:var(--brand);display:block;margin-bottom:16px}
        .hrow{display:flex;gap:14px;padding:13px 0;border-bottom:1px solid var(--rule);
          opacity:0;transform:translateX(-8px);transition:opacity .45s ease,transform .45s ease}
        .hrow.in{opacity:1;transform:none}
        .hrow:last-child{border-bottom:0}
        .hrow .k{font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
          color:var(--dim);min-width:52px;padding-top:3px}
        .hrow .v{font-size:14.5px;color:var(--ink);line-height:1.42}
        .harvest .foot{margin-top:16px;padding-top:15px;border-top:1px solid var(--rule);font-size:12.5px;color:var(--dim)}

        .bounds{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
        .bound{border-radius:20px;padding:28px 26px 30px;transition:transform .3s}
        .bound:hover{transform:translateY(-5px)}
        .bound:nth-child(1){background:var(--coral-bg)}
        .bound:nth-child(2){background:var(--leaf-bg)}
        .bound:nth-child(3){background:var(--sky-bg)}
        .bound .dot{width:34px;height:34px;border-radius:12px;margin-bottom:18px}
        .bound:nth-child(1) .dot{background:var(--coral)}
        .bound:nth-child(2) .dot{background:var(--leaf)}
        .bound:nth-child(3) .dot{background:var(--sky)}
        .bound p{font-size:19px;color:var(--ink);line-height:1.3;margin-bottom:12px;
          font-weight:800;letter-spacing:-.022em}
        .bound span{font-size:14.5px;color:var(--ink2)}

        .cols{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:34px}
        .card{background:var(--white);border:1.5px solid var(--rule);border-radius:20px;
          padding:34px 32px 36px;transition:transform .3s,box-shadow .3s}
        .card:hover{transform:translateY(-5px);box-shadow:0 18px 38px rgba(23,21,18,.09)}
        .card .mono{color:var(--brand);display:block;margin-bottom:17px}
        .card h3{font-size:22px;margin-bottom:12px;line-height:1.24;letter-spacing:-.024em}
        .card p{font-size:15px;color:var(--ink2);margin-bottom:18px}
        .facts{list-style:none;display:flex;flex-direction:column;gap:10px}
        .facts li{display:flex;gap:12px;font-size:14.5px;color:var(--ink);align-items:baseline}
        .facts li::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--brand);flex-shrink:0;transform:translateY(-2px)}

        .vision{background:var(--ink);color:#fff;position:relative;z-index:2;overflow:hidden}
        .vision::before{content:'';position:absolute;width:500px;height:500px;left:-140px;bottom:-220px;
          background:radial-gradient(circle,rgba(94,148,100,.22) 0%,transparent 68%)}
        .vision .wrap{padding-top:86px;padding-bottom:90px}
        .visgrid{display:grid;grid-template-columns:.86fr 1.14fr;gap:56px;align-items:center}
        .vision .mono{color:var(--brand-hi);display:block;margin-bottom:20px}
        .vision h2{font-size:clamp(27px,3.4vw,42px);color:#fff;line-height:1.2;margin-bottom:22px}
        .vision h2 span{color:var(--brand-hi)}
        .vision p{color:#BEB8AC;font-size:16px;line-height:1.72}
        .vision p+p{margin-top:14px}
        .vispair{display:grid;grid-template-columns:1fr 1fr;gap:16px}
        .vispair .ph:first-child{margin-top:34px}

        .close{padding:94px 0 106px;border-top:1px solid var(--rule);text-align:center;position:relative;z-index:2}
        .close h2{font-size:clamp(29px,4vw,44px);max-width:22ch;margin:0 auto 22px}
        .close p{color:var(--ink2);max-width:52ch;margin:0 auto 30px;font-size:16.5px}
        .close .routes{justify-content:center}

        footer{border-top:1px solid var(--rule);padding:34px 32px 50px;position:relative;z-index:2}
        .foot{max-width:1200px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap}
        .footlinks{display:flex;gap:24px;flex-wrap:wrap}
        .footlinks a{text-decoration:none;color:var(--dim);transition:color .18s}
        .footlinks a:hover{color:var(--ink)}
        .foot .mono{color:var(--dim)}

        @media(max-width:1100px){
          .rgrid{grid-template-columns:repeat(3,1fr)}
          .rcell:nth-child(3){border-right:0}
          .rcell:nth-child(1),.rcell:nth-child(2),.rcell:nth-child(3){border-bottom:1px solid var(--rule)}
          .prow{gap:14px}
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
          .prow{grid-template-columns:1fr;gap:20px}
          .pcell:nth-child(2){margin-top:0}
        }
        @media(max-width:620px){
          .navlinks a.mono:not(.navcta){display:none}
          .brandsub{display:none}
          .statbar span{display:none}
          .sec{padding:66px 0}
          .tick{font-size:16px;padding:0 20px}
          .routes{flex-direction:column}
          .route{width:100%;align-items:center}
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
              <h1>
                Some of your best customers will never join your mailing list.{' '}
                <span>They'll read this one.</span>
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
              <span className="blob b1" /><span className="blob b2" />
              <span className="blob b3" /><span className="blob b4" />

              <div className="peek p1 plum">
                <span className="mono">Fiber &amp; Fawn</span>
                <div className="st">Twelve years of the same Saturday</div>
              </div>
              <div className="peek p2 sky">
                <span className="mono">Pike Fish Co</span>
                <div className="st">The neighbors knocked to ask what was burning</div>
              </div>
              <div className="peek p3 coral">
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
                  <div className="mrow amber">
                    <span className="mono">Picked for this reader</span>
                    <span className="h">She's not famous. She's out of chili oil.</span>
                    <span className="v">Cedar Bakery · Ballard</span>
                  </div>
                  <div className="mrow leaf">
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
                <Photo src={s.src} alt={s.cap} tone={s.tone} ratio="4 / 3" />
                <div className="cap">{s.cap}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── REASSURANCE ── */}
      <section className="reassure">
        <div className="rgrid">
          {[
            ['var(--amber)', "It's a different appetite", "Lots of people love your brand and will never sign up for your newsletter. One email about the whole neighborhood? That they'll take."],
            ['var(--leaf)', 'Your list stays yours', "We don't see it. We don't import it. We don't email it."],
            ['var(--coral)', 'Talk it out or write it up', "Whichever suits you. If you've got someone who writes well, even better."],
            ['var(--sky)', 'Nothing goes out unread', "You see every story first. If something's wrong, you say so and we fix it."],
            ['var(--plum)', 'Free, and staying free', 'For you and for the people reading.'],
          ].map(([c, h, p], i) => (
            <div className="rcell" key={i}>
              <div className="dot" style={{ background: c as string }} />
              <h4>{h}</h4>
              <p>{p}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── DARK CLAIM ── */}
      <section className="claim">
        <div className="wrap">
          <div>
            <span className="mono">The whole idea</span>
            <h2>One issue goes out.<br /><span>No two people get the same email.</span></h2>
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
          <h2>It's a different job, and a different reader.</h2>
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
          <h2>We ask about the week, not about the product.</h2>
          <p className="note">
            Nobody has to come up with an idea. We ask, you answer, and it's usually more
            interesting than you think. Three of the questions we actually use:
          </p>
          <div className="asks">
            {ASKS.map((a, i) => (
              <div className="ask" key={i}>
                <Photo src={a.src} alt="" tone={a.tone} ratio="16 / 9" />
                <div className="inner">
                  <span className="mono" style={{ color: `var(--${a.tone})` }}>Question {i + 1}</span>
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
          <h2>The same week. Two different emails.</h2>
          <p className="note">
            Sam scans the bakery's code most Saturdays. Jo scans the farm's. They both get
            Brown Bag No. 6, and what's inside is not the same.
            <br /><span style={{ color: 'var(--dim)', fontSize: 14 }}>Hover a coloured block to see why it was picked.</span>
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
                    <div key={i}
                      className={`blk ${b.own ? `own ${b.tone}` : 'n'} ${dealt > i * 2 + box.off ? 'in' : ''}`}>
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
          <h2>It remembers what you told it last time.</h2>
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
          <h2>The rules matter more than the features.</h2>
          <p className="note" style={{ marginBottom: 38 }}>
            Three things are fixed. They're why a business can hand us a story and a reader
            keeps opening the email.
          </p>
          <div className="bounds">
            <div className="bound">
              <div className="dot" />
              <p>Nothing is published without a person reading it first.</p>
              <span>Every story, every sponsor, every line. An editor approves it or it doesn't run.
                There is no automatic path to a reader's inbox.</span>
            </div>
            <div className="bound">
              <div className="dot" />
              <p>We never write a fact you didn't tell us.</p>
              <span>Your words are kept exactly as you said them. Every published sentence traces
                back to one of them, and you can correct it at any point.</span>
            </div>
            <div className="bound">
              <div className="dot" />
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
          <h2>One neighborhood at a time, on purpose.</h2>
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
                <span>You'll probably never know who.</span></h2>
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
              {/* hero-a: hands mid-task, tight crop. src="/photos/hero-a.jpg" */}
              <Photo alt="Hands at work" tone="coral" ratio="3 / 4" />
              {/* hero-b: a stall from the customer's side. src="/photos/hero-b.jpg" */}
              <Photo alt="A stall on a Saturday" tone="leaf" ratio="3 / 4" />
            </div>
          </div>
        </div>
      </section>

      {/* ── CLOSE ── */}
      <section className="close rise">
        <div className="wrap">
          <h2>If you sell something near people, we'd like to hear from you.</h2>
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
          <a className="brandmark" href="/" style={{ fontSize: 20 }}>Marlo</a>
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