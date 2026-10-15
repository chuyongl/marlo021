import { ReactNode, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import QRCode from 'qrcode'
import { api, ApiError, copyText, mediaUrl, store, CATEGORY_LABEL } from '../lib/api'

export function BagMark({ size = 22 }: { size?: number }) {
  // A folded paper bag, drawn simply.
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 7h14l-1.2 13.2a1 1 0 0 1-1 .8H7.2a1 1 0 0 1-1-.8L5 7z" fill="#a86f37" />
      <path d="M5 7l1.6-3h10.8L19 7" fill="#c79762" />
      <path d="M9.5 10.5c0 1.4 1.1 2.5 2.5 2.5s2.5-1.1 2.5-2.5" stroke="#fffdf8" strokeWidth="1.4" fill="none" strokeLinecap="round" />
    </svg>
  )
}

export function Wordmark({ className = '' }: { className?: string }) {
  return (
    <Link to="/" className={`inline-flex items-center gap-2 no-underline ${className}`}>
      <BagMark />
      <span className="font-serif text-[22px] font-semibold tracking-tight text-ink">Brown Bag</span>
    </Link>
  )
}

export function SiteHeader() {
  const [open, setOpen] = useState(false)
  const links = [
    { to: '/stories', label: 'Stories' },
    { to: '/for-vendors', label: 'For vendors' },
    { to: '/for-markets', label: 'For markets' },
  ]
  return (
    <header className="no-print border-b border-line/70 bg-paper/90 backdrop-blur sticky z-30" style={{ top: 'env(safe-area-inset-top, 0px)' }}>
      <div className="wrap flex h-16 items-center justify-between">
        <Wordmark />
        <nav className="hidden items-center gap-1 sm:flex">
          {links.map((l) => (
            <Link key={l.to} to={l.to} className="rounded-md px-3 py-2 text-[15px] font-medium text-soft no-underline hover:text-ink">{l.label}</Link>
          ))}
          <Link to="/vendor" className="btn-quiet btn-sm ml-2 no-underline">Vendor sign in</Link>
        </nav>
        <button className="btn-ghost sm:hidden" aria-label="Menu" aria-expanded={open} onClick={() => setOpen(!open)}>
          <svg width="22" height="22" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
        </button>
      </div>
      {open && (
        <nav className="wrap flex flex-col gap-1 pb-4 sm:hidden">
          {links.map((l) => (
            <Link key={l.to} to={l.to} onClick={() => setOpen(false)} className="rounded-md px-2 py-2 font-medium text-ink no-underline">{l.label}</Link>
          ))}
          <Link to="/vendor" onClick={() => setOpen(false)} className="rounded-md px-2 py-2 font-medium text-kraft no-underline">Vendor sign in</Link>
        </nav>
      )}
    </header>
  )
}

export function SiteFooter() {
  return (
    <footer className="no-print mt-24 border-t border-line">
      <div className="wrap grid gap-8 py-12 text-[14px] text-soft sm:grid-cols-4">
        <div className="sm:col-span-2">
          <Wordmark />
          <p className="mt-3 max-w-sm">A free weekly email about Seattle's market vendors and makers. Every story is told by the vendor, checked by them, and approved by a named editor.</p>
        </div>
        <div className="flex flex-col gap-2">
          <Link to="/stories" className="no-underline hover:text-ink">Stories</Link>
          <Link to="/nominate" className="no-underline hover:text-ink">Nominate a shop</Link>
          <Link to="/share" className="no-underline hover:text-ink">Share what you made</Link>
          <Link to="/why-local" className="no-underline hover:text-ink">Why local email works</Link>
        </div>
        <div className="flex flex-col gap-2">
          <Link to="/for-vendors" className="no-underline hover:text-ink">For vendors</Link>
          <Link to="/for-markets" className="no-underline hover:text-ink">For markets</Link>
          <Link to="/vendor" className="no-underline hover:text-ink">Vendor sign in</Link>
          <Link to="/privacy" className="no-underline hover:text-ink">Privacy</Link>
          <Link to="/terms" className="no-underline hover:text-ink">Terms</Link>
        </div>
      </div>
    </footer>
  )
}

export function Page({ children, narrow = false }: { children: ReactNode; narrow?: boolean }) {
  useEffect(() => { window.scrollTo(0, 0) }, [])
  return (
    <div className="min-h-screen" style={{ paddingLeft: 'env(safe-area-inset-left, 0px)', paddingRight: 'env(safe-area-inset-right, 0px)' }}>
      <SiteHeader />
      <main className={narrow ? 'wrap-narrow' : ''}>{children}</main>
      <SiteFooter />
    </div>
  )
}

export function Spinner({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-10 text-soft" role="status">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-line border-t-kraft" />
      <span className="text-sm">{label}…</span>
    </div>
  )
}

export function Notice({ kind = 'info', children }: { kind?: 'info' | 'good' | 'bad'; children: ReactNode }) {
  const cls = kind === 'good' ? 'border-moss/30 bg-moss/10 text-moss' : kind === 'bad' ? 'border-rust/30 bg-rust/10 text-rust' : 'border-sky/30 bg-sky/10 text-sky'
  return <div role={kind === 'bad' ? 'alert' : 'status'} className={`rounded-lg border px-3 py-2.5 text-[14px] ${cls}`}>{children}</div>
}

export function useLoad<T>(fn: () => Promise<T>, deps: any[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [tick, setTick] = useState(0)
  useEffect(() => {
    let alive = true
    setLoading(true)
    fn().then((d) => { if (alive) { setData(d); setError('') } })
      .catch((e: ApiError) => { if (alive) setError(e.message) })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick])
  return { data, error, loading, reload: () => setTick((t) => t + 1), setData }
}

export function CopyButton({ text, label = 'Copy', className = 'btn-quiet btn-sm' }: { text: string; label?: string; className?: string }) {
  const [done, setDone] = useState(false)
  return (
    <button type="button" className={className} onClick={async () => {
      const ok = await copyText(text)
      if (ok) { setDone(true); setTimeout(() => setDone(false), 1600) } else { window.prompt('Copy this:', text) }
    }}>{done ? 'Copied' : label}</button>
  )
}

export function CopyField({ value, label }: { value: string; label?: string }) {
  return (
    <div>
      {label && <span className="label">{label}</span>}
      <div className="flex gap-2">
        <input className="field min-w-0 flex-1 font-mono text-[13px]" readOnly value={value} onFocus={(e) => e.currentTarget.select()} />
        <CopyButton text={value} />
      </div>
    </div>
  )
}

export function QR({ value, size = 220, className = '' }: { value: string; size?: number; className?: string }) {
  const [src, setSrc] = useState('')
  useEffect(() => {
    QRCode.toDataURL(value, { width: size * 2, margin: 1, color: { dark: '#231d17', light: '#ffffff' } }).then(setSrc).catch(() => setSrc(''))
  }, [value, size])
  return src ? <img src={src} width={size} height={size} alt={`QR code for ${value}`} className={className} /> : <div style={{ width: size, height: size }} className="bg-line/40" />
}

export function Cats({ cats }: { cats: string[] }) {
  return <>{(cats || []).map((c) => <span key={c} className="chip">{CATEGORY_LABEL[c] || c}</span>)}</>
}

export function SampleTag({ show }: { show?: boolean }) {
  return show ? <span className="chip-info" title="Example content to show how Brown Bag works">Sample</span> : null
}

export function Paras({ text, className = 'story-body' }: { text?: string | null; className?: string }) {
  return <div className={className}>{(text || '').split('\n').filter((p) => p.trim()).map((p, i) => <p key={i}>{p}</p>)}</div>
}

export function Avatar({ name, url, size = 48 }: { name: string; url?: string | null; size?: number }) {
  if (url) return <img src={mediaUrl(url)} alt="" width={size} height={size} className="rounded-full object-cover" style={{ width: size, height: size }} />
  const initials = name.split(/\s+/).slice(0, 2).map((w) => w[0]).join('').toUpperCase()
  return <div className="flex items-center justify-center rounded-full bg-kraft/15 font-semibold text-kraftdeep" style={{ width: size, height: size, fontSize: size / 2.8 }}>{initials}</div>
}

// ── Follow form: used on vendor pages, market pages and story pages ─────────

export function FollowBox({ vendorIds, source, sourceRef, cta = 'Follow', onDone, compact = false }: {
  vendorIds: string[]; source: string; sourceRef?: string; cta?: string; onDone?: (names: string[]) => void; compact?: boolean
}) {
  const known = store.get('reader')
  const [email, setEmail] = useState('')
  const [consent, setConsent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState<string[] | null>(null)
  const ref = new URLSearchParams(window.location.search).get('ref') || undefined

  async function submit(e?: React.FormEvent) {
    e?.preventDefault()
    if (!vendorIds.length) { setError('Pick at least one vendor to follow.'); return }
    setBusy(true); setError('')
    try {
      const r = await api('/public/follow', { body: { email: known ? undefined : email, token: known || undefined, consent, vendor_ids: vendorIds, source, source_ref: sourceRef, ref } })
      store.set('reader', r.token)
      setDone(r.newly_followed.length ? r.newly_followed : vendorIds.length ? ['them'] : [])
      onDone?.(r.newly_followed)
    } catch (err: any) {
      if (known && err.status === 404) store.clear('reader')
      setError(err.message)
    } finally { setBusy(false) }
  }

  if (done) {
    return (
      <Notice kind="good">
        You're following {done.join(', ')}. Their news comes in your weekly Brown Bag email, usually Thursday.
      </Notice>
    )
  }
  if (known) {
    return (
      <div className="flex flex-col gap-2">
        <button className="btn-primary w-full sm:w-auto" disabled={busy} onClick={() => submit()}>{busy ? 'Following…' : cta}</button>
        <p className="hint">You're already on the list, so one tap does it.</p>
        {error && <Notice kind="bad">{error}</Notice>}
      </div>
    )
  }
  return (
    <form onSubmit={submit} className="flex flex-col gap-3">
      <div className={compact ? 'flex flex-col gap-2 sm:flex-row' : 'flex flex-col gap-2'}>
        <label htmlFor="follow-email" className="sr-only">Email</label>
        <input id="follow-email" className="field min-w-0 flex-1" type="email" inputMode="email" autoComplete="email" required placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
        <button className="btn-primary shrink-0" disabled={busy}>{busy ? 'Following…' : cta}</button>
      </div>
      <label className="flex items-start gap-2 text-[13px] text-soft">
        <input id="follow-consent" type="checkbox" className="mt-0.5 h-4 w-4 accent-[#a86f37]" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
        <span>Send me the free Brown Bag email once a week. Unsubscribe with one click, any time. <Link to="/privacy" className="text-soft">Privacy</Link></span>
      </label>
      {error && <Notice kind="bad">{error}</Notice>}
    </form>
  )
}

export function StoryCard({ s, big = false }: { s: any; big?: boolean }) {
  const first = (s.body || '').split('\n').find((p: string) => p.trim()) || ''
  return (
    <Link to={`/s/${s.slug}`} className="group card block p-5 no-underline transition hover:border-kraft sm:p-6">
      <div className="mb-2 flex flex-wrap items-center gap-2 text-[13px] text-soft">
        <span className="font-semibold text-kraftdeep">{s.vendor?.name}</span>
        {s.vendor?.neighborhood && <span>· {s.vendor.neighborhood}</span>}
        <SampleTag show={s.is_sample} />
      </div>
      <h3 className={`font-serif ${big ? 'text-[28px]' : 'text-[22px]'} font-medium leading-tight text-ink group-hover:text-kraftdeep`}>{s.headline}</h3>
      <p className="mt-3 line-clamp-3 font-serif text-[17px] leading-relaxed text-soft">{first}</p>
    </Link>
  )
}
