import { useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { api, mediaUrl, store, uploadPhoto } from '../lib/api'
import { Avatar, Cats, CopyButton, FollowBox, Notice, Page, Paras, SampleTag, Spinner, StoryCard, useLoad } from '../ui/kit'

// ── /m/:slug — one QR for a whole market ──────────────────────────────────────

export function VenuePage() {
  const { slug = '' } = useParams()
  const { data, error } = useLoad(() => api(`/public/venue/${slug}`), [slug])
  const [picked, setPicked] = useState<string[]>([])
  const [q, setQ] = useState('')

  const vendors = useMemo(() => (data?.vendors || []).filter((v: any) =>
    !q || v.name.toLowerCase().includes(q.toLowerCase()) || (v.categories || []).join(' ').includes(q.toLowerCase())), [data, q])

  if (error) return <Page narrow><Notice kind="bad">{error}</Notice></Page>
  if (!data) return <Page narrow><Spinner /></Page>
  const toggle = (id: string) => setPicked((p) => p.includes(id) ? p.filter((x) => x !== id) : [...p, id])

  return (
    <Page narrow>
      <section className="pb-6 pt-10">
        <p className="eyebrow">Brown Bag · {data.neighborhood}</p>
        <h1 className="mt-2 font-serif text-[40px] font-medium leading-tight">{data.name}</h1>
        {data.schedule_note && <p className="mt-2 text-soft">{data.schedule_note}</p>}
        <p className="mt-4 text-[17px] leading-relaxed">Which stalls did you visit? Tick the ones you liked and we'll tell you each week where they'll be, what's new, and the story behind them.</p>
      </section>

      {data.vendors.length > 6 && (
        <input className="field mb-3" placeholder="Search vendors" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search vendors" />
      )}
      <ul className="flex flex-col gap-2">
        {vendors.map((v: any) => {
          const on = picked.includes(v.id)
          return (
            <li key={v.id}>
              <label className={`card flex cursor-pointer items-start gap-3 p-4 transition ${on ? 'border-kraft ring-2 ring-kraft/20' : ''}`}>
                <input type="checkbox" className="mt-1 h-5 w-5 shrink-0 accent-[#a86f37]" checked={on} onChange={() => toggle(v.id)} />
                <Avatar name={v.name} url={v.photo_url} size={44} />
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-center gap-2"><span className="font-semibold">{v.name}</span><SampleTag show={v.is_sample} /></span>
                  <span className="mt-0.5 block text-[14px] text-soft">{v.description}</span>
                  {v.latest && <span className="mt-1 block text-[13px] text-kraftdeep">Latest: {v.latest.headline}</span>}
                </span>
                <Link to={`/v/${v.scan_code}`} className="shrink-0 text-[13px] text-soft" onClick={(e) => e.stopPropagation()}>Page</Link>
              </label>
            </li>
          )
        })}
      </ul>
      {!data.vendors.length && <Notice>No vendors from this market have joined yet.</Notice>}

      <div className="card mt-6 p-4">
        <p className="mb-2 text-[14px] font-semibold">{picked.length ? `${picked.length} selected` : 'Select the vendors you liked'}</p>
        <FollowBox vendorIds={picked} source="qr_venue" sourceRef={slug} cta={picked.length > 1 ? `Follow ${picked.length} vendors` : 'Follow'} />
      </div>
    </Page>
  )
}

// ── /v/:code — a vendor's page (their own QR lands here) ─────────────────────

export function VendorPage() {
  const { code = '' } = useParams()
  const [sp] = useSearchParams()
  const qr = sp.get('qr') ? 1 : 0
  const { data, error } = useLoad(() => api(`/public/vendor/${code}?qr=${qr}`), [code])
  if (error) return <Page narrow><div className="py-12"><Notice kind="bad">{error}</Notice></div></Page>
  if (!data) return <Page narrow><Spinner /></Page>
  return (
    <Page narrow>
      <section className="pb-8 pt-10">
        <div className="flex items-center gap-4">
          <Avatar name={data.name} url={data.photo_url} size={64} />
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2"><h1 className="font-serif text-[34px] font-medium leading-tight">{data.name}</h1><SampleTag show={data.is_sample} /></div>
            <p className="text-soft">{[data.venue?.name, data.neighborhood].filter(Boolean).join(' · ')}</p>
          </div>
        </div>
        {data.description && <p className="mt-5 text-[17px] leading-relaxed">{data.description}</p>}
        <div className="mt-3 flex flex-wrap gap-2"><Cats cats={data.categories} /></div>
        {data.schedule_note && <p className="mt-4 rounded-lg bg-kraft/10 px-3 py-2 text-[15px] text-kraftdeep"><b>Where to find them:</b> {data.schedule_note}</p>}
        <div className="card mt-6 p-5">
          <p className="mb-3 font-semibold">Follow {data.name}</p>
          <p className="mb-4 text-[14px] text-soft">Get their news in the free Brown Bag email: where they'll be, what's new, and their stories. {data.followers > 2 ? `${data.followers} people follow them.` : ''}</p>
          <FollowBox vendorIds={[data.id]} source={qr ? 'qr_vendor' : 'vendor_page'} sourceRef={code} compact />
        </div>
        <div className="mt-3 flex flex-wrap gap-4 text-[14px]">
          {data.instagram && <a href={`https://instagram.com/${data.instagram}`} target="_blank" rel="noreferrer" className="text-soft">Instagram @{data.instagram}</a>}
          {data.website && <a href={data.website.startsWith('http') ? data.website : `https://${data.website}`} target="_blank" rel="noreferrer" className="text-soft">Website</a>}
          {data.venue && <Link to={`/m/${data.venue.slug}`} className="text-soft">More vendors at {data.venue.name}</Link>}
        </div>
      </section>

      {data.updates.length > 0 && (
        <section className="border-t border-line py-8">
          <h2 className="eyebrow">Latest news</h2>
          {data.updates.map((u: any) => (
            <div key={u.id} className="mt-4"><p className="font-semibold">{u.headline}</p><p className="mt-1 leading-relaxed text-ink/90">{u.body}</p></div>
          ))}
        </section>
      )}

      {data.stories.length > 0 && (
        <section className="border-t border-line py-8">
          <h2 className="eyebrow mb-4">Stories</h2>
          <div className="flex flex-col gap-3">{data.stories.map((s: any) => <StoryCard key={s.id} s={{ ...s, vendor: { name: data.name, neighborhood: data.neighborhood } }} />)}</div>
        </section>
      )}

      <section className="border-t border-line py-8">
        <h2 className="eyebrow">Readers made this</h2>
        {data.shares.map((s: any) => (
          <figure key={s.id} className="mt-4">
            {s.image_url && <img src={mediaUrl(s.image_url)} alt="" className="mb-2 max-h-80 w-full rounded-lg object-cover" loading="lazy" />}
            <blockquote className="font-serif text-[18px] leading-relaxed">“{s.text}”</blockquote>
            <figcaption className="mt-1 text-[13px] text-soft">— {s.reader_name || 'A reader'}</figcaption>
          </figure>
        ))}
        <p className="mt-4 text-[15px]">Bought something from {data.name}? <Link to={`/share?v=${data.id}`} className="font-semibold text-kraft">Share what you made with it</Link>.</p>
      </section>
    </Page>
  )
}

// ── /s/:slug — a story ───────────────────────────────────────────────────────

export function StoryPage() {
  const { slug = '' } = useParams()
  const { data, error } = useLoad(() => api(`/public/story/${slug}`), [slug])
  if (error) return <Page narrow><div className="py-12"><Notice kind="bad">{error}</Notice></div></Page>
  if (!data) return <Page narrow><Spinner /></Page>
  const v = data.vendor
  const token = store.get('reader')
  const shareUrl = `${window.location.origin}/s/${data.slug}${token ? `?ref=${token}` : ''}`
  const date = data.reviewed_at ? new Date(data.reviewed_at).toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' }) : ''
  return (
    <Page narrow>
      <article className="pb-10 pt-10">
        <div className="flex flex-wrap items-center gap-2 text-[14px] text-soft">
          {v && <Link to={`/v/${v.scan_code}`} className="font-semibold text-kraftdeep no-underline">{v.name}</Link>}
          {v?.neighborhood && <span>· {v.neighborhood}</span>}
          {date && <span>· {date}</span>}
          <SampleTag show={data.is_sample} />
        </div>
        <h1 className="mt-3 font-serif text-[40px] font-medium leading-[1.1] sm:text-[46px]">{data.headline}</h1>
        <div className="mt-8"><Paras text={data.body} /></div>
        <p className="mt-6 text-[13px] text-soft">Told by {v?.name || 'the vendor'}, checked by them, and approved by a Brown Bag editor.</p>
        <div className="mt-6 flex flex-wrap items-center gap-2">
          <span className="text-[14px] font-semibold">Send this story to someone</span>
          <CopyButton text={shareUrl} label="Copy link" />
          {typeof navigator !== 'undefined' && (navigator as any).share && (
            <button className="btn-quiet btn-sm" onClick={() => (navigator as any).share({ title: data.headline, url: shareUrl }).catch(() => {})}>Share</button>
          )}
        </div>
      </article>
      {v && (
        <section className="card mb-10 p-5">
          <div className="flex items-center gap-3">
            <Avatar name={v.name} url={v.photo_url} size={44} />
            <div><p className="font-semibold">{v.name}</p><p className="text-[14px] text-soft">{v.schedule_note || v.neighborhood}</p></div>
          </div>
          <p className="mb-4 mt-4 text-[15px]">Follow {v.name} to hear what happens next.</p>
          <FollowBox vendorIds={[v.id]} source="story_page" sourceRef={data.slug} compact />
        </section>
      )}
      {data.more?.length > 0 && (
        <section className="mb-10">
          <h2 className="eyebrow mb-3">More from {v?.name}</h2>
          <div className="flex flex-col gap-3">{data.more.filter((m: any) => m.kind === 'story').map((m: any) => <StoryCard key={m.id} s={{ ...m, vendor: v }} />)}</div>
        </section>
      )}
    </Page>
  )
}

export function StoriesPage() {
  const { data } = useLoad(() => api('/public/stories'))
  return (
    <Page>
      <section className="wrap pb-6 pt-12">
        <p className="eyebrow">Brown Bag</p>
        <h1 className="mt-2 font-serif text-[44px] font-medium">Stories</h1>
        <p className="mt-2 max-w-prose text-soft">Every story here started as a conversation with the vendor. They checked it, and an editor approved it.</p>
      </section>
      <section className="wrap">
        {!data ? <Spinner /> : <div className="grid gap-4 md:grid-cols-2">{data.map((s: any) => <StoryCard key={s.id} s={s} />)}</div>}
        {data && !data.length && <Notice>No stories yet. The first ones are being written.</Notice>}
      </section>
    </Page>
  )
}

// ── /share — "I made this" ───────────────────────────────────────────────────

export function SharePage() {
  const [sp] = useSearchParams()
  const t = sp.get('t') || store.get('reader') || undefined
  const { data: vendors } = useLoad(() => api('/public/vendors'))
  const [vendorId, setVendorId] = useState(sp.get('v') || '')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [text, setText] = useState('')
  const [photo, setPhoto] = useState<string>('')
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<{ kind: 'good' | 'bad'; text: string } | null>(null)

  async function onFile(f?: File) {
    if (!f) return
    setBusy(true)
    try { setPhoto(await uploadPhoto(f)) } catch (e: any) { setMsg({ kind: 'bad', text: e.message }) } finally { setBusy(false) }
  }
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setMsg(null)
    try {
      await api('/public/share', { body: { t, email: t ? undefined : email || undefined, reader_name: name || undefined, vendor_id: vendorId || undefined, text, image_url: photo || undefined } })
      setMsg({ kind: 'good', text: "Thanks! An editor will look at it this week, and the vendor will see it too." })
      setText(''); setPhoto('')
    } catch (e: any) { setMsg({ kind: 'bad', text: e.message }) } finally { setBusy(false) }
  }
  return (
    <Page narrow>
      <section className="pb-6 pt-10">
        <p className="eyebrow">Readers made this</p>
        <h1 className="mt-2 font-serif text-[38px] font-medium leading-tight">What did you make with it?</h1>
        <p className="mt-3 text-[17px] text-soft">Cooked something, wore something, gave something away? Send a photo and a line or two. The best ones run in next week's email, credited the way you like.</p>
      </section>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <div>
          <label className="label" htmlFor="share-vendor">Who did you buy it from?</label>
          <select id="share-vendor" className="field" value={vendorId} onChange={(e) => setVendorId(e.target.value)}>
            <option value="">Not sure / someone else</option>
            {(vendors || []).map((v: any) => <option key={v.id} value={v.id}>{v.name}</option>)}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="share-text">Tell us about it</label>
          <textarea id="share-text" className="field min-h-[120px]" required minLength={3} maxLength={1200} value={text} onChange={(e) => setText(e.target.value)} placeholder="Made Otto's apple-sage toast for Sunday breakfast…" />
        </div>
        <div>
          <label className="label" htmlFor="share-photo">Photo (optional)</label>
          <input id="share-photo" type="file" accept="image/*" className="block text-[14px]" onChange={(e) => onFile(e.target.files?.[0])} />
          {photo && <img src={mediaUrl(photo)} alt="Your upload" className="mt-3 max-h-60 rounded-lg" />}
        </div>
        <div>
          <label className="label" htmlFor="share-name">How should we credit you?</label>
          <input id="share-name" className="field" value={name} onChange={(e) => setName(e.target.value)} placeholder="Priya, Beacon Hill" maxLength={80} />
        </div>
        {!t && (
          <div>
            <label className="label" htmlFor="share-email">Your email (optional, so we can ask before we run it)</label>
            <input id="share-email" className="field" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
        )}
        {msg && <Notice kind={msg.kind}>{msg.text}</Notice>}
        <button className="btn-primary self-start" disabled={busy || text.trim().length < 3}>{busy ? 'Sending…' : 'Send it'}</button>
      </form>
    </Page>
  )
}

// ── /nominate ────────────────────────────────────────────────────────────────

export function NominatePage() {
  const [f, setF] = useState({ shop_name: '', where: '', why: '', email: '' })
  const [done, setDone] = useState(false)
  const [err, setErr] = useState('')
  const t = store.get('reader') || undefined
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr('')
    try { await api('/public/nominate', { body: { ...f, email: f.email || undefined, t } }); setDone(true) } catch (e: any) { setErr(e.message) }
  }
  return (
    <Page narrow>
      <section className="pb-6 pt-10">
        <p className="eyebrow">Nominate a shop</p>
        <h1 className="mt-2 font-serif text-[38px] font-medium leading-tight">Who should we write about?</h1>
        <p className="mt-3 text-[17px] text-soft">A stall, a bakery, a maker you keep going back to. If they join, you'll automatically follow them.</p>
      </section>
      {done ? <Notice kind="good">Thank you. We'll go say hello.</Notice> : (
        <form onSubmit={submit} className="flex flex-col gap-4">
          <div><label className="label" htmlFor="n-name">Shop or vendor name</label><input id="n-name" className="field" required value={f.shop_name} onChange={(e) => setF({ ...f, shop_name: e.target.value })} /></div>
          <div><label className="label" htmlFor="n-where">Where do you find them?</label><input id="n-where" className="field" value={f.where} onChange={(e) => setF({ ...f, where: e.target.value })} placeholder="Pike Place, north arcade, Saturdays" /></div>
          <div><label className="label" htmlFor="n-why">What's good about them?</label><textarea id="n-why" className="field min-h-[100px]" value={f.why} onChange={(e) => setF({ ...f, why: e.target.value })} /></div>
          {!t && <div><label className="label" htmlFor="n-email">Your email (optional)</label><input id="n-email" type="email" className="field" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></div>}
          {err && <Notice kind="bad">{err}</Notice>}
          <button className="btn-primary self-start">Send nomination</button>
        </form>
      )}
    </Page>
  )
}

// ── /unsubscribe ─────────────────────────────────────────────────────────────

export function UnsubscribePage() {
  const [sp] = useSearchParams()
  const t = sp.get('t') || ''
  const [state, setState] = useState<'ask' | 'done' | 'error'>('ask')
  const [msg, setMsg] = useState('')
  const { data: me } = useLoad(() => t ? api(`/public/me?t=${encodeURIComponent(t)}`) : Promise.resolve(null), [t])
  async function go() {
    try { await api('/public/unsubscribe', { body: { t } }); setState('done'); store.clear('reader') } catch (e: any) { setMsg(e.message); setState('error') }
  }
  async function unfollow(id: string) {
    await api('/public/unfollow', { body: { t, vendor_id: id } }).catch(() => {})
    window.location.reload()
  }
  return (
    <Page narrow>
      <section className="py-14">
        <h1 className="font-serif text-[36px] font-medium">Unsubscribe</h1>
        {!t && <p className="mt-3 text-soft">Use the unsubscribe link at the bottom of any Brown Bag email.</p>}
        {t && state === 'ask' && (
          <>
            <p className="mt-3 text-[17px]">{me?.email ? `${me.email} will stop getting Brown Bag.` : 'You will stop getting Brown Bag.'} No more emails, effective now.</p>
            <button className="btn-primary mt-6" onClick={go}>Unsubscribe</button>
            {me?.follows?.length > 1 && (
              <div className="mt-10">
                <p className="font-semibold">Or just stop following some vendors</p>
                <ul className="mt-3 flex flex-col gap-2">
                  {me.follows.map((f: any) => (
                    <li key={f.id} className="card flex items-center justify-between p-3"><span>{f.name}</span><button className="btn-quiet btn-sm" onClick={() => unfollow(f.id)}>Unfollow</button></li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
        {state === 'done' && <div className="mt-4"><Notice kind="good">Done. You won't get any more emails from us. If that was a mistake, follow any vendor again to come back.</Notice></div>}
        {state === 'error' && <div className="mt-4"><Notice kind="bad">{msg}</Notice></div>}
      </section>
    </Page>
  )
}
