import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { Page, Spinner, StoryCard, useLoad } from '../ui/kit'

export default function Home() {
  const { data } = useLoad(() => api('/public/home'))

  return (
    <Page>
      {/* Hero: what a reader gets */}
      <section className="wrap grid items-center gap-10 pb-16 pt-12 md:grid-cols-[1.1fr_1fr] md:pt-20">
        <div>
          <p className="eyebrow">Free · weekly · Seattle</p>
          <h1 className="mt-3 font-serif text-[44px] font-medium leading-[1.05] tracking-tight sm:text-[58px]">
            The people behind the stalls, in one short email a week.
          </h1>
          <p className="mt-5 max-w-prose text-[18px] leading-relaxed text-soft">
            Brown Bag follows the market vendors and makers you buy from. Once a week you get a real story from one of them,
            where your vendors will be, what's new, and what other readers made with what they bought.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/m/pike-place" className="btn-primary no-underline">Follow Pike Place vendors</Link>
            <Link to="/stories" className="btn-quiet no-underline">Read the stories</Link>
          </div>
          <p className="mt-4 text-[14px] text-soft">Saw a Brown Bag code at a stall? Scanning it follows that vendor.</p>
        </div>
        <IssueMock first={data?.stories?.[0]} />
      </section>

      {/* Latest stories */}
      <section className="wrap py-10">
        <div className="mb-6 flex items-end justify-between gap-4">
          <h2 className="font-serif text-[32px] font-medium">Recent stories</h2>
          <Link to="/stories" className="text-[15px] font-semibold text-kraft">All stories</Link>
        </div>
        {!data ? <Spinner /> : (
          <div className="grid gap-4 md:grid-cols-2">
            {data.stories.slice(0, 4).map((s: any) => <StoryCard key={s.id} s={s} />)}
          </div>
        )}
      </section>

      {/* Markets */}
      <section className="wrap py-10">
        <h2 className="font-serif text-[32px] font-medium">Follow a whole market</h2>
        <p className="mt-2 max-w-prose text-soft">Pick the vendors you like at a market and follow them in one go.</p>
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {(data?.venues || []).map((v: any) => (
            <Link key={v.slug} to={`/m/${v.slug}`} className="card block p-5 no-underline hover:border-kraft">
              <p className="font-serif text-[22px] font-medium text-ink">{v.name}</p>
              <p className="mt-1 text-[14px] text-soft">{v.neighborhood} · {v.vendor_count} {v.vendor_count === 1 ? 'vendor' : 'vendors'}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="wrap py-14">
        <div className="grid gap-10 md:grid-cols-3">
          {[
            ['Vendors talk, we write', "Each week we ask a vendor a question or two, the way a regular would. A writer turns the answer into a short story. Nobody has to write anything."],
            ['They check it, an editor approves it', 'The vendor sees the draft first and fixes anything wrong. Then a named editor reads every word before it goes out.'],
            ['You get one email', "Stories from the vendors you follow and a few you'd like, plus where they'll be. Reply with a photo of what you made and it might run next week."],
          ].map(([h, p]) => (
            <div key={h}>
              <h3 className="font-serif text-[23px] font-medium">{h}</h3>
              <p className="mt-2 leading-relaxed text-soft">{p}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Two doors */}
      <section className="wrap grid gap-4 py-6 md:grid-cols-2">
        <div className="overflow-hidden rounded-2xl bg-ink text-card">
          <img src="/photos/ask-3.jpg" alt="A jeweler showing customers her tools at a workbench" className="h-56 w-full object-cover opacity-90" loading="lazy" />
          <div className="p-7">
            <p className="eyebrow text-[#e3b886]">For vendors</p>
            <h3 className="mt-2 font-serif text-[28px] font-medium">Stay in touch with customers between market days.</h3>
            <p className="mt-2 text-card/80">Free. Answer a question on your phone; we do the writing and send it to people who already like what you make.</p>
            <Link to="/for-vendors" className="btn-kraft mt-5 no-underline">How it works for vendors</Link>
          </div>
        </div>
        <div className="overflow-hidden rounded-2xl border border-line bg-card">
          <img src="/photos/strip-1.jpg" alt="The Public Market Center sign at Pike Place at night" className="h-56 w-full object-cover" loading="lazy" />
          <div className="p-7">
            <p className="eyebrow">For markets</p>
            <h3 className="mt-2 font-serif text-[28px] font-medium">A weekly newsletter for your market, run for you.</h3>
            <p className="mt-2 text-soft">One shared QR code, stories from your vendors every week, and a live report on who's following whom.</p>
            <Link to="/for-markets" className="btn-primary mt-5 no-underline">See the market pilot</Link>
          </div>
        </div>
      </section>
    </Page>
  )
}

function IssueMock({ first }: { first?: any }) {
  const para = (first?.body || '').split('\n').filter((p: string) => p.trim()).slice(0, 2)
  return (
    <div className="relative mx-auto w-full max-w-md">
      <div className="absolute -inset-3 -rotate-2 rounded-2xl bg-[#d9b78f]" aria-hidden="true" />
      <div className="relative rounded-xl border border-line bg-card p-6 shadow-[0_1px_0_#e4d9c9]">
        <div className="flex items-baseline justify-between border-b border-line pb-3">
          <span className="font-serif text-[24px] font-semibold">Brown Bag</span>
          <span className="text-[12px] text-soft">Thursday · Seattle</span>
        </div>
        <p className="eyebrow mt-4">This week's story</p>
        <p className="mt-1 font-serif text-[24px] font-medium leading-tight">{first?.headline || 'She’s not famous. She’s out of chili oil.'}</p>
        <p className="mt-1 text-[13px] text-soft">{first?.vendor?.name || 'Fortune Noodle'} · {first?.vendor?.neighborhood || 'Ballard'}</p>
        <div className="mt-3 space-y-2 font-serif text-[16px] leading-relaxed text-ink/90">
          {(para.length ? para : ['Mei sold out by 11 on Saturday. She usually goes till two.']).map((p: string, i: number) => <p key={i}>{p}</p>)}
        </div>
        <p className="eyebrow mt-5">From your vendors</p>
        <p className="mt-1 text-[14px]"><b>Lena Ruiz Jewelry</b> — north arcade Thursday and Saturday, with new moon pendants.</p>
        <p className="eyebrow mt-5">Readers made this</p>
        <p className="mt-1 text-[14px] italic text-soft">“Made Otto's apple-sage toast with a fried egg on top. My kid asked for it again Monday.”</p>
      </div>
    </div>
  )
}
