import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, API, mediaUrl, store, timeAgo, CATEGORY_LABEL } from '../../lib/api'
import { BagMark, CopyButton, CopyField, Notice, QR, SampleTag, Spinner, useLoad } from '../../ui/kit'

type Tab = 'overview' | 'review' | 'issue' | 'vendors' | 'markets' | 'readers' | 'inbox' | 'skills' | 'settings'
const TABS: [Tab, string][] = [
  ['overview', 'Overview'], ['review', 'Review'], ['issue', 'This week’s issue'], ['vendors', 'Vendors'],
  ['markets', 'Markets & codes'], ['readers', 'Readers'], ['inbox', 'Inbox'], ['skills', 'Skills'], ['settings', 'Settings'],
]

export default function EditorHome() {
  const [authed, setAuthed] = useState(!!store.get('editor'))
  return authed ? <EditorApp onSignOut={() => { store.clear('editor'); setAuthed(false) }} /> : <EditorLogin onIn={() => setAuthed(true)} />
}

function EditorLogin({ onIn }: { onIn: () => void }) {
  const { data: status } = useLoad(() => api('/editor/setup-status'))
  const [f, setF] = useState({ email: '', password: '', name: '', code: '' })
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const setup = status?.needs_setup
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr(''); setBusy(true)
    try {
      const r = setup ? await api('/editor/setup', { body: f }) : await api('/editor/login', { body: { email: f.email, password: f.password } })
      store.set('editor', r.token); onIn()
    } catch (e: any) { setErr(e.message) } finally { setBusy(false) }
  }
  return (
    <div className="min-h-screen bg-paper">
      <div className="wrap-narrow max-w-md pt-16">
        <Link to="/" className="inline-flex items-center gap-2 no-underline"><BagMark /><span className="font-serif text-[20px] font-semibold text-ink">Brown Bag</span><span className="text-[13px] text-soft">editor</span></Link>
        <h1 className="mt-10 font-serif text-[34px] font-medium">{setup ? 'Set up the first editor' : 'Editor sign in'}</h1>
        {setup && <p className="mt-2 text-soft">Use the setup code you were given. This page only works until the first editor exists.</p>}
        <form onSubmit={submit} className="mt-6 flex flex-col gap-4">
          {setup && <div><label className="label" htmlFor="ed-code">Setup code</label><input id="ed-code" className="field" required value={f.code} onChange={(e) => setF({ ...f, code: e.target.value })} /></div>}
          {setup && <div><label className="label" htmlFor="ed-name">Your name (signs the weekly greeting)</label><input id="ed-name" className="field" required value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></div>}
          <div><label className="label" htmlFor="ed-email">Email</label><input id="ed-email" type="email" className="field" required autoComplete="username" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></div>
          <div><label className="label" htmlFor="ed-pw">Password{setup ? ' (8+ characters)' : ''}</label><input id="ed-pw" type="password" className="field" required minLength={setup ? 8 : 1} autoComplete={setup ? 'new-password' : 'current-password'} value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} /></div>
          {err && <Notice kind="bad">{err}</Notice>}
          <button className="btn-primary self-start" disabled={busy || !status}>{setup ? 'Create editor account' : 'Sign in'}</button>
        </form>
      </div>
    </div>
  )
}

function EditorApp({ onSignOut }: { onSignOut: () => void }) {
  const [tab, setTab] = useState<Tab>(() => (window.location.hash.replace('#', '') as Tab) || 'overview')
  const me = useLoad(() => api('/editor/me', { as: 'editor' }))
  useEffect(() => { try { window.history.replaceState(null, '', `#${tab}`) } catch { /* ignore */ } }, [tab])
  useEffect(() => { if (me.error && !store.get('editor')) onSignOut() }, [me.error, onSignOut])
  return (
    <div className="min-h-screen bg-paper" style={{ paddingLeft: 'env(safe-area-inset-left,0px)', paddingRight: 'env(safe-area-inset-right,0px)' }}>
      <header className="sticky z-20 border-b border-line bg-paper/95 backdrop-blur" style={{ top: 'env(safe-area-inset-top,0px)' }}>
        <div className="wrap flex h-14 items-center justify-between gap-3">
          <Link to="/" className="flex items-center gap-2 no-underline"><BagMark size={20} /><span className="font-serif text-[19px] font-semibold text-ink">Brown Bag</span><span className="text-[13px] text-soft">editor</span></Link>
          <div className="flex items-center gap-3 text-[14px] text-soft"><span className="hidden sm:inline">{me.data?.name}</span><button className="btn-ghost btn-sm" onClick={onSignOut}>Sign out</button></div>
        </div>
      </header>
      <div className="wrap grid gap-6 py-6 lg:grid-cols-[200px_1fr]">
        <nav className="lg:sticky lg:top-20 lg:self-start">
          <select className="field lg:hidden" value={tab} onChange={(e) => setTab(e.target.value as Tab)} aria-label="Section">
            {TABS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </select>
          <ul className="hidden flex-col gap-0.5 lg:flex">
            {TABS.map(([k, l]) => <li key={k}><button onClick={() => setTab(k)} className={`w-full rounded-md px-3 py-2 text-left text-[14px] font-medium ${tab === k ? 'bg-ink text-card' : 'text-soft hover:bg-card hover:text-ink'}`}>{l}</button></li>)}
          </ul>
        </nav>
        <main className="min-w-0">
          {tab === 'overview' && <Overview go={setTab} />}
          {tab === 'review' && <Review />}
          {tab === 'issue' && <IssueTab editorName={me.data?.name} />}
          {tab === 'vendors' && <Vendors />}
          {tab === 'markets' && <Markets />}
          {tab === 'readers' && <Readers />}
          {tab === 'inbox' && <Inbox />}
          {tab === 'skills' && <Skills />}
          {tab === 'settings' && <Settings />}
        </main>
      </div>
    </div>
  )
}

function H({ title, sub, right }: { title: string; sub?: string; right?: React.ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div><h1 className="font-serif text-[30px] font-medium leading-tight">{title}</h1>{sub && <p className="mt-1 max-w-prose text-[15px] text-soft">{sub}</p>}</div>
      {right}
    </div>
  )
}

// ── Overview ─────────────────────────────────────────────────────────────────

function Overview({ go }: { go: (t: Tab) => void }) {
  const { data, error } = useLoad(() => api('/editor/overview', { as: 'editor' }))
  if (error) return <Notice kind="bad">{error}</Notice>
  if (!data) return <Spinner />
  const todo: [number, string, Tab][] = [
    [data.pending_review, 'drafts to review', 'review'], [data.open_corrections, 'vendor corrections', 'review'],
    [data.pending_shares, 'reader photos to approve', 'review'], [data.new_leads, 'new inquiries', 'inbox'], [data.new_nominations, 'shop nominations', 'inbox'],
  ]
  return (
    <div>
      <H title="Overview" sub={data.diagnosis} />
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[['Readers', data.readers, `+${data.new_readers_7} this week`], ['Vendors', data.vendors, data.sample_vendors ? `${data.sample_vendors} sample` : ''],
          ['Approved stories', data.approved_stories, `${data.new_stories_7} new this week`], ['Clicks, 7 days', data.clicks_7, `${data.issues_sent} issues sent`]].map(([k, v, s]) => (
          <div key={k as string} className="card p-4"><p className="num text-[30px] font-semibold">{v as number}</p><p className="text-[13px] text-soft">{k}</p>{s && <p className="mt-1 text-[12px] text-kraftdeep">{s}</p>}</div>
        ))}
      </div>
      <div className="card mt-6 p-5">
        <p className="font-semibold">To do</p>
        <ul className="mt-2 flex flex-col">
          {todo.map(([n, label, t]) => (
            <li key={label} className="flex items-center justify-between border-t border-line py-2.5 first:border-0">
              <span className={n ? 'text-ink' : 'text-soft'}><b className="num">{n}</b> {label}</span>
              {n > 0 && <button className="btn-quiet btn-sm" onClick={() => go(t)}>Open</button>}
            </li>
          ))}
          <li className="flex items-center justify-between border-t border-line py-2.5"><span><b className="num">{data.waiting_on_vendor}</b> drafts waiting for the vendor to check</span><button className="btn-ghost btn-sm" onClick={() => go('review')}>See them</button></li>
        </ul>
      </div>
      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        <button className="card p-4 text-left hover:border-kraft" onClick={() => go('vendors')}><p className="font-semibold">Send this week's questions</p><p className="text-[13px] text-soft">Email every vendor their question and login link.</p></button>
        <button className="card p-4 text-left hover:border-kraft" onClick={() => go('issue')}><p className="font-semibold">Put together the issue</p><p className="text-[13px] text-soft">Write the greeting, preview, send.</p></button>
        <button className="card p-4 text-left hover:border-kraft" onClick={() => go('markets')}><p className="font-semibold">Market reports</p><p className="text-[13px] text-soft">Share the live report with a market.</p></button>
      </div>
    </div>
  )
}

// ── Review queue ─────────────────────────────────────────────────────────────

function Review() {
  const { data, error, reload } = useLoad(() => api('/editor/queue', { as: 'editor' }))
  if (error) return <Notice kind="bad">{error}</Notice>
  if (!data) return <Spinner />
  return (
    <div className="flex flex-col gap-10">
      <section>
        <H title="Drafts to review" sub="The vendor has checked these. Edit, score, approve. Approved pieces go into the bank for the next issue." />
        {!data.drafts.length && <Notice>Nothing waiting. Nice.</Notice>}
        <div className="flex flex-col gap-4">{data.drafts.map((d: any) => <DraftEditor key={d.id} d={d} onDone={reload} />)}</div>
      </section>
      {data.corrections.length > 0 && (
        <section>
          <H title="Corrections on published pieces" sub="A vendor flagged a wrong fact. The piece is held back from issues until you resolve it." />
          <div className="flex flex-col gap-4">{data.corrections.map((c: any) => (
            <div key={c.id} className="card p-4">
              <Notice>“{c.note}” — {c.block?.vendor?.name}</Notice>
              <div className="mt-3"><DraftEditor d={c.block} onDone={reload} correctionId={c.id} /></div>
            </div>
          ))}</div>
        </section>
      )}
      {data.escalations.length > 0 && (
        <section>
          <H title="Needs a person first" sub="Sensitive material. Nothing was drafted automatically. Read it, then decide." />
          <div className="flex flex-col gap-4">{data.escalations.map((s: any) => <Escalation key={s.id} s={s} onDone={reload} />)}</div>
        </section>
      )}
      <section>
        <H title="Reader photos" sub="Approved ones can appear under “Readers made this” in the issue and on the vendor's page." />
        {!data.shares.length && <Notice>No new reader photos.</Notice>}
        <div className="grid gap-4 md:grid-cols-2">{data.shares.map((s: any) => (
          <div key={s.id} className="card p-4">
            {s.image_url && <img src={mediaUrl(s.image_url)} alt="" className="mb-2 max-h-64 w-full rounded-lg object-cover" />}
            <p className="font-serif text-[17px]">“{s.text}”</p>
            <p className="mt-1 text-[13px] text-soft">— {s.reader_name || 'no name'} {s.email ? `(${s.email})` : ''} · {s.vendor?.name || 'no vendor'} · {timeAgo(s.created_at)}</p>
            <div className="mt-3 flex gap-2">
              <button className="btn-primary btn-sm" onClick={() => api(`/editor/shares/${s.id}`, { as: 'editor', body: { action: 'approve' } }).then(reload)}>Approve</button>
              <button className="btn-quiet btn-sm" onClick={() => api(`/editor/shares/${s.id}`, { as: 'editor', body: { action: 'reject' } }).then(reload)}>Skip</button>
            </div>
          </div>
        ))}</div>
      </section>
      {data.with_vendor.length > 0 && (
        <section>
          <H title="Waiting on the vendor" sub="Drafts the vendor hasn't checked yet. You can approve one directly if you've confirmed the facts with them." />
          <div className="flex flex-col gap-4">{data.with_vendor.map((d: any) => <DraftEditor key={d.id} d={d} onDone={reload} />)}</div>
        </section>
      )}
    </div>
  )
}

function DraftEditor({ d, onDone, correctionId }: { d: any; onDone: () => void; correctionId?: string }) {
  const [headline, setHeadline] = useState(d.headline || '')
  const [body, setBody] = useState(d.body || '')
  const [q, setQ] = useState<number>(d.quality_score || 25)
  const [pub, setPub] = useState<boolean>(d.is_public ?? true)
  const [reason, setReason] = useState('')
  const [vendorLine, setVendorLine] = useState('')
  const [rejecting, setRejecting] = useState(false)
  const [showRaw, setShowRaw] = useState(false)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const words = body.split(/\s+/).filter(Boolean).length
  async function act(action: string) {
    setBusy(true); setErr('')
    try {
      await api(`/editor/blocks/${d.id}`, { as: 'editor', method: 'PATCH', body: { headline, body, quality_score: q, is_public: pub, action, reject_reason: reason || undefined, editor_note: action === 'approve' && vendorLine.trim() ? vendorLine.trim() : undefined } })
      if (correctionId && action === 'approve') await api(`/editor/corrections/${correctionId}`, { as: 'editor', body: { action: 'resolve' } })
      onDone()
    } catch (e: any) { setErr(e.message) } finally { setBusy(false) }
  }
  const g = d.guard
  return (
    <article className="card p-5">
      <div className="mb-3 flex flex-wrap items-center gap-2 text-[13px]">
        <span className="font-semibold text-kraftdeep">{d.vendor?.name}</span>
        <span className="chip">{d.kind === 'update' ? 'Update' : 'Story'}</span>
        <SampleTag show={d.is_sample} />
        {g && <span className={g.pass ? 'chip-good' : 'chip-bad'}>Style check {g.pass ? 'passed' : 'flagged'}</span>}
        <span className="text-soft">{timeAgo(d.created_at)}</span>
      </div>
      {d.corrections?.length > 0 && <div className="mb-3">{d.corrections.map((c: any) => <Notice key={c.id}>Vendor says: “{c.note}”</Notice>)}</div>}
      <Brief d={d} />
      {g && !g.pass && <div className="mb-3"><Notice kind="bad">{g.notes}{g.invented_facts?.length ? ` Not in the conversation: ${g.invented_facts.join('; ')}` : ''}</Notice></div>}
      <label className="label" htmlFor={`h-${d.id}`}>Headline <span className="font-normal text-soft">({headline.length}/60)</span></label>
      <input id={`h-${d.id}`} className="field font-serif text-[20px]" value={headline} onChange={(e) => setHeadline(e.target.value)} />
      <label className="label mt-4" htmlFor={`b-${d.id}`}>Text <span className="font-normal text-soft">({words} words)</span></label>
      <textarea id={`b-${d.id}`} className="field min-h-[220px] font-serif text-[17px] leading-relaxed" value={body} onChange={(e) => setBody(e.target.value)} />
      {d.raw_text && (
        <div className="mt-3">
          <button className="text-[13px] font-semibold text-kraft" onClick={() => setShowRaw(!showRaw)} aria-expanded={showRaw}>{showRaw ? 'Hide' : 'Show'} the conversation it came from</button>
          {showRaw && <pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap rounded-lg bg-paper p-3 text-[13px] leading-relaxed">{d.raw_text}</pre>}
        </div>
      )}
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <label className="label" htmlFor={`q-${d.id}`}>Quality: <span className="num">{q}</span>/40</label>
          <input id={`q-${d.id}`} type="range" min={0} max={40} value={q} onChange={(e) => setQ(+e.target.value)} className="w-full accent-[#a86f37]" />
          <p className="hint">Below 15 never ships. 25 is a solid story; 35+ leads the issue. The lead story runs in full; a second story shows its opening with a link.</p>
        </div>
        <label className="flex items-start gap-2 text-[14px]"><input type="checkbox" className="mt-1 h-4 w-4 accent-[#a86f37]" checked={pub} onChange={(e) => setPub(e.target.checked)} /><span>Show on the public website after approval. Turn off for anything personal.</span></label>
      </div>
      {err && <div className="mt-3"><Notice kind="bad">{err}</Notice></div>}
      {!rejecting && d.kind !== 'update' && !d.is_sample && (
        <div className="mt-4">
          <label className="label" htmlFor={`vl-${d.id}`}>A line for the vendor <span className="font-normal text-soft">(optional)</span></label>
          <input id={`vl-${d.id}`} className="field" maxLength={300} value={vendorLine} onChange={(e) => setVendorLine(e.target.value)} placeholder="The line about the hand dryer is why this one works." />
          <p className="hint">When you approve, they get an email saying it's running, with this line in it. Say something specific about their story.</p>
        </div>
      )}
      {!rejecting ? (
        <div className="mt-4 flex flex-wrap gap-2">
          <button className="btn-primary" disabled={busy} onClick={() => act('approve')}>{correctionId ? 'Fix and approve' : 'Approve'}</button>
          <button className="btn-quiet" disabled={busy} onClick={() => act('save')}>Save edits</button>
          <button className="btn-ghost" disabled={busy} onClick={() => setRejecting(true)}>Don't run it</button>
          {correctionId && <button className="btn-ghost" onClick={() => api(`/editor/corrections/${correctionId}`, { as: 'editor', body: { action: 'dismiss' } }).then(onDone)}>Dismiss correction</button>}
        </div>
      ) : (
        <div className="mt-4 flex flex-col gap-2">
          <input className="field" placeholder="Short note for the vendor (optional)" value={reason} onChange={(e) => setReason(e.target.value)} aria-label="Reason" />
          <div className="flex gap-2"><button className="btn-danger btn-sm" disabled={busy} onClick={() => act('reject')}>Don't run it</button><button className="btn-ghost btn-sm" onClick={() => setRejecting(false)}>Cancel</button></div>
        </div>
      )}
    </article>
  )
}

const RUBRIC: [string, string][] = [
  ['scene', 'Scene'], ['person', 'Person'], ['stakes', 'Stakes'], ['turn', 'Turn'], ['voice', 'Voice'],
  ['place', 'Place'], ['truthfulness', 'Truthful'], ['plainness', 'Plain'], ['pull', 'Pull'],
]

function Brief({ d }: { d: any }) {
  const g = d.guard || {}
  const b = g.brief
  const claims: any[] = d.claims || []
  const bad = claims.filter((c) => c.status === 'unsupported')
  const vc = g.vendor_check
  const rushed = !!vc && vc.changes === 0 && typeof vc.seconds === 'number' && vc.seconds < 20 && !vc.read_full
  if (!b && !claims.length && !d.revisions) return null
  return (
    <div className="mb-4 rounded-lg border border-line bg-paper p-4 text-[14px]">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-semibold">Before you read</span>
        {b?.verdict && <span className={b.verdict === 'run' ? 'chip-good' : b.verdict === 'hold' ? 'chip-bad' : 'chip-warn'}>{b.verdict === 'run' ? 'Ready to run' : b.verdict === 'hold' ? 'Hold: thin material' : 'Needs a light edit'}</span>}
        {b?.lead_worthy && <span className="chip-good">Could lead the issue</span>}
        {g.claims_total > 0 && <span className="chip">{g.claims_supported}/{g.claims_total} claims trace to the vendor’s words</span>}
        {g.vendor_confirmed > 0 && <span className="chip-good">Vendor confirmed {g.vendor_confirmed} claims</span>}
        {vc?.read_full && <span className="chip-good">Vendor read or listened to the whole story</span>}
        {rushed && <span className="chip-warn">Vendor confirmed everything in {vc.seconds}s without opening the story. Worth a closer look.</span>}
        {d.revisions > 0 && <span className="chip">Revised {d.revisions}× after the vendor’s changes</span>}
      </div>
      {b?.scores && (
        <dl className="mt-3 grid grid-cols-3 gap-x-4 gap-y-1 sm:grid-cols-5" aria-label="Rubric scores out of 4">
          {RUBRIC.map(([k, label]) => (
            <div key={k} className="flex items-baseline justify-between gap-2"><dt className="text-soft">{label}</dt><dd className={`num font-semibold ${b.scores[k] <= 2 ? 'text-rust' : ''}`}>{b.scores[k] ?? '–'}<span className="font-normal text-soft">/4</span></dd></div>
          ))}
        </dl>
      )}
      {b?.whats_missing && <p className="mt-3"><b>Missing:</b> {b.whats_missing}</p>}
      {b?.strongest_quotes?.length > 0 && <p className="mt-1"><b>Best lines:</b> {b.strongest_quotes.map((q: string) => `“${q}”`).join('  ')}</p>}
      {bad.length > 0 && <p className="mt-2 text-rust"><b>Not found in the conversation:</b> {bad.map((c) => c.text).join('; ')}</p>}
      {claims.length > 0 && (
        <details className="mt-2">
          <summary className="cursor-pointer font-semibold text-kraft">Claim by claim</summary>
          <ul className="mt-2 flex flex-col gap-1.5">
            {claims.map((c, i) => (
              <li key={i} className="text-[13px] leading-snug">
                <span className={c.status === 'unsupported' ? 'chip-bad' : c.status === 'inferred' ? 'chip-warn' : 'chip-good'}>{c.status}</span>{' '}
                {c.text}{c.evidence ? <span className="text-soft"> — “{c.evidence}”</span> : null}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}

function Escalation({ s, onDone }: { s: any; onDone: () => void }) {
  const [writing, setWriting] = useState(false)
  const [headline, setHeadline] = useState('')
  const [body, setBody] = useState('')
  return (
    <div className="card p-5">
      <p className="text-[13px] font-semibold text-kraftdeep">{s.vendor?.name} · {timeAgo(s.created_at)}</p>
      <pre className="mt-2 max-h-80 overflow-auto whitespace-pre-wrap rounded-lg bg-paper p-3 text-[14px] leading-relaxed">{s.raw_text}</pre>
      {!writing ? (
        <div className="mt-3 flex flex-wrap gap-2">
          <button className="btn-quiet btn-sm" onClick={() => setWriting(true)}>Write it myself</button>
          <button className="btn-quiet btn-sm" onClick={() => api(`/editor/submissions/${s.id}`, { as: 'editor', body: { action: 'draft' } }).then(onDone)}>Let the writer draft it</button>
          <button className="btn-ghost btn-sm" onClick={() => api(`/editor/submissions/${s.id}`, { as: 'editor', body: { action: 'discard' } }).then(onDone)}>Set aside</button>
        </div>
      ) : (
        <div className="mt-3 flex flex-col gap-2">
          <input className="field" placeholder="Headline" value={headline} onChange={(e) => setHeadline(e.target.value)} aria-label="Headline" />
          <textarea className="field min-h-[160px] font-serif" placeholder="Story" value={body} onChange={(e) => setBody(e.target.value)} aria-label="Story" />
          <div className="flex gap-2">
            <button className="btn-primary btn-sm" disabled={!headline || !body} onClick={() => api('/editor/blocks', { as: 'editor', body: { vendor_id: s.vendor?.id, headline, body, submission_id: s.id } }).then(onDone)}>Send to the vendor to check</button>
            <button className="btn-ghost btn-sm" onClick={() => setWriting(false)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  )
}

// ── The issue ────────────────────────────────────────────────────────────────

function IssueTab({ editorName }: { editorName?: string }) {
  const iss = useLoad(() => api('/editor/issue', { as: 'editor' }))
  const [f, setF] = useState({ subject: '', greeting: '', editor_name: '' })
  const [html, setHtml] = useState('')
  const [asEmail, setAsEmail] = useState('')
  const [testTo, setTestTo] = useState('')
  const [msg, setMsg] = useState<{ kind: 'good' | 'bad' | 'info'; text: string } | null>(null)
  const [confirm, setConfirm] = useState(false)
  const [busy, setBusy] = useState(false)

  useEffect(() => { if (iss.data) setF({ subject: iss.data.subject || '', greeting: iss.data.greeting || '', editor_name: iss.data.editor_name || editorName || '' }) }, [iss.data, editorName])
  async function loadPreview(email = asEmail) {
    try { setHtml(await api(`/editor/issue/preview${email ? `?email=${encodeURIComponent(email)}` : ''}`, { as: 'editor', raw: true })) } catch (e: any) { setMsg({ kind: 'bad', text: e.message }) }
  }
  useEffect(() => { if (iss.data) loadPreview('') }, [iss.data]) // eslint-disable-line react-hooks/exhaustive-deps

  async function save() {
    setBusy(true); setMsg(null)
    try { await api('/editor/issue', { as: 'editor', method: 'PATCH', body: f }); await loadPreview(); setMsg({ kind: 'good', text: 'Saved.' }) } catch (e: any) { setMsg({ kind: 'bad', text: e.message }) } finally { setBusy(false) }
  }
  async function test() {
    setBusy(true); setMsg(null)
    try { await api('/editor/issue', { as: 'editor', method: 'PATCH', body: f }); await api('/editor/issue/test', { as: 'editor', body: { email: testTo } }); setMsg({ kind: 'good', text: `Test sent to ${testTo}.` }) } catch (e: any) { setMsg({ kind: 'bad', text: e.message }) } finally { setBusy(false) }
  }
  async function send() {
    setBusy(true); setMsg(null)
    try {
      await api('/editor/issue', { as: 'editor', method: 'PATCH', body: f })
      const r = await api('/editor/issue/send', { as: 'editor', method: 'POST' })
      setMsg({ kind: 'good', text: `Issue No. ${r.issue_number} is going out now. It takes about a second per reader. Refresh this page in a few minutes to see the count.` })
      setConfirm(false); iss.reload()
    } catch (e: any) { setMsg({ kind: 'bad', text: e.message }) } finally { setBusy(false) }
  }

  if (iss.error) return <Notice kind="bad">{iss.error}</Notice>
  if (!iss.data) return <Spinner />
  const d = iss.data
  return (
    <div>
      <H title={`Issue No. ${d.issue_number}`} sub={`Goes to ${d.readers} ${d.readers === 1 ? 'reader' : 'readers'}. Each one gets their own selection: stories from vendors they follow first, never a story they've already seen.`} />
      {d.last_error && <div className="mb-4"><Notice kind="bad">The last send attempt didn't go out: {d.last_error}</Notice></div>}
      <div className="grid gap-6 xl:grid-cols-[1fr_1.1fr]">
        <div className="flex flex-col gap-4">
          <div className="card p-5">
            <p className="text-[14px]"><b>{d.stories_available}</b> approved stories in the bank. Lead story for a new reader: <i>{d.preview_stories[0] || 'none yet'}</i></p>
            {d.stories_available < 3 && <p className="mt-2 text-[14px] text-rust">Fewer than 3 stories available. Readers will get mostly updates. Send this week's questions to vendors.</p>}
          </div>
          <div><label className="label" htmlFor="i-sub">Subject line</label><input id="i-sub" className="field" value={f.subject} onChange={(e) => setF({ ...f, subject: e.target.value })} placeholder={d.preview_stories[0] || 'Uses the lead story headline if empty'} /></div>
          <div><label className="label" htmlFor="i-greet">Your greeting</label><textarea id="i-greet" className="field min-h-[140px]" value={f.greeting} onChange={(e) => setF({ ...f, greeting: e.target.value })} placeholder="A few lines from you: what's in season, what you noticed at the market this week." /></div>
          <div><label className="label" htmlFor="i-name">Signed by</label><input id="i-name" className="field" value={f.editor_name} onChange={(e) => setF({ ...f, editor_name: e.target.value })} /></div>
          <div className="flex flex-wrap gap-2"><button className="btn-quiet" disabled={busy} onClick={save}>Save and refresh preview</button></div>
          <div className="card p-4">
            <label className="label" htmlFor="i-test">Send a test to</label>
            <div className="flex gap-2"><input id="i-test" type="email" className="field min-w-0 flex-1" value={testTo} onChange={(e) => setTestTo(e.target.value)} placeholder="you@example.com" /><button className="btn-quiet shrink-0" disabled={busy || !testTo} onClick={test}>Send test</button></div>
          </div>
          <div className="card border-kraft/50 p-4">
            {!confirm ? <button className="btn-kraft" disabled={busy || !d.readers} onClick={() => setConfirm(true)}>Send to {d.readers} {d.readers === 1 ? 'reader' : 'readers'}…</button> : (
              <div className="flex flex-col gap-2">
                <p className="text-[14px]">This sends issue No. {d.issue_number} to {d.readers} {d.readers === 1 ? 'reader' : 'readers'} now. It can't be unsent.</p>
                <div className="flex gap-2"><button className="btn-kraft" disabled={busy} onClick={send}>Yes, send it</button><button className="btn-ghost" onClick={() => setConfirm(false)}>Not yet</button></div>
              </div>
            )}
            {!d.readers && <p className="hint">No readers yet. Followers appear here as soon as someone follows a vendor.</p>}
          </div>
          {msg && <Notice kind={msg.kind}>{msg.text}</Notice>}
          {d.history.length > 0 && (
            <div className="card overflow-x-auto p-4">
              <p className="mb-2 font-semibold">Sent issues</p>
              <table className="w-full text-[14px]"><thead><tr className="text-left text-[12px] text-soft"><th className="py-1">No.</th><th>Subject</th><th className="text-right">Sent to</th><th className="text-right">Clicks</th></tr></thead>
                <tbody>{d.history.map((h: any) => <tr key={h.issue_number} className="border-t border-line"><td className="py-1.5">{h.issue_number}</td><td>{h.subject}</td><td className="num text-right">{h.sent_count}</td><td className="num text-right">{h.clicks}</td></tr>)}</tbody></table>
            </div>
          )}
        </div>
        <div>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <span className="text-[14px] font-semibold">Preview</span>
            <input className="field min-w-0 max-w-xs flex-1 py-1.5 text-[14px]" placeholder="See it as a reader (email)" value={asEmail} onChange={(e) => setAsEmail(e.target.value)} aria-label="Preview as reader" />
            <button className="btn-quiet btn-sm" onClick={() => loadPreview()}>Show</button>
          </div>
          <iframe title="Issue preview" srcDoc={html} className="h-[900px] w-full rounded-xl border border-line bg-white" />
        </div>
      </div>
    </div>
  )
}

// ── Vendors ──────────────────────────────────────────────────────────────────

function Vendors() {
  const list = useLoad(() => api('/editor/vendors', { as: 'editor' }))
  const opts = useLoad(() => api('/vendor/options'))
  const [adding, setAdding] = useState(false)
  const [open, setOpen] = useState<string | null>(null)
  const [msg, setMsg] = useState<{ kind: 'good' | 'bad' | 'info'; text: string } | null>(null)
  async function remind() {
    setMsg(null)
    try { const r = await api('/editor/vendors/remind', { as: 'editor', body: {} }); setMsg({ kind: 'good', text: `Sending this week's question to ${r.queued} vendors (sample vendors are skipped). Each gets a personal question and a login link.` }) } catch (e: any) { setMsg({ kind: 'bad', text: e.message }) }
  }
  if (list.error) return <Notice kind="bad">{list.error}</Notice>
  return (
    <div>
      <H title="Vendors" sub="Everyone with a Brown Bag page. Vendors join with a code, or you add them here." right={
        <div className="flex flex-wrap gap-2"><button className="btn-quiet" onClick={remind}>Email this week's questions</button><button className="btn-primary" onClick={() => setAdding(!adding)}>Add a vendor</button></div>} />
      {msg && <div className="mb-4"><Notice kind={msg.kind}>{msg.text}</Notice></div>}
      {adding && <AddVendor venues={opts.data?.venues || []} onDone={() => { setAdding(false); list.reload() }} />}
      {!list.data ? <Spinner /> : (
        <div className="card overflow-x-auto">
          <table className="w-full min-w-[760px] text-[14px]">
            <thead><tr className="border-b border-line text-left text-[12px] text-soft">
              <th className="px-4 py-2 font-medium">Vendor</th><th className="px-2 font-medium">Market</th><th className="num px-2 text-right font-medium">Followers</th>
              <th className="num px-2 text-right font-medium">Approved</th><th className="num px-2 text-right font-medium">Waiting</th><th className="px-2 font-medium">Last answered</th><th className="px-4" />
            </tr></thead>
            <tbody>
              {list.data.map((v: any) => (
                <VendorRow key={v.id} v={v} open={open === v.id} toggle={() => setOpen(open === v.id ? null : v.id)} reload={list.reload} />
              ))}
            </tbody>
          </table>
          {!list.data.length && <p className="p-4 text-soft">No vendors yet.</p>}
        </div>
      )}
    </div>
  )
}

function ConversationView({ c, vendorName }: { c: any; vendorName: string }) {
  const skills = Object.entries(c.map?.skills || {}) as [string, number][]
  return (
    <details className="mb-2 rounded-lg border border-line bg-card p-3">
      <summary className="cursor-pointer text-[14px]">
        Week of {c.week} · {c.status}{c.escalated ? ' · escalated' : ''} · {c.messages.length} messages
        {c.hook ? <span className="text-soft"> · “{c.hook}”</span> : null}
        {c.map?.ready ? <span className="chip-good ml-1">story-ready</span> : null}
        {c.map?.mode === 'low_yield' ? <span className="chip-warn ml-1">short answers</span> : null}
      </summary>
      {skills.length > 0 && (
        <p className="mt-2 flex flex-wrap items-center gap-1 text-[12px] text-soft">Skills used: {skills.map(([k, n]) => <span key={k} className="chip">{k} ×{n}</span>)}</p>
      )}
      {c.map?.quotes?.length > 0 && <p className="mt-2 text-[13px]"><b>Vendor’s own lines:</b> {c.map.quotes.map((q: string) => `“${q}”`).join('  ')}</p>}
      {c.map?.want && <p className="text-[13px]"><b>What they wanted:</b> {c.map.want}</p>}
      {c.map?.turn && <p className="text-[13px]"><b>The turn:</b> {c.map.turn}</p>}
      <div className="mt-2 flex flex-col gap-1.5 text-[13px]">
        {c.messages.map((m: any, i: number) => (
          <p key={i}>
            <b className={m.role === 'agent' ? 'text-kraftdeep' : ''}>{m.role === 'agent' ? 'Interviewer' : vendorName}:</b> {m.content}
            {m.voice && <span className="chip ml-1" title="Spoken, then turned into words by speech-to-text and checked by the vendor">spoken</span>}
            {m.role === 'agent' && m.skill && <span className="chip ml-1">{m.skill}</span>}
            {m.problems?.length > 0 && <span className="chip-bad ml-1" title={m.problems.join('; ')}>rule flagged</span>}
            {m.images?.map((u: string) => <img key={u} src={mediaUrl(u)} alt="Attached by the vendor" className="mt-1 max-h-32 rounded" />)}
          </p>
        ))}
      </div>
    </details>
  )
}

function VendorRow({ v, open, toggle, reload }: { v: any; open: boolean; toggle: () => void; reload: () => void }) {
  const [link, setLink] = useState('')
  const [note, setNote] = useState('')
  const convs = useLoad(() => open ? api(`/editor/vendors/${v.id}/conversations`, { as: 'editor' }) : Promise.resolve(null), [open])
  async function getLink(send: boolean) {
    setNote('')
    try { const r = await api(`/editor/vendors/${v.id}/login-link`, { as: 'editor', body: { send } }); setLink(r.login_url); setNote(send ? (r.email_sent ? 'Emailed.' : `Email didn't send (${r.email_error}). Copy the link instead.`) : '') } catch (e: any) { setNote(e.message) }
  }
  return (
    <>
      <tr className="border-b border-line align-top">
        <td className="px-4 py-3"><button className="text-left font-semibold text-ink hover:text-kraftdeep" onClick={toggle}>{v.name}</button> <SampleTag show={v.is_sample} />{v.status !== 'active' && <span className="chip-bad ml-1">{v.status}</span>}<div className="text-[12px] text-soft">{v.email}</div></td>
        <td className="px-2 py-3 text-soft">{v.venue?.name || v.neighborhood || '—'}</td>
        <td className="num px-2 py-3 text-right">{v.followers}</td><td className="num px-2 py-3 text-right">{v.approved}</td><td className="num px-2 py-3 text-right">{v.waiting}</td>
        <td className="px-2 py-3 text-soft">{v.last_submitted_at ? timeAgo(v.last_submitted_at) : 'never'}{v.silent_cycles > 1 && <span className="chip-warn ml-1">quiet {v.silent_cycles} wks</span>}</td>
        <td className="px-4 py-3 text-right"><button className="btn-ghost btn-sm" onClick={toggle}>{open ? 'Close' : 'Open'}</button></td>
      </tr>
      {open && (
        <tr className="border-b border-line bg-paper/60"><td colSpan={7} className="px-4 py-4">
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="flex flex-col gap-3">
              <p className="text-[14px]">{v.description}</p>
              <p className="text-[13px] text-soft">{(v.categories || []).map((c: string) => CATEGORY_LABEL[c] || c).join(', ')} · page <a href={`/v/${v.scan_code}`} target="_blank" rel="noreferrer">/v/{v.scan_code}</a> · last in the app {v.last_seen_at ? timeAgo(v.last_seen_at) : 'never'}</p>
              <div className="flex flex-wrap gap-2">
                <button className="btn-quiet btn-sm" onClick={() => getLink(false)}>Get login link</button>
                <button className="btn-quiet btn-sm" onClick={() => getLink(true)}>Email login link</button>
                {v.status === 'active'
                  ? <button className="btn-ghost btn-sm" onClick={() => api(`/editor/vendors/${v.id}`, { as: 'editor', method: 'PATCH', body: { status: 'paused' } }).then(reload)}>Pause</button>
                  : <button className="btn-ghost btn-sm" onClick={() => api(`/editor/vendors/${v.id}`, { as: 'editor', method: 'PATCH', body: { status: 'active' } }).then(reload)}>Reactivate</button>}
              </div>
              {link && <CopyField value={link} label="Login link (works 7 days; send it by text or email)" />}
              {note && <Notice>{note}</Notice>}
            </div>
            <div>
              <p className="mb-2 text-[13px] font-semibold">Recent conversations</p>
              {!convs.data ? <Spinner /> : !convs.data.length ? <p className="text-[14px] text-soft">No conversations yet.</p> : convs.data.map((c: any) => <ConversationView key={c.id} c={c} vendorName={v.name} />)}
            </div>
          </div>
        </td></tr>
      )}
    </>
  )
}

function AddVendor({ venues, onDone }: { venues: any[]; onDone: () => void }) {
  const [f, setF] = useState({ name: '', email: '', venue_id: '', description: '', schedule_note: '', instagram: '', categories: [] as string[], send_link: true })
  const [res, setRes] = useState<any>(null)
  const [err, setErr] = useState('')
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr('')
    try { setRes(await api('/editor/vendors', { as: 'editor', body: { ...f, venue_id: f.venue_id || undefined } })) } catch (e: any) { setErr(e.message) }
  }
  if (res) return (
    <div className="card mb-6 flex flex-col gap-3 p-5">
      <Notice kind="good">Vendor added. {res.email_sent ? 'We emailed them their link.' : res.email_error ? `The email didn't send (${res.email_error}).` : ''}</Notice>
      <CopyField value={res.login_url} label="Their login link: text it to them" />
      <button className="btn-quiet btn-sm self-start" onClick={onDone}>Done</button>
    </div>
  )
  return (
    <form onSubmit={submit} className="card mb-6 grid gap-4 p-5 sm:grid-cols-2">
      <div><label className="label" htmlFor="av-name">Business name</label><input id="av-name" className="field" required value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></div>
      <div><label className="label" htmlFor="av-email">Email</label><input id="av-email" type="email" className="field" required value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></div>
      <div><label className="label" htmlFor="av-venue">Market</label><select id="av-venue" className="field" value={f.venue_id} onChange={(e) => setF({ ...f, venue_id: e.target.value })}><option value="">None / own shop</option>{venues.map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}</select></div>
      <div><label className="label" htmlFor="av-sched">When and where</label><input id="av-sched" className="field" value={f.schedule_note} onChange={(e) => setF({ ...f, schedule_note: e.target.value })} /></div>
      <div className="sm:col-span-2"><label className="label" htmlFor="av-desc">What they make</label><input id="av-desc" className="field" value={f.description} onChange={(e) => setF({ ...f, description: e.target.value })} /></div>
      <div className="sm:col-span-2">
        <span className="label">Sells</span>
        <div className="flex flex-wrap gap-2">{Object.entries(CATEGORY_LABEL).map(([k, l]) => (
          <button type="button" key={k} aria-pressed={f.categories.includes(k)} onClick={() => setF({ ...f, categories: f.categories.includes(k) ? f.categories.filter((x) => x !== k) : [...f.categories, k] })} className={`rounded-full border px-3 py-1 text-[13px] ${f.categories.includes(k) ? 'border-kraft bg-kraft text-white' : 'border-line bg-card'}`}>{l}</button>
        ))}</div>
      </div>
      <label className="flex items-center gap-2 text-[14px] sm:col-span-2"><input type="checkbox" className="h-4 w-4 accent-[#a86f37]" checked={f.send_link} onChange={(e) => setF({ ...f, send_link: e.target.checked })} />Email them a welcome with their login link</label>
      {err && <div className="sm:col-span-2"><Notice kind="bad">{err}</Notice></div>}
      <div className="sm:col-span-2"><button className="btn-primary">Add vendor</button></div>
    </form>
  )
}

// ── Markets and codes ────────────────────────────────────────────────────────

function Markets() {
  const venues = useLoad(() => api('/editor/venues', { as: 'editor' }))
  const codes = useLoad(() => api('/editor/codes', { as: 'editor' }))
  const [nv, setNv] = useState({ name: '', neighborhood: '', schedule_note: '' })
  const [nc, setNc] = useState({ code: '', label: '', max_uses: 50 })
  const [err, setErr] = useState('')
  return (
    <div className="flex flex-col gap-10">
      <section>
        <H title="Markets" sub="Each market has one shared QR code (for bags, signs and stalls) and a private report link you can send to the market's organizers." />
        <div className="grid gap-4 md:grid-cols-2">
          {(venues.data || []).map((v: any) => (
            <div key={v.id} className="card flex gap-4 p-4">
              <QR value={v.qr_url} size={110} />
              <div className="flex min-w-0 flex-1 flex-col gap-2">
                <p className="font-semibold">{v.name} <span className="font-normal text-soft">· {v.vendors} vendors</span></p>
                <div className="flex flex-wrap gap-2 text-[13px]">
                  <a href={v.page_url} target="_blank" rel="noreferrer" className="btn-quiet btn-sm no-underline">Shopper page</a>
                  <a href={v.report_url} target="_blank" rel="noreferrer" className="btn-quiet btn-sm no-underline">Report</a>
                  <CopyButton text={v.report_url} label="Copy report link" />
                </div>
                <button className="self-start text-[12px] text-soft underline" onClick={() => api(`/editor/venues/${v.id}/new-report-link`, { as: 'editor', method: 'POST' }).then(venues.reload)}>Make a new report link (old one stops working)</button>
              </div>
            </div>
          ))}
        </div>
        <form className="card mt-4 grid gap-3 p-4 sm:grid-cols-[1fr_1fr_1fr_auto]" onSubmit={(e) => { e.preventDefault(); setErr(''); api('/editor/venues', { as: 'editor', body: nv }).then(() => { setNv({ name: '', neighborhood: '', schedule_note: '' }); venues.reload() }).catch((x) => setErr(x.message)) }}>
          <input className="field" required placeholder="New market name" value={nv.name} onChange={(e) => setNv({ ...nv, name: e.target.value })} aria-label="Market name" />
          <input className="field" placeholder="Neighborhood" value={nv.neighborhood} onChange={(e) => setNv({ ...nv, neighborhood: e.target.value })} aria-label="Neighborhood" />
          <input className="field" placeholder="When it runs" value={nv.schedule_note} onChange={(e) => setNv({ ...nv, schedule_note: e.target.value })} aria-label="Schedule" />
          <button className="btn-primary">Add market</button>
        </form>
      </section>
      <section>
        <H title="Invitation codes" sub="Vendors sign up themselves with a code. Give a market's organizer one code for all their vendors." />
        <div className="card overflow-x-auto">
          <table className="w-full min-w-[640px] text-[14px]">
            <thead><tr className="border-b border-line text-left text-[12px] text-soft"><th className="px-4 py-2 font-medium">Code</th><th className="px-2 font-medium">Label</th><th className="num px-2 text-right font-medium">Used</th><th className="px-2 font-medium">Signup link</th><th className="px-4" /></tr></thead>
            <tbody>{(codes.data || []).map((c: any) => (
              <tr key={c.id} className="border-b border-line">
                <td className="px-4 py-2.5 font-mono font-semibold">{c.code} {!c.is_active && <span className="chip-bad">off</span>}</td>
                <td className="px-2 text-soft">{c.label}</td>
                <td className="num px-2 text-right">{c.use_count}{c.max_uses ? `/${c.max_uses}` : ''}</td>
                <td className="px-2"><CopyButton text={c.signup_url} label="Copy link" /></td>
                <td className="px-4 text-right"><button className="btn-ghost btn-sm" onClick={() => api(`/editor/codes/${c.id}/toggle`, { as: 'editor', method: 'POST' }).then(codes.reload)}>{c.is_active ? 'Turn off' : 'Turn on'}</button></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
        <form className="card mt-4 grid gap-3 p-4 sm:grid-cols-[1fr_1.5fr_120px_auto]" onSubmit={(e) => { e.preventDefault(); setErr(''); api('/editor/codes', { as: 'editor', body: { ...nc, code: nc.code || undefined } }).then(() => { setNc({ code: '', label: '', max_uses: 50 }); codes.reload() }).catch((x) => setErr(x.message)) }}>
          <input className="field uppercase" placeholder="Code (or leave empty)" value={nc.code} onChange={(e) => setNc({ ...nc, code: e.target.value })} aria-label="Code" />
          <input className="field" placeholder="Label, e.g. Fremont Sunday Market" value={nc.label} onChange={(e) => setNc({ ...nc, label: e.target.value })} aria-label="Label" />
          <input className="field" type="number" min={1} value={nc.max_uses} onChange={(e) => setNc({ ...nc, max_uses: +e.target.value })} aria-label="Max uses" />
          <button className="btn-primary">Create code</button>
        </form>
        {err && <div className="mt-3"><Notice kind="bad">{err}</Notice></div>}
      </section>
    </div>
  )
}

// ── Readers, inbox, settings ────────────────────────────────────────────────

function Readers() {
  const { data, error } = useLoad(() => api('/editor/readers', { as: 'editor' }))
  if (error) return <Notice kind="bad">{error}</Notice>
  if (!data) return <Spinner />
  const label: Record<string, string> = { qr_vendor: 'Vendor QR', qr_venue: 'Market QR', vendor_page: 'Vendor page', story_page: 'Story page', website: 'Website', unknown: 'Unknown' }
  return (
    <div>
      <H title="Readers" sub="Where readers came from tells you which growth loop is working." />
      <div className="mb-6 flex flex-wrap gap-2">{Object.entries(data.by_source).map(([k, v]) => <span key={k} className="chip text-[13px]">{label[k] || k}: <b className="num ml-1 text-ink">{v as number}</b></span>)}</div>
      <div className="card overflow-x-auto">
        <table className="w-full min-w-[600px] text-[14px]">
          <thead><tr className="border-b border-line text-left text-[12px] text-soft"><th className="px-4 py-2 font-medium">Email</th><th className="px-2 font-medium">Came from</th><th className="num px-2 text-right font-medium">Follows</th><th className="px-2 font-medium">Area</th><th className="px-4 font-medium">Joined</th></tr></thead>
          <tbody>{data.readers.map((r: any) => (
            <tr key={r.email} className="border-b border-line"><td className="px-4 py-2">{r.email} {r.status !== 'active' && <span className="chip-bad">{r.status}</span>}</td><td className="px-2 text-soft">{label[r.source] || r.source || '—'}</td><td className="num px-2 text-right">{r.follows}</td><td className="px-2 text-soft">{r.neighborhood || '—'}</td><td className="px-4 text-soft">{timeAgo(r.created_at)}</td></tr>
          ))}</tbody>
        </table>
        {!data.readers.length && <p className="p-4 text-soft">No readers yet.</p>}
      </div>
    </div>
  )
}

function Inbox() {
  const { data, error, reload } = useLoad(() => api('/editor/inbox', { as: 'editor' }))
  if (error) return <Notice kind="bad">{error}</Notice>
  if (!data) return <Spinner />
  const setStatus = (kind: string, id: string, status: string) => api(`/editor/inbox/${kind}/${id}`, { as: 'editor', body: { status } }).then(reload)
  return (
    <div className="flex flex-col gap-10">
      <section>
        <H title="Inquiries" sub="From the For markets and For vendors pages." />
        {!data.leads.length && <Notice>No inquiries yet.</Notice>}
        <div className="flex flex-col gap-3">{data.leads.map((l: any) => (
          <div key={l.id} className="card p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p><b>{l.name}</b> · {l.organization || '—'} <span className="chip ml-1">{l.kind}</span></p>
              <select className="field w-auto py-1 text-[13px]" value={l.status} onChange={(e) => setStatus('lead', l.id, e.target.value)} aria-label="Status"><option value="new">New</option><option value="contacted">Contacted</option><option value="done">Done</option></select>
            </div>
            <p className="mt-1 text-[14px]"><a href={`mailto:${l.email}`}>{l.email}</a> · {timeAgo(l.created_at)}</p>
            {l.message && <p className="mt-2 text-[14px] text-soft">{l.message}</p>}
          </div>
        ))}</div>
      </section>
      <section>
        <H title="Shop nominations" sub="Readers telling you who to write about next." />
        {!data.nominations.length && <Notice>No nominations yet.</Notice>}
        <div className="flex flex-col gap-3">{data.nominations.map((n: any) => (
          <div key={n.id} className="card p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p><b>{n.shop_name}</b>{n.where ? ` · ${n.where}` : ''}</p>
              <select className="field w-auto py-1 text-[13px]" value={n.status} onChange={(e) => setStatus('nomination', n.id, e.target.value)} aria-label="Status"><option value="new">New</option><option value="contacted">Contacted</option><option value="joined">Joined</option><option value="declined">Declined</option></select>
            </div>
            {n.why && <p className="mt-1 text-[14px] text-soft">{n.why}</p>}
            <p className="mt-1 text-[13px] text-soft">{n.email || 'anonymous'} · {timeAgo(n.created_at)}</p>
          </div>
        ))}</div>
      </section>
    </div>
  )
}

// ── Skills: the instructions behind the interviewer and the writer ───────────

const STAGE_LABEL: Record<string, string> = {
  scout: 'Finding a story to ask about', interview: 'Interviewing', director: 'Reading the answers',
  write: 'Writing and checking', eval: 'Testing only',
}
const CAN_TRY = new Set(['story-scout', 'opener', 'director', 'scene-deepener', 'stakes-and-turn', 'meaning-asker', 'low-yield', 'sensitive-guard', 'wrap-up'])

function Skills() {
  const { data, error, setData } = useLoad(() => api('/editor/skills', { as: 'editor' }))
  const [sel, setSel] = useState('')
  if (error) return <Notice kind="bad">{error}</Notice>
  if (!data) return <Spinner />
  const cur = data.find((s: any) => s.name === sel) || data[0]
  const stages = Object.keys(STAGE_LABEL).filter((st) => data.some((s: any) => s.stage === st))
  return (
    <div>
      <H title="Skills" sub="Each skill is a short set of instructions the interviewer or writer follows. Edit the words and the next conversation uses them. Nothing here needs code." />
      <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
        <nav aria-label="Skills" className="flex flex-col gap-4">
          {stages.map((st) => (
            <div key={st}>
              <p className="eyebrow mb-1">{STAGE_LABEL[st]}</p>
              <ul className="flex flex-col gap-0.5">
                {data.filter((s: any) => s.stage === st).map((s: any) => (
                  <li key={s.name}>
                    <button onClick={() => setSel(s.name)} aria-current={cur.name === s.name ? 'true' : undefined}
                      className={`flex w-full items-center justify-between rounded-md px-3 py-1.5 text-left text-[14px] ${cur.name === s.name ? 'bg-ink text-card' : 'text-ink hover:bg-card'}`}>
                      <span>{s.name}</span>{s.edited && <span className={`text-[11px] ${cur.name === s.name ? 'text-card/80' : 'text-kraftdeep'}`}>edited</span>}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
        <SkillEditor key={cur.name} sk={cur} onSaved={(sk: any) => setData(data.map((x: any) => (x.name === sk.name ? sk : x)))} />
      </div>
    </div>
  )
}

function SkillEditor({ sk, onSaved }: { sk: any; onSaved: (sk: any) => void }) {
  const [body, setBody] = useState<string>(sk.body)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<{ kind: 'good' | 'bad'; text: string } | null>(null)
  const [question, setQuestion] = useState('Tell me about the last Saturday you sold out. What time did the last jar go?')
  const [answer, setAnswer] = useState('')
  const [trying, setTrying] = useState(false)
  const [out, setOut] = useState<{ output: string; problems: string[] } | null>(null)
  const [tryErr, setTryErr] = useState('')
  const dirty = body.trim() !== sk.body.trim()

  async function save() {
    setBusy(true); setMsg(null)
    try { const r = await api(`/editor/skills/${sk.name}`, { as: 'editor', method: 'PUT', body: { body } }); onSaved(r); setBody(r.body); setMsg({ kind: 'good', text: 'Saved. The next conversation uses this.' }) }
    catch (e: any) { setMsg({ kind: 'bad', text: e.message }) } finally { setBusy(false) }
  }
  async function reset() {
    if (!window.confirm('Go back to the original wording for this skill? Your edits will be lost.')) return
    setBusy(true); setMsg(null)
    try { const r = await api(`/editor/skills/${sk.name}`, { as: 'editor', method: 'DELETE' }); onSaved(r); setBody(r.body); setMsg({ kind: 'good', text: 'Back to the original.' }) }
    catch (e: any) { setMsg({ kind: 'bad', text: e.message }) } finally { setBusy(false) }
  }
  async function tryIt() {
    setTrying(true); setTryErr(''); setOut(null)
    try { setOut(await api(`/editor/skills/${sk.name}/try`, { as: 'editor', body: { question, answer } })) }
    catch (e: any) { setTryErr(e.message) } finally { setTrying(false) }
  }

  return (
    <div className="flex flex-col gap-5">
      <section className="card p-5">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="font-serif text-[22px] font-medium">{sk.name}</h2>
          {sk.edited && <span className="chip-warn">edited{sk.edited_by ? ` by ${sk.edited_by}` : ''}{sk.edited_at ? ` · ${timeAgo(sk.edited_at)}` : ''}</span>}
        </div>
        <p className="mt-1 text-[14px] text-soft">{sk.description}</p>
        <label className="label mt-4" htmlFor="skill-body">Instructions</label>
        <textarea id="skill-body" className="field min-h-[320px] font-mono text-[13px] leading-relaxed" value={body} onChange={(e) => setBody(e.target.value)} spellCheck={false} />
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button className="btn-primary" disabled={busy || !dirty} onClick={save}>{busy ? 'Saving…' : 'Save'}</button>
          {dirty && <button className="btn-ghost" disabled={busy} onClick={() => setBody(sk.body)}>Discard changes</button>}
          {sk.edited && <button className="btn-ghost" disabled={busy} onClick={reset}>Back to the original</button>}
        </div>
        {msg && <div className="mt-3"><Notice kind={msg.kind}>{msg.text}</Notice></div>}
        {sk.extras?.length > 0 && (
          <details className="mt-4">
            <summary className="cursor-pointer text-[14px] font-semibold text-kraft">Examples this skill also reads ({sk.extras.length})</summary>
            {sk.extras.map((x: any) => <pre key={x.name} className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg bg-paper p-3 text-[12px] leading-relaxed"><b>{x.name}</b>{'\n\n'}{x.text}</pre>)}
            <p className="hint mt-1">Examples are part of the skill's original files and can't be edited here. Put anything you want to change in the instructions above.</p>
          </details>
        )}
      </section>

      {CAN_TRY.has(sk.name) && (
        <section className="card p-5">
          <h3 className="font-semibold">Try it</h3>
          <p className="text-[14px] text-soft">Runs the saved version of this skill on an answer you type. {dirty && <b>You have unsaved edits, so save first to try them.</b>}</p>
          {sk.name !== 'story-scout' && sk.name !== 'opener' && (
            <>
              <label className="label mt-3" htmlFor="try-q">The interviewer asked</label>
              <input id="try-q" className="field" value={question} onChange={(e) => setQuestion(e.target.value)} />
            </>
          )}
          <label className="label mt-3" htmlFor="try-a">{sk.name === 'opener' ? 'Story the vendor picked' : sk.name === 'story-scout' ? 'Nothing to type for this one' : 'The vendor answered'}</label>
          <textarea id="try-a" className="field min-h-[90px]" value={answer} onChange={(e) => setAnswer(e.target.value)} disabled={sk.name === 'story-scout'}
            placeholder={sk.name === 'opener' ? 'The regular who always asks for one thing' : 'We sold out around two. It was a woman with a stroller who bought the last ones, she said her kid wouldn’t eat anything else.'} />
          <button className="btn-quiet mt-3" disabled={trying || dirty} onClick={tryIt}>{trying ? 'Running…' : 'Run'}</button>
          {tryErr && <div className="mt-3"><Notice kind="bad">{tryErr}</Notice></div>}
          {out && (
            <div className="mt-3">
              <p className="label">Result</p>
              <pre className="whitespace-pre-wrap rounded-lg bg-paper p-3 text-[14px] leading-relaxed">{out.output}</pre>
              {out.problems?.length > 0 && <p className="mt-2 text-[13px] text-rust">Rule check flagged: {out.problems.join('; ')}</p>}
              {out.problems?.length === 0 && <p className="mt-2 text-[13px] text-moss">Passes the rule check (one question, no “why”, no praise).</p>}
            </div>
          )}
        </section>
      )}
    </div>
  )
}

function Settings() {
  const s = useLoad(() => api('/editor/settings', { as: 'editor' }))
  const [f, setF] = useState({ publication_name: '', from_email: '', from_name: '' })
  const [ne, setNe] = useState({ name: '', email: '', password: '' })
  const [msg, setMsg] = useState<{ kind: 'good' | 'bad'; text: string } | null>(null)
  const [confirmSamples, setConfirmSamples] = useState(false)
  useEffect(() => { if (s.data) setF({ publication_name: s.data.publication_name, from_email: s.data.from_email, from_name: s.data.from_name }) }, [s.data])
  const run = (p: Promise<any>, ok: string) => p.then(() => { setMsg({ kind: 'good', text: ok }); s.reload() }).catch((e) => setMsg({ kind: 'bad', text: e.message }))
  if (!s.data) return <Spinner />
  return (
    <div className="flex max-w-2xl flex-col gap-8">
      <H title="Settings" />
      {msg && <Notice kind={msg.kind}>{msg.text}</Notice>}
      <form className="card flex flex-col gap-4 p-5" onSubmit={(e) => { e.preventDefault(); run(api('/editor/settings', { as: 'editor', method: 'PATCH', body: f }), 'Saved.') }}>
        <p className="font-semibold">Publication</p>
        <div><label className="label" htmlFor="st-pub">Name readers see</label><input id="st-pub" className="field" value={f.publication_name} onChange={(e) => setF({ ...f, publication_name: e.target.value })} /></div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div><label className="label" htmlFor="st-fn">Emails come from (name)</label><input id="st-fn" className="field" value={f.from_name} onChange={(e) => setF({ ...f, from_name: e.target.value })} /></div>
          <div><label className="label" htmlFor="st-fe">Emails come from (address)</label><input id="st-fe" type="email" className="field" value={f.from_email} onChange={(e) => setF({ ...f, from_email: e.target.value })} /><p className="hint">Must be on a domain verified with the email provider (Resend).</p></div>
        </div>
        <button className="btn-primary self-start">Save</button>
      </form>
      <form className="card flex flex-col gap-3 p-5" onSubmit={(e) => { e.preventDefault(); run(api('/editor/editors', { as: 'editor', body: ne }).then(() => setNe({ name: '', email: '', password: '' })), 'Editor added.') }}>
        <p className="font-semibold">Editors</p>
        <ul className="text-[14px] text-soft">{s.data.editors.map((e: any) => <li key={e.email}>{e.name} · {e.email}</li>)}</ul>
        <div className="grid gap-3 sm:grid-cols-3">
          <input className="field" required placeholder="Name" value={ne.name} onChange={(e) => setNe({ ...ne, name: e.target.value })} aria-label="Name" />
          <input className="field" required type="email" placeholder="Email" value={ne.email} onChange={(e) => setNe({ ...ne, email: e.target.value })} aria-label="Email" />
          <input className="field" required type="password" minLength={8} placeholder="Password" value={ne.password} onChange={(e) => setNe({ ...ne, password: e.target.value })} aria-label="Password" />
        </div>
        <button className="btn-quiet self-start">Add editor</button>
      </form>
      <div className="card flex flex-col gap-3 p-5">
        <p className="font-semibold">Sample content</p>
        <p className="text-[14px] text-soft">The site started with five sample vendors and their stories (marked “Sample”) so every page has something to show. Remove them before real readers arrive.</p>
        {!confirmSamples ? <button className="btn-danger self-start" onClick={() => setConfirmSamples(true)}>Remove sample content…</button> : (
          <div className="flex flex-wrap gap-2"><button className="btn-danger" onClick={() => run(api('/editor/samples', { as: 'editor', method: 'DELETE' }).then(() => setConfirmSamples(false)), 'Sample content removed.')}>Yes, remove all sample vendors and stories</button><button className="btn-ghost" onClick={() => setConfirmSamples(false)}>Cancel</button></div>
        )}
      </div>
      <p className="text-[12px] text-soft">API: {API}</p>
    </div>
  )
}

