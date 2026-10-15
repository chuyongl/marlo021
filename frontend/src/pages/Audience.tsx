import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { Notice, Page } from '../ui/kit'

const SCRIPT: { role: 'agent' | 'maker'; text: string }[] = [
  { role: 'agent', text: 'Did the moon pendants make it to the table this week?' },
  { role: 'maker', text: 'Yes, Thursday. Sold 9 of 12 before noon.' },
  { role: 'agent', text: 'Nine before noon. Who was buying them?' },
  { role: 'maker', text: 'A woman bought three, one for each of her daughters. She asked me to stamp their initials on the back.' },
  { role: 'agent', text: 'Did you stamp them right there at the table?' },
  { role: 'maker', text: "On my grandpa's railroad spike. She waited and watched the whole time." },
]

function InterviewDemo() {
  const [n, setN] = useState(1)
  useEffect(() => {
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (reduce) { setN(SCRIPT.length); return }
    const id = setInterval(() => setN((x) => (x >= SCRIPT.length ? 1 : x + 1)), 1900)
    return () => clearInterval(id)
  }, [])
  return (
    <div className="card mx-auto w-full max-w-sm p-4" aria-label="Example conversation with the Brown Bag interviewer">
      <p className="mb-3 text-center text-[12px] text-soft">This week · Lena Ruiz Jewelry</p>
      <div className="flex min-h-[340px] flex-col gap-2">
        {SCRIPT.slice(0, n).map((m, i) => (
          <div key={i} className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-[14px] leading-snug ${m.role === 'agent' ? 'self-start bg-paper' : 'self-end bg-ink text-card'}`}>{m.text}</div>
        ))}
      </div>
    </div>
  )
}

export function ForVendors() {
  return (
    <Page>
      <section className="wrap grid items-center gap-10 pb-12 pt-12 md:grid-cols-2 md:pt-16">
        <div>
          <p className="eyebrow">For vendors · free</p>
          <h1 className="mt-3 font-serif text-[42px] font-medium leading-[1.08] sm:text-[52px]">Your customers, between market days.</h1>
          <p className="mt-5 max-w-prose text-[18px] leading-relaxed text-soft">
            Some weeks you get a good spot and sell out. Some weeks you don't get a table at all. Brown Bag keeps the people who like
            your work hearing from you either way: where you'll be next, what's new, and the stories behind what you make.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/vendor/join" className="btn-primary no-underline">I have a code</Link>
            <a href="#ask" className="btn-quiet no-underline">Ask for a code</a>
            <Link to="/vendor" className="btn-ghost no-underline">Sign in</Link>
          </div>
        </div>
        <InterviewDemo />
      </section>

      <section className="wrap py-12">
        <h2 className="font-serif text-[32px] font-medium">You talk. We write. You check it.</h2>
        <div className="mt-8 grid gap-8 md:grid-cols-3">
          {[
            ['A question a week', 'We send one specific question to your phone. Answer between customers, in a line or two. The interviewer asks a follow-up only when there is something worth asking.'],
            ['You see it first', 'A writer turns your answers into a short story or a quick note. You read it before anyone else and fix anything wrong. Then an editor approves it.'],
            ['It reaches your people', 'Everyone who follows you gets it in their weekly email, along with where you will be. New readers discover you through stories they like.'],
          ].map(([h, p]) => (<div key={h}><h3 className="font-serif text-[23px] font-medium">{h}</h3><p className="mt-2 leading-relaxed text-soft">{p}</p></div>))}
        </div>
      </section>

      <section className="wrap py-12">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[
            ['Your own page and QR code', 'Print it on a table card. Customers scan, type their email once, and they follow you.'],
            ['A ready-made Instagram post', 'Every approved story comes with an image and a caption you can post as is.'],
            ['Who is following', 'See how many people follow you, how many clicked your story, and how many found you through it.'],
            ['Photos from customers', 'When a reader shares what they made with your sausage or how they wore your necklace, you see it.'],
            ['Quick updates', '"North arcade Thursday and Saturday." Type it in ten seconds; it goes in the next email.'],
            ['Nothing to pay', "Brown Bag is free for vendors. We don't take a cut, we don't ask for discounts."],
          ].map(([h, p]) => (<div key={h} className="card p-5"><p className="font-semibold">{h}</p><p className="mt-1.5 text-[15px] leading-relaxed text-soft">{p}</p></div>))}
        </div>
      </section>

      <section id="ask" className="wrap-narrow py-12">
        <h2 className="font-serif text-[30px] font-medium">Ask for a code</h2>
        <p className="mt-2 text-soft">We're starting at a few Seattle markets. Tell us where you sell and we'll get back to you.</p>
        <LeadForm kind="vendor" orgLabel="Where do you sell?" orgPlaceholder="Pike Place day stalls, Ballard Sunday market…" button="Ask for a code" />
      </section>
    </Page>
  )
}

export function ForMarkets() {
  return (
    <Page>
      <section className="relative">
        <img src="/photos/strip-1.jpg" alt="Pike Place Market's Public Market Center sign lit up at night" className="h-[460px] w-full object-cover sm:h-[440px]" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-black/10" />
        <div className="wrap absolute inset-x-0 bottom-0 pb-10 text-white">
          <p className="eyebrow text-[#f0c793]">For market organizations</p>
          <h1 className="mt-2 max-w-3xl font-serif text-[32px] font-medium leading-[1.1] sm:text-[52px]">A weekly newsletter for your market, written with your vendors and run for you.</h1>
        </div>
      </section>

      <section className="wrap grid gap-10 py-14 md:grid-cols-[1.2fr_1fr]">
        <div>
          <h2 className="font-serif text-[30px] font-medium">The problem it solves</h2>
          <div className="mt-4 space-y-4 text-[17px] leading-relaxed text-ink/90">
            <p>Most people who buy from a vendor never see them again unless they happen to walk past. Day-stall artisans move tables. Visitors go home. Instagram shows a vendor's posts to a small share of their own followers.</p>
            <p>Brown Bag gives every shopper one easy way to keep up with the vendors they liked: one QR code for the whole market, one email a week, written from what your vendors tell us and approved by a named editor.</p>
          </div>
        </div>
        <div className="card p-6">
          <p className="eyebrow">What the market gets</p>
          <ul className="mt-3 space-y-3 text-[15px] leading-relaxed">
            {[
              'One shared QR code for bags, signs and stalls. Shoppers tick the vendors they visited and follow them all at once.',
              'A page for every vendor, and a weekly interview that turns their week into a story or a short update.',
              'Stories checked by the vendor and approved by an editor before anything goes out.',
              'A ready-made Instagram post for every story, so vendors spread it themselves.',
              'A live report: how many people follow your vendors, which vendors are growing, which stories got read.',
            ].map((t) => <li key={t} className="flex gap-2"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-kraft" />{t}</li>)}
          </ul>
        </div>
      </section>

      <section className="wrap py-6">
        <h2 className="font-serif text-[30px] font-medium">What you'll see each week</h2>
        <p className="mt-2 max-w-prose text-soft">Your report lives at a private link you can share with your board. This is an example with made-up numbers.</p>
        <ReportPreview />
      </section>

      <section className="wrap grid gap-8 py-14 md:grid-cols-3">
        {[
          ['Free for vendors', 'Vendors never pay and never give a discount. That keeps them willing to take part, and it keeps the stories honest.'],
          ['No app to install', 'Shoppers scan and type an email. Vendors use a link on their phone. Nobody downloads anything.'],
          ['Careful with data', 'We only use follows to decide what goes in each email. No ad targeting on health or personal details, and one-click unsubscribe.'],
        ].map(([h, p]) => (<div key={h}><h3 className="font-serif text-[22px] font-medium">{h}</h3><p className="mt-2 leading-relaxed text-soft">{p}</p></div>))}
      </section>

      <section className="wrap-narrow pb-10">
        <div className="card p-6 sm:p-8">
          <p className="eyebrow">Pilot</p>
          <h2 className="mt-2 font-serif text-[30px] font-medium">Try it with your vendors for eight weeks.</h2>
          <p className="mt-2 text-soft">We set up your market, print-ready QR materials and vendor pages, run the weekly interviews and editing, and send you the report every week. Tell us a little about your market and we'll set up a call.</p>
          <div className="mt-6"><LeadForm kind="market" orgLabel="Market or organization" orgPlaceholder="Pike Place Market" button="Talk to us about a pilot" /></div>
        </div>
      </section>
    </Page>
  )
}

export function ReportPreview() {
  const rows = [
    ['Lena Ruiz Jewelry', 64, 3, 41], ['Pike Hill Honey', 52, 2, 33], ['Fortune Noodle', 47, 4, 58],
    ['Corner Cheese Co.', 31, 1, 12], ['Rosa’s Tamales', 22, 1, 9],
  ]
  const weeks = [12, 19, 25, 31, 44, 52, 61, 73]
  const max = Math.max(...weeks)
  return (
    <div className="card mt-6 overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-3">
        <p className="font-semibold">Example Market · weekly report</p>
        <span className="chip-info">Example</span>
      </div>
      <div className="grid grid-cols-2 gap-px bg-line sm:grid-cols-4">
        {[['Readers following your vendors', '412'], ['New follows this week', '73'], ['Story clicks, 30 days', '1,180'], ['Reader photos', '19']].map(([k, v]) => (
          <div key={k} className="bg-card px-5 py-4"><p className="num text-[28px] font-semibold">{v}</p><p className="text-[13px] text-soft">{k}</p></div>
        ))}
      </div>
      <div className="grid gap-6 p-5 md:grid-cols-[1fr_1.3fr]">
        <div>
          <p className="mb-3 text-[13px] font-semibold text-soft">New follows per week</p>
          <div className="flex h-36 items-end gap-2">
            {weeks.map((w, i) => (
              <div key={i} className="flex h-full flex-1 flex-col items-center justify-end gap-1">
                <span className="num text-[11px] text-soft">{w}</span>
                <div className={`w-full rounded-t ${i === weeks.length - 1 ? 'bg-kraft' : 'bg-kraft/35'}`} style={{ height: `${(w / max) * 100}%` }} />
              </div>
            ))}
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[14px]">
            <thead><tr className="text-left text-[12px] text-soft"><th className="py-1 pr-2 font-medium">Vendor</th><th className="num py-1 pr-2 text-right font-medium">Followers</th><th className="num py-1 pr-2 text-right font-medium">Stories</th><th className="num py-1 text-right font-medium">Clicks</th></tr></thead>
            <tbody>{rows.map(([n, f, s, c]) => (<tr key={n as string} className="border-t border-line"><td className="py-2 pr-2">{n}</td><td className="num py-2 pr-2 text-right">{f}</td><td className="num py-2 pr-2 text-right">{s}</td><td className="num py-2 text-right">{c}</td></tr>))}</tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function LeadForm({ kind, orgLabel, orgPlaceholder, button }: { kind: 'market' | 'vendor'; orgLabel: string; orgPlaceholder: string; button: string }) {
  const [f, setF] = useState({ name: '', organization: '', email: '', message: '' })
  const [state, setState] = useState<'idle' | 'busy' | 'done'>('idle')
  const [err, setErr] = useState('')
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setState('busy'); setErr('')
    try { await api('/public/lead', { body: { kind, ...f } }); setState('done') } catch (e: any) { setErr(e.message); setState('idle') }
  }
  if (state === 'done') return <Notice kind="good">Thanks, we got it. We'll email you within a couple of days.</Notice>
  return (
    <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
      <div><label className="label" htmlFor={`${kind}-name`}>Your name</label><input id={`${kind}-name`} className="field" required value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></div>
      <div><label className="label" htmlFor={`${kind}-email`}>Email</label><input id={`${kind}-email`} type="email" className="field" required value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></div>
      <div className="sm:col-span-2"><label className="label" htmlFor={`${kind}-org`}>{orgLabel}</label><input id={`${kind}-org`} className="field" placeholder={orgPlaceholder} value={f.organization} onChange={(e) => setF({ ...f, organization: e.target.value })} /></div>
      <div className="sm:col-span-2"><label className="label" htmlFor={`${kind}-msg`}>Anything else? (optional)</label><textarea id={`${kind}-msg`} className="field min-h-[90px]" value={f.message} onChange={(e) => setF({ ...f, message: e.target.value })} /></div>
      {err && <div className="sm:col-span-2"><Notice kind="bad">{err}</Notice></div>}
      <div className="sm:col-span-2"><button className="btn-primary" disabled={state === 'busy'}>{state === 'busy' ? 'Sending…' : button}</button></div>
    </form>
  )
}
