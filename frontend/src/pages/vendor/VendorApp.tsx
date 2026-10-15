import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api, mediaUrl, store, timeAgo, uploadPhoto, CATEGORY_LABEL } from '../../lib/api'
import { Avatar, BagMark, CopyButton, CopyField, Notice, Paras, QR, SampleTag, Spinner, useLoad } from '../../ui/kit'

type Tab = 'talk' | 'stories' | 'reach' | 'share' | 'profile'

// ── Entry points ─────────────────────────────────────────────────────────────

export function VendorHome() {
  const has = !!store.get('vendor')
  return has ? <VendorApp /> : <VendorLogin />
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-paper" style={{ paddingLeft: 'env(safe-area-inset-left,0px)', paddingRight: 'env(safe-area-inset-right,0px)' }}>
      <div className="wrap-narrow pb-16 pt-8">
        <Link to="/" className="inline-flex items-center gap-2 no-underline"><BagMark /><span className="font-serif text-[20px] font-semibold text-ink">Brown Bag</span><span className="text-[13px] text-soft">for vendors</span></Link>
        {children}
      </div>
    </div>
  )
}

export function VendorLogin() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [err, setErr] = useState('')
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr('')
    try { await api('/vendor/login', { body: { email } }); setSent(true) } catch (e: any) { setErr(e.message) }
  }
  return (
    <Shell>
      <h1 className="mt-10 font-serif text-[36px] font-medium">Sign in</h1>
      <p className="mt-2 text-soft">No password. We'll email you a link that keeps you signed in on this phone.</p>
      {sent ? <div className="mt-6"><Notice kind="good">If {email} has a vendor account, the link is on its way. Check your inbox (and spam).</Notice></div> : (
        <form onSubmit={submit} className="mt-6 flex flex-col gap-3">
          <label className="label" htmlFor="vl-email">Your email</label>
          <input id="vl-email" className="field" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          {err && <Notice kind="bad">{err}</Notice>}
          <button className="btn-primary self-start">Send me a login link</button>
        </form>
      )}
      <p className="mt-10 text-[15px]">New to Brown Bag? <Link to="/vendor/join" className="font-semibold text-kraft">Join with your code</Link> · <Link to="/for-vendors" className="text-soft">How it works</Link></p>
    </Shell>
  )
}

export function VendorAuth() {
  const [sp] = useSearchParams()
  const nav = useNavigate()
  const [err, setErr] = useState('')
  useEffect(() => {
    const token = sp.get('token') || ''
    api('/vendor/auth', { body: { token } })
      .then((r) => { store.set('vendor', r.session_token); nav('/vendor', { replace: true }) })
      .catch((e) => setErr(e.message))
  }, [sp, nav])
  return <Shell>{err ? <div className="mt-10"><Notice kind="bad">{err}</Notice><Link to="/vendor" className="btn-quiet mt-4 no-underline">Get a new link</Link></div> : <Spinner label="Signing you in" />}</Shell>
}

export function VendorJoin() {
  const [sp] = useSearchParams()
  const nav = useNavigate()
  const { data: opts } = useLoad(() => api('/vendor/options'))
  const [step, setStep] = useState<1 | 2>(1)
  const [code, setCode] = useState(sp.get('code') || '')
  const [f, setF] = useState({ name: '', email: '', venue_id: '', categories: [] as string[], description: '', schedule_note: '', instagram: '', website: '' })
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  async function check(e: React.FormEvent) {
    e.preventDefault(); setErr('')
    try { await api('/vendor/validate-code', { body: { code } }); setStep(2) } catch (e: any) { setErr(e.message) }
  }
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr(''); setBusy(true)
    try {
      const r = await api('/vendor/signup', { body: { code, ...f, venue_id: f.venue_id || undefined } })
      store.set('vendor', r.session_token)
      nav('/vendor', { replace: true })
    } catch (e: any) { setErr(e.message) } finally { setBusy(false) }
  }
  const toggleCat = (c: string) => setF((x) => ({ ...x, categories: x.categories.includes(c) ? x.categories.filter((y) => y !== c) : [...x.categories, c].slice(0, 4) }))

  return (
    <Shell>
      <h1 className="mt-10 font-serif text-[36px] font-medium">Join Brown Bag</h1>
      <p className="mt-2 text-soft">Free for vendors. Takes about two minutes.</p>
      {step === 1 ? (
        <form onSubmit={check} className="mt-6 flex flex-col gap-3">
          <label className="label" htmlFor="vj-code">Your invitation code</label>
          <input id="vj-code" className="field uppercase tracking-wider" required value={code} onChange={(e) => setCode(e.target.value)} placeholder="PIKEPILOT" />
          {err && <Notice kind="bad">{err}</Notice>}
          <button className="btn-primary self-start">Continue</button>
          <p className="hint">No code? <Link to="/for-vendors#ask" className="text-kraft">Ask for one</Link>.</p>
        </form>
      ) : (
        <form onSubmit={submit} className="mt-6 flex flex-col gap-5">
          <div><label className="label" htmlFor="vj-name">Business or stall name</label><input id="vj-name" className="field" required value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} placeholder="Lena Ruiz Jewelry" /></div>
          <div><label className="label" htmlFor="vj-email">Email</label><input id="vj-email" type="email" className="field" required value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /><p className="hint">This is how you sign in. We send one question a week, nothing else.</p></div>
          <div>
            <span className="label">What do you sell? (up to 4)</span>
            <div className="flex flex-wrap gap-2">
              {(opts?.categories || []).map((c: any) => (
                <button type="button" key={c.value} onClick={() => toggleCat(c.value)} className={`rounded-full border px-3 py-1.5 text-[14px] ${f.categories.includes(c.value) ? 'border-kraft bg-kraft text-white' : 'border-line bg-card text-ink'}`} aria-pressed={f.categories.includes(c.value)}>{c.label}</button>
              ))}
            </div>
          </div>
          <div>
            <label className="label" htmlFor="vj-venue">Where do you usually sell?</label>
            <select id="vj-venue" className="field" value={f.venue_id} onChange={(e) => setF({ ...f, venue_id: e.target.value })}>
              <option value="">Somewhere else / my own shop</option>
              {(opts?.venues || []).map((v: any) => <option key={v.id} value={v.id}>{v.name}</option>)}
            </select>
          </div>
          <div><label className="label" htmlFor="vj-desc">In a sentence, what do you make?</label><textarea id="vj-desc" className="field min-h-[80px]" value={f.description} onChange={(e) => setF({ ...f, description: e.target.value })} placeholder="Hammered silver necklaces and earrings, made at my kitchen table." /></div>
          <div><label className="label" htmlFor="vj-sched">When and where can people find you?</label><input id="vj-sched" className="field" value={f.schedule_note} onChange={(e) => setF({ ...f, schedule_note: e.target.value })} placeholder="Pike Place day stalls, usually Thu and Sat" /></div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div><label className="label" htmlFor="vj-ig">Instagram (optional)</label><input id="vj-ig" className="field" value={f.instagram} onChange={(e) => setF({ ...f, instagram: e.target.value })} placeholder="@yourshop" /></div>
            <div><label className="label" htmlFor="vj-web">Website (optional)</label><input id="vj-web" className="field" value={f.website} onChange={(e) => setF({ ...f, website: e.target.value })} /></div>
          </div>
          {err && <Notice kind="bad">{err}</Notice>}
          <button className="btn-primary self-start" disabled={busy}>{busy ? 'Setting up…' : 'Create my page'}</button>
        </form>
      )}
    </Shell>
  )
}

// ── The app ──────────────────────────────────────────────────────────────────

function VendorApp() {
  const [tab, setTab] = useState<Tab>(() => (window.location.hash.replace('#', '') as Tab) || 'talk')
  const me = useLoad(() => api('/vendor/me', { as: 'vendor' }))
  const nav = useNavigate()
  useEffect(() => { if (me.error && !store.get('vendor')) nav('/vendor', { replace: true }) }, [me.error, nav])
  useEffect(() => { try { window.history.replaceState(null, '', `#${tab}`) } catch { /* ignore */ } }, [tab])

  if (me.error) return <Shell><div className="mt-10"><Notice kind="bad">{me.error}</Notice><button className="btn-quiet mt-4" onClick={() => { store.clear('vendor'); window.location.reload() }}>Sign in again</button></div></Shell>
  if (!me.data) return <Shell><Spinner /></Shell>
  const v = me.data
  const tabs: [Tab, string][] = [['talk', 'This week'], ['stories', 'Stories'], ['reach', 'Readers'], ['share', 'Share'], ['profile', 'Profile']]
  return (
    <div className="min-h-screen bg-paper pb-24 sm:pb-10" style={{ paddingLeft: 'env(safe-area-inset-left,0px)', paddingRight: 'env(safe-area-inset-right,0px)' }}>
      <header className="sticky z-20 border-b border-line bg-paper/95 backdrop-blur" style={{ top: 'env(safe-area-inset-top,0px)' }}>
        <div className="wrap-narrow flex h-14 items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2"><BagMark size={20} /><span className="truncate font-semibold">{v.name}</span><SampleTag show={v.is_sample} /></div>
          <a href={v.page_url} target="_blank" rel="noreferrer" className="shrink-0 text-[13px] text-soft">My page ↗</a>
        </div>
        <nav className="wrap-narrow hidden gap-1 pb-2 sm:flex">
          {tabs.map(([k, l]) => <button key={k} onClick={() => setTab(k)} className={`rounded-md px-3 py-1.5 text-[14px] font-medium ${tab === k ? 'bg-ink text-card' : 'text-soft hover:text-ink'}`}>{l}</button>)}
        </nav>
      </header>
      <main className="wrap-narrow pt-6">
        {tab === 'talk' && <Talk me={v} goStories={() => setTab('stories')} />}
        {tab === 'stories' && <Stories me={v} />}
        {tab === 'reach' && <Reach />}
        {tab === 'share' && <ShareKit me={v} />}
        {tab === 'profile' && <Profile me={v} reload={me.reload} />}
      </main>
      <nav className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-5 border-t border-line bg-card sm:hidden" style={{ paddingBottom: 'env(safe-area-inset-bottom,0px)' }}>
        {tabs.map(([k, l]) => <button key={k} onClick={() => setTab(k)} className={`py-3 text-[12px] font-semibold ${tab === k ? 'text-kraft' : 'text-soft'}`}>{l}</button>)}
      </nav>
    </div>
  )
}

// ── This week: the interview ─────────────────────────────────────────────────

function Talk({ me, goStories }: { me: any; goStories: () => void }) {
  const conv = useLoad(() => api('/vendor/conversation', { as: 'vendor' }))
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)
  const [err, setErr] = useState('')
  const [pending, setPending] = useState<string | null>(null)
  const [drafting, setDrafting] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)
  const c = conv.data

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [c?.messages?.length, pending])
  useEffect(() => { if (c?.drafting) setDrafting(true) }, [c?.drafting])
  useEffect(() => {
    if (!drafting) return
    const id = setInterval(async () => {
      try {
        const r = await api('/vendor/stories', { as: 'vendor' })
        if (!r.drafts_in_progress) { setDrafting(false); clearInterval(id) }
      } catch { /* keep polling */ }
    }, 6000)
    return () => clearInterval(id)
  }, [drafting])

  async function send(e?: React.FormEvent) {
    e?.preventDefault()
    const t = text.trim()
    if (!t || sending) return
    setSending(true); setErr(''); setPending(t); setText('')
    try {
      const r = await api('/vendor/conversation/message', { as: 'vendor', body: { text: t } })
      conv.setData(r)
      if (r.drafting) setDrafting(true)
    } catch (e: any) { setErr(e.message); setText(t) } finally { setSending(false); setPending(null) }
  }
  async function startNew() {
    setErr('')
    try { conv.setData(await api('/vendor/conversation/new', { as: 'vendor', method: 'POST' })) } catch (e: any) { setErr(e.message) }
  }

  if (conv.error) return <Notice kind="bad">{conv.error}</Notice>
  if (!c) return <Spinner label="Getting this week's question" />

  return (
    <div className="flex flex-col gap-6">
      <QuickUpdate />
      <section>
        <p className="eyebrow mb-3">This week's conversation</p>
        <div className="card flex flex-col gap-2 p-4" aria-live="polite">
          {c.messages.map((m: any, i: number) => (
            <div key={i} className={`max-w-[88%] whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-[15px] leading-snug ${m.role === 'agent' ? 'self-start bg-paper' : 'self-end bg-ink text-card'}`}>{m.content}</div>
          ))}
          {pending && <div className="max-w-[88%] self-end whitespace-pre-wrap rounded-2xl bg-ink/80 px-3.5 py-2.5 text-[15px] text-card">{pending}</div>}
          {sending && <div className="self-start rounded-2xl bg-paper px-3.5 py-2.5 text-[15px] text-soft"><span className="animate-pulse">Thinking…</span></div>}
          <div ref={endRef} />
        </div>
        {!c.finished ? (
          <form onSubmit={send} className="mt-3 flex flex-col gap-2">
            <label htmlFor="talk-input" className="sr-only">Your answer</label>
            <textarea id="talk-input" className="field min-h-[84px]" value={text} onChange={(e) => setText(e.target.value)} placeholder="Type your answer. A line or two is plenty."
              onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) send() }} />
            <div className="flex flex-wrap items-center gap-2">
              <button className="btn-primary" disabled={sending || !text.trim()}>{sending ? 'Sending…' : 'Send'}</button>
              <button type="button" className="btn-ghost btn-sm" disabled={sending} onClick={() => { setText("That's all I've got this week."); }}>That's all for this week</button>
            </div>
            <p className="hint">You can leave and come back: the conversation waits for you.</p>
          </form>
        ) : (
          <div className="mt-4 flex flex-col gap-3">
            {c.escalated ? <Notice>Thank you for sharing this. An editor will read it personally before anything else happens.</Notice>
              : drafting ? <Notice><span className="inline-flex items-center gap-2"><span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-sky/30 border-t-sky" />Writing your draft. It usually takes about a minute, and you'll see it before anyone else.</span></Notice>
              : c.status === 'submitted' ? <Notice kind="good">Your draft is ready. <button className="font-semibold underline" onClick={goStories}>Read it and check the facts</button>.</Notice>
              : <Notice>No story this week, and that's fine. Some weeks are like that.</Notice>}
            <button className="btn-quiet self-start" onClick={startNew}>Tell us something else</button>
          </div>
        )}
        {err && <div className="mt-3"><Notice kind="bad">{err}</Notice></div>}
      </section>
    </div>
  )
}

function QuickUpdate() {
  const [open, setOpen] = useState(false)
  const [text, setText] = useState('')
  const [state, setState] = useState<'idle' | 'busy' | 'done'>('idle')
  const [err, setErr] = useState('')
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setState('busy'); setErr('')
    try { await api('/vendor/updates', { as: 'vendor', body: { text } }); setState('done'); setText('') } catch (e: any) { setErr(e.message); setState('idle') }
  }
  return (
    <section className="card p-4">
      <div className="flex items-center justify-between gap-3">
        <div><p className="font-semibold">Quick update</p><p className="text-[14px] text-soft">Where you'll be, what's new, a recipe. Goes in the next email.</p></div>
        {!open && <button className="btn-quiet btn-sm shrink-0" onClick={() => { setOpen(true); setState('idle') }}>Write one</button>}
      </div>
      {open && (state === 'done' ? (
        <div className="mt-3"><Notice kind="good">Got it. We'll tidy the wording and you'll see it under Stories in a minute.</Notice><button className="btn-ghost btn-sm mt-2" onClick={() => { setOpen(false); setState('idle') }}>Close</button></div>
      ) : (
        <form onSubmit={submit} className="mt-3 flex flex-col gap-2">
          <label htmlFor="qu-text" className="sr-only">Update</label>
          <textarea id="qu-text" className="field min-h-[80px]" required minLength={5} value={text} onChange={(e) => setText(e.target.value)} placeholder="North arcade Thursday and Saturday. Just finished a set of tiny moon pendants." />
          {err && <Notice kind="bad">{err}</Notice>}
          <div className="flex gap-2"><button className="btn-primary btn-sm" disabled={state === 'busy'}>{state === 'busy' ? 'Sending…' : 'Send update'}</button><button type="button" className="btn-ghost btn-sm" onClick={() => setOpen(false)}>Cancel</button></div>
        </form>
      ))}
    </section>
  )
}

// ── Stories ──────────────────────────────────────────────────────────────────

function Stories({ me }: { me: any }) {
  const { data, error, reload } = useLoad(() => api('/vendor/stories', { as: 'vendor' }))
  useEffect(() => {
    if (!data?.drafts_in_progress) return
    const id = setTimeout(reload, 7000)
    return () => clearTimeout(id)
  }, [data, reload])
  if (error) return <Notice kind="bad">{error}</Notice>
  if (!data) return <Spinner />
  const waiting = data.stories.filter((s: any) => s.status === 'vendor_preview')
  const rest = data.stories.filter((s: any) => s.status !== 'vendor_preview')
  return (
    <div className="flex flex-col gap-6">
      {data.drafts_in_progress > 0 && <Notice>Writing {data.drafts_in_progress === 1 ? 'a draft' : `${data.drafts_in_progress} drafts`} for you now. This page refreshes on its own.</Notice>}
      {waiting.length > 0 && (
        <section>
          <p className="eyebrow mb-3">Waiting for you to check</p>
          <div className="flex flex-col gap-4">{waiting.map((s: any) => <DraftCheck key={s.id} s={s} onDone={reload} />)}</div>
        </section>
      )}
      <section>
        <p className="eyebrow mb-3">All your stories and updates</p>
        {!rest.length && !waiting.length && <Notice>Nothing yet. Answer this week's question and your first draft shows up here.</Notice>}
        <div className="flex flex-col gap-3">{rest.map((s: any) => <StoryRow key={s.id} s={s} me={me} onChange={reload} />)}</div>
      </section>
      <Library />
    </div>
  )
}

function DraftCheck({ s, onDone }: { s: any; onDone: () => void }) {
  const [fixing, setFixing] = useState(false)
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  async function ok() {
    setBusy(true)
    try { await api(`/vendor/stories/${s.id}/approve`, { as: 'vendor', method: 'POST' }); onDone() } catch (e: any) { setErr(e.message) } finally { setBusy(false) }
  }
  async function fix(e: React.FormEvent) {
    e.preventDefault(); setBusy(true)
    try { await api(`/vendor/stories/${s.id}/correction`, { as: 'vendor', body: { note } }); onDone() } catch (e: any) { setErr(e.message) } finally { setBusy(false) }
  }
  return (
    <article className="card border-kraft/50 p-5">
      <span className="chip-warn">{s.kind === 'update' ? 'Update' : 'Story'} · please check</span>
      <h3 className="mt-3 font-serif text-[24px] font-medium leading-tight">{s.headline}</h3>
      <div className="mt-3"><Paras text={s.body} className="story-body [&>p]:text-[17px]" /></div>
      <p className="text-[14px] text-soft">Is everything here true? You're the only one who knows.</p>
      {!fixing ? (
        <div className="mt-3 flex flex-wrap gap-2">
          <button className="btn-primary" disabled={busy} onClick={ok}>Looks right</button>
          <button className="btn-quiet" onClick={() => setFixing(true)}>Something's wrong</button>
        </div>
      ) : (
        <form onSubmit={fix} className="mt-3 flex flex-col gap-2">
          <label className="label" htmlFor={`fix-${s.id}`}>What should it say instead?</label>
          <textarea id={`fix-${s.id}`} className="field min-h-[80px]" required value={note} onChange={(e) => setNote(e.target.value)} placeholder="It was the north arcade, not the south one." />
          <div className="flex gap-2"><button className="btn-primary btn-sm" disabled={busy}>Send to the editor</button><button type="button" className="btn-ghost btn-sm" onClick={() => setFixing(false)}>Cancel</button></div>
        </form>
      )}
      {err && <div className="mt-2"><Notice kind="bad">{err}</Notice></div>}
    </article>
  )
}

function StoryRow({ s, me, onChange }: { s: any; me: any; onChange: () => void }) {
  const [open, setOpen] = useState(false)
  const [note, setNote] = useState('')
  const [sent, setSent] = useState(false)
  const chip = s.status === 'approved' ? 'chip-good' : s.status === 'rejected' ? 'chip-bad' : 'chip'
  async function toggleVisibility() {
    await api(`/vendor/stories/${s.id}/visibility`, { as: 'vendor', body: { is_public: !s.is_public } }).catch(() => {})
    onChange()
  }
  async function correct(e: React.FormEvent) {
    e.preventDefault()
    await api(`/vendor/stories/${s.id}/correction`, { as: 'vendor', body: { note } }).then(() => { setSent(true); setNote('') }).catch(() => {})
  }
  return (
    <article className="card p-4">
      <button className="flex w-full items-start justify-between gap-3 text-left" onClick={() => setOpen(!open)} aria-expanded={open}>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2"><span className={chip}>{s.status_label}</span><span className="text-[12px] text-soft">{s.kind === 'update' ? 'Update' : 'Story'} · {timeAgo(s.created_at)}</span></div>
          <p className="mt-1.5 font-serif text-[19px] leading-snug">{s.headline}</p>
        </div>
        <span className="text-soft" aria-hidden="true">{open ? '−' : '+'}</span>
      </button>
      {open && (
        <div className="mt-3 border-t border-line pt-3">
          <Paras text={s.body} className="story-body [&>p]:text-[16px]" />
          {s.reject_reason && <Notice>Editor's note: {s.reject_reason}</Notice>}
          {s.corrections?.map((c: any, i: number) => <p key={i} className="text-[13px] text-soft">Your correction ({c.status}): {c.note}</p>)}
          {s.status === 'approved' && (
            <div className="mt-3 flex flex-col gap-3">
              {s.public_url && <CopyField value={s.public_url} label="Link to this story" />}
              {s.kind === 'story' && <InstagramKit s={s} me={me} />}
              <div className="flex flex-wrap gap-2">
                <button className="btn-quiet btn-sm" onClick={toggleVisibility}>{s.is_public ? 'Hide from the website' : 'Show on the website'}</button>
              </div>
              {sent ? <Notice kind="good">Sent. The editor will fix it, and the story won't go out again until they do.</Notice> : (
                <form onSubmit={correct} className="flex gap-2"><input className="field min-w-0 flex-1" placeholder="Spotted a mistake? Tell the editor" value={note} onChange={(e) => setNote(e.target.value)} aria-label="Correction" /><button className="btn-quiet btn-sm shrink-0" disabled={!note.trim()}>Send</button></form>
              )}
            </div>
          )}
        </div>
      )}
    </article>
  )
}

function wrapLines(ctx: CanvasRenderingContext2D, text: string, maxWidth: number) {
  const words = text.split(/\s+/)
  const lines: string[] = []
  let line = ''
  for (const w of words) {
    const test = line ? `${line} ${w}` : w
    if (ctx.measureText(test).width > maxWidth && line) { lines.push(line); line = w } else line = test
  }
  if (line) lines.push(line)
  return lines
}

function InstagramKit({ s, me }: { s: any; me: any }) {
  const [img, setImg] = useState('')
  useEffect(() => {
    let alive = true
    ;(async () => {
      try { await (document as any).fonts?.load?.('500 64px Newsreader') } catch { /* fallback font */ }
      const c = document.createElement('canvas')
      c.width = 1080; c.height = 1350
      const x = c.getContext('2d')!
      x.fillStyle = '#f6f1e8'; x.fillRect(0, 0, 1080, 1350)
      x.fillStyle = '#a86f37'; x.fillRect(0, 0, 1080, 18)
      x.fillStyle = '#a86f37'; x.font = '600 30px "Plus Jakarta Sans", sans-serif'
      x.fillText('BROWN BAG · THIS WEEK', 90, 150)
      x.fillStyle = '#231d17'; x.font = '500 84px Newsreader, Georgia, serif'
      let y = 280
      for (const l of wrapLines(x, s.headline, 900).slice(0, 5)) { x.fillText(l, 90, y); y += 98 }
      y += 30
      x.font = '400 40px Newsreader, Georgia, serif'; x.fillStyle = '#3d342b'
      const first = (s.body || '').split('\n').find((p: string) => p.trim()) || ''
      for (const l of wrapLines(x, first, 900).slice(0, 7)) { x.fillText(l, 90, y); y += 58 }
      x.fillStyle = '#231d17'; x.font = '600 38px "Plus Jakarta Sans", sans-serif'
      x.fillText(me.name, 90, 1190)
      x.fillStyle = '#6f6253'; x.font = '400 30px "Plus Jakarta Sans", sans-serif'
      x.fillText('Read the whole story · link in bio', 90, 1245)
      if (alive) setImg(c.toDataURL('image/png'))
    })()
    return () => { alive = false }
  }, [s, me])
  return (
    <div className="rounded-lg bg-paper p-3">
      <p className="text-[14px] font-semibold">Post it on Instagram</p>
      <div className="mt-2 flex flex-col gap-3 sm:flex-row">
        {img && <img src={img} alt="Instagram post for this story" className="w-40 rounded border border-line" />}
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <textarea className="field min-h-[120px] text-[13px]" readOnly value={s.instagram_caption} aria-label="Instagram caption" />
          <div className="flex flex-wrap gap-2">
            <CopyButton text={s.instagram_caption} label="Copy caption" />
            {img && <a href={img} download={`brown-bag-${s.slug}.png`} className="btn-quiet btn-sm no-underline">Save image</a>}
          </div>
        </div>
      </div>
    </div>
  )
}

function Library() {
  const { data } = useLoad(() => api('/vendor/library', { as: 'vendor' }))
  if (!data?.length) return null
  return (
    <section>
      <p className="eyebrow mb-1">What other vendors shared</p>
      <p className="mb-3 text-[14px] text-soft">Small things make good stories. A sellout, a split tomato crop, a customer who came back.</p>
      <div className="flex flex-col gap-2">
        {data.slice(0, 6).map((s: any) => (
          <a key={s.id} href={`/s/${s.slug}`} target="_blank" rel="noreferrer" className="card block p-3 no-underline hover:border-kraft">
            <span className="text-[12px] font-semibold text-kraftdeep">{s.vendor?.name}</span>
            <span className="block font-serif text-[17px] text-ink">{s.headline}</span>
          </a>
        ))}
      </div>
    </section>
  )
}

// ── Readers ──────────────────────────────────────────────────────────────────

function Reach() {
  const { data, error } = useLoad(() => api('/vendor/stats', { as: 'vendor' }))
  if (error) return <Notice kind="bad">{error}</Notice>
  if (!data) return <Spinner />
  const tiles: [string, number][] = [['People following you', data.followers], ['New this week', data.new_followers_7], ['Story clicks, 30 days', data.clicks_30], ['QR scans, 30 days', data.scans_30], ['Approved stories', data.stories], ['Times your news was sent', data.times_sent]]
  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {tiles.map(([k, v]) => <div key={k} className="card p-4"><p className="num text-[30px] font-semibold">{v}</p><p className="text-[13px] leading-snug text-soft">{k}</p></div>)}
      </div>
      <p className="text-[13px] text-soft">These numbers are only for you. We don't rank vendors against each other.</p>
      <section>
        <p className="eyebrow mb-3">What readers made with your things</p>
        {!data.reader_shares.length && <Notice>Nothing yet. When a reader sends a photo of what they made with something of yours, it shows up here.</Notice>}
        <div className="flex flex-col gap-3">
          {data.reader_shares.map((s: any) => (
            <figure key={s.id} className="card p-4">
              {s.image_url && <img src={mediaUrl(s.image_url)} alt="" className="mb-2 max-h-72 w-full rounded-lg object-cover" />}
              <blockquote className="font-serif text-[17px]">“{s.text}”</blockquote>
              <figcaption className="mt-1 text-[13px] text-soft">— {s.reader_name || 'A reader'} · {timeAgo(s.created_at)} {s.status === 'approved' ? '· featured' : ''}</figcaption>
            </figure>
          ))}
        </div>
      </section>
    </div>
  )
}

// ── Share kit ────────────────────────────────────────────────────────────────

function ShareKit({ me }: { me: any }) {
  const regulars = `Hi! I'm now in Brown Bag, a free weekly email about Seattle market vendors. Follow me there and you'll know where I'll be each week and what's new: ${me.page_url}`
  const neighbor = `I've been using Brown Bag: it's free, they ask me a question a week and write a short story for people who follow me. You'd be great in it. ${window.location.origin}/for-vendors`
  return (
    <div className="flex flex-col gap-6">
      <section className="card flex flex-col items-center p-6 text-center">
        <p className="font-semibold">Your QR code</p>
        <p className="mt-1 text-[14px] text-soft">Customers scan it, type their email once, and follow you.</p>
        <QR value={me.qr_url} size={200} className="mt-4" />
        <p className="mt-2 break-all font-mono text-[12px] text-soft">{me.page_url.replace(/^https?:\/\//, '')}</p>
        <Link to="/vendor/card" className="btn-primary mt-4 no-underline">Print a table card</Link>
      </section>
      <section className="card p-5">
        <p className="font-semibold">Bring your regulars</p>
        <p className="mt-1 text-[14px] text-soft">Send this to your mailing list, post it, or text it to customers who ask how to keep up with you.</p>
        <textarea className="field mt-3 min-h-[100px] text-[14px]" readOnly value={regulars} aria-label="Message for your regulars" />
        <div className="mt-2"><CopyButton text={regulars} label="Copy message" /></div>
      </section>
      <section className="card p-5">
        <p className="font-semibold">Invite a neighbor vendor</p>
        <p className="mt-1 text-[14px] text-soft">The more vendors from your market join, the more readers find you.</p>
        <textarea className="field mt-3 min-h-[90px] text-[14px]" readOnly value={neighbor} aria-label="Message for another vendor" />
        <div className="mt-2"><CopyButton text={neighbor} label="Copy message" /></div>
      </section>
      {me.venue && <p className="text-[14px] text-soft">Your market also has a shared code at {me.venue.name}, listing every vendor there: <a href={me.venue_qr_url} target="_blank" rel="noreferrer" className="text-kraft">open it</a>.</p>}
    </div>
  )
}

export function VendorCard() {
  const { data, error } = useLoad(() => api('/vendor/me', { as: 'vendor' }))
  if (error) return <Shell><Notice kind="bad">{error}</Notice></Shell>
  if (!data) return <Shell><Spinner /></Shell>
  return (
    <div className="min-h-screen bg-white p-6">
      <div className="no-print mx-auto mb-6 flex max-w-xl gap-2"><button className="btn-primary" onClick={() => window.print()}>Print</button><Link to="/vendor#share" className="btn-quiet no-underline">Back</Link></div>
      <div className="mx-auto flex max-w-[420px] flex-col items-center rounded-2xl border-2 border-ink p-8 text-center">
        <div className="flex items-center gap-2"><BagMark size={28} /><span className="font-serif text-[28px] font-semibold">Brown Bag</span></div>
        <p className="mt-6 font-serif text-[30px] font-medium leading-tight">Follow {data.name}</p>
        <p className="mt-2 text-[16px] text-soft">Where we'll be each week, what's new, and the stories behind it. One free email a week.</p>
        <QR value={data.qr_url} size={240} className="mt-6" />
        <p className="mt-4 text-[14px] font-semibold">Scan with your phone camera</p>
        <p className="mt-1 font-mono text-[12px] text-soft">{data.page_url.replace(/^https?:\/\//, '')}</p>
      </div>
    </div>
  )
}

// ── Profile ──────────────────────────────────────────────────────────────────

function Profile({ me, reload }: { me: any; reload: () => void }) {
  const [f, setF] = useState({ name: me.name || '', description: me.description || '', schedule_note: me.schedule_note || '', instagram: me.instagram || '', website: me.website || '' })
  const [cats, setCats] = useState<string[]>(me.categories || [])
  const [msg, setMsg] = useState<{ kind: 'good' | 'bad'; text: string } | null>(null)
  const [busy, setBusy] = useState(false)
  async function save(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setMsg(null)
    try { await api('/vendor/me', { as: 'vendor', method: 'PATCH', body: { ...f, categories: cats } }); setMsg({ kind: 'good', text: 'Saved.' }); reload() } catch (e: any) { setMsg({ kind: 'bad', text: e.message }) } finally { setBusy(false) }
  }
  async function photo(file?: File) {
    if (!file) return
    setBusy(true)
    try { const url = await uploadPhoto(file, 'vendor'); await api('/vendor/me', { as: 'vendor', method: 'PATCH', body: { photo_url: url } }); reload() } catch (e: any) { setMsg({ kind: 'bad', text: e.message }) } finally { setBusy(false) }
  }
  return (
    <form onSubmit={save} className="flex flex-col gap-5">
      <div className="flex items-center gap-4">
        <Avatar name={me.name} url={me.photo_url} size={64} />
        <label className="btn-quiet btn-sm cursor-pointer">Change photo<input type="file" accept="image/*" className="sr-only" onChange={(e) => photo(e.target.files?.[0])} /></label>
      </div>
      <div><label className="label" htmlFor="p-name">Business or stall name</label><input id="p-name" className="field" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></div>
      <div><label className="label" htmlFor="p-desc">What you make</label><textarea id="p-desc" className="field min-h-[80px]" value={f.description} onChange={(e) => setF({ ...f, description: e.target.value })} /></div>
      <div><label className="label" htmlFor="p-sched">When and where to find you</label><input id="p-sched" className="field" value={f.schedule_note} onChange={(e) => setF({ ...f, schedule_note: e.target.value })} /></div>
      <div>
        <span className="label">What you sell</span>
        <div className="flex flex-wrap gap-2">
          {Object.entries(CATEGORY_LABEL).map(([k, l]) => (
            <button type="button" key={k} aria-pressed={cats.includes(k)} onClick={() => setCats((c) => c.includes(k) ? c.filter((x) => x !== k) : [...c, k].slice(0, 4))} className={`rounded-full border px-3 py-1.5 text-[14px] ${cats.includes(k) ? 'border-kraft bg-kraft text-white' : 'border-line bg-card'}`}>{l}</button>
          ))}
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div><label className="label" htmlFor="p-ig">Instagram</label><input id="p-ig" className="field" value={f.instagram} onChange={(e) => setF({ ...f, instagram: e.target.value })} /></div>
        <div><label className="label" htmlFor="p-web">Website</label><input id="p-web" className="field" value={f.website} onChange={(e) => setF({ ...f, website: e.target.value })} /></div>
      </div>
      {msg && <Notice kind={msg.kind}>{msg.text}</Notice>}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button className="btn-primary" disabled={busy}>Save</button>
        <button type="button" className="btn-ghost btn-sm" onClick={() => { store.clear('vendor'); window.location.href = '/vendor' }}>Sign out</button>
      </div>
      <p className="text-[13px] text-soft">Signed in as {me.email}.</p>
    </form>
  )
}
