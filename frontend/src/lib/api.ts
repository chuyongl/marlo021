// API client and the three kinds of identity the site remembers:
//   reader  — subscriber token (after following once, this browser can follow in one tap)
//   vendor  — vendor session token (from a magic link)
//   editor  — editor token (email + password)

export const API = (process.env.REACT_APP_API_URL || 'https://api.marlo021.ai').replace(/\/$/, '')

const KEYS = { reader: 'bb_reader', vendor: 'bb_vendor', editor: 'bb_editor' } as const
type Who = keyof typeof KEYS

export const store = {
  get(who: Who): string | null {
    try { return localStorage.getItem(KEYS[who]) } catch { return null }
  },
  set(who: Who, value: string) {
    try { localStorage.setItem(KEYS[who], value) } catch { /* private mode */ }
  },
  clear(who: Who) {
    try { localStorage.removeItem(KEYS[who]) } catch { /* ignore */ }
  },
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

type Opts = { method?: string; body?: unknown; as?: Who; form?: FormData; raw?: boolean }

export async function api<T = any>(path: string, opts: Opts = {}): Promise<T> {
  const headers: Record<string, string> = {}
  if (opts.as) {
    const t = store.get(opts.as)
    if (t) headers.Authorization = `Bearer ${t}`
  }
  let body: BodyInit | undefined
  if (opts.form) body = opts.form
  else if (opts.body !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(opts.body)
  }
  let res: Response
  try {
    res = await fetch(API + path, { method: opts.method || (body ? 'POST' : 'GET'), headers, body })
  } catch {
    throw new ApiError(0, "We couldn't reach the server. Check your connection and try again.")
  }
  if (!res.ok) {
    let msg = 'Something went wrong. Please try again.'
    try {
      const j = await res.json()
      if (typeof j.detail === 'string') msg = j.detail
      else if (Array.isArray(j.detail) && j.detail[0]?.msg) msg = humanize(j.detail[0])
    } catch { /* not json */ }
    if (res.status === 401 && opts.as) store.clear(opts.as)
    throw new ApiError(res.status, msg)
  }
  if (opts.raw) return (await res.text()) as unknown as T
  return res.json()
}

function humanize(d: { loc?: string[]; msg: string }) {
  const field = d.loc?.[d.loc.length - 1]
  if (field === 'email') return 'Please enter a valid email address.'
  return field ? `${field.replace(/_/g, ' ')}: ${d.msg}` : d.msg
}

export function mediaUrl(u?: string | null) {
  if (!u) return ''
  return u.startsWith('/media/') ? API + u : u
}

// Resize a photo in the browser before uploading, so phones don't send 8 MB files.
export async function shrinkImage(file: File, max = 1400): Promise<Blob> {
  const url = URL.createObjectURL(file)
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const i = new Image()
      i.onload = () => resolve(i)
      i.onerror = reject
      i.src = url
    })
    const scale = Math.min(1, max / Math.max(img.width, img.height))
    const c = document.createElement('canvas')
    c.width = Math.round(img.width * scale)
    c.height = Math.round(img.height * scale)
    c.getContext('2d')!.drawImage(img, 0, 0, c.width, c.height)
    return await new Promise<Blob>((resolve) => c.toBlob((b) => resolve(b || file), 'image/jpeg', 0.84))
  } catch {
    return file
  } finally {
    URL.revokeObjectURL(url)
  }
}

export async function uploadPhoto(file: File, as?: Who): Promise<string> {
  const blob = await shrinkImage(file)
  const form = new FormData()
  form.append('file', blob, 'photo.jpg')
  const path = as === 'vendor' ? '/vendor/photo' : '/public/media'
  const r = await api<{ url: string }>(path, { form, as, method: 'POST' })
  return r.url
}

export const CATEGORY_LABEL: Record<string, string> = {
  bakery: 'Bakery', produce: 'Produce', prepared_food: 'Prepared food', meat: 'Meat & sausage',
  seafood: 'Seafood', dairy_cheese: 'Dairy & cheese', preserves: 'Preserves & sauces', honey: 'Honey',
  coffee_tea: 'Coffee & tea', flowers: 'Flowers & plants', jewelry: 'Jewelry', crafts: 'Crafts & goods',
}

export function timeAgo(iso?: string | null) {
  if (!iso) return ''
  const d = (Date.now() - new Date(iso).getTime()) / 1000
  if (d < 60) return 'just now'
  if (d < 3600) return `${Math.round(d / 60)} min ago`
  if (d < 86400) return `${Math.round(d / 3600)} h ago`
  if (d < 86400 * 14) return `${Math.round(d / 86400)} days ago`
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}
