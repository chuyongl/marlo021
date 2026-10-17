import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'

// Record a voice memo, send it for transcription, hand the words back so the person can check
// and fix them before anything is sent. The recording itself is never kept.

const MAX_SECONDS = 300

function pickMime(): string {
  const options = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/webm', 'audio/ogg;codecs=opus']
  for (const m of options) {
    try { if (MediaRecorder.isTypeSupported(m)) return m } catch { /* keep looking */ }
  }
  return ''
}

function supported() {
  return typeof window !== 'undefined' && typeof MediaRecorder !== 'undefined' && !!navigator.mediaDevices?.getUserMedia
}

function clock(s: number) {
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

export function VoiceButton({ onText, disabled }: { onText: (t: string) => void; disabled?: boolean }) {
  const [state, setState] = useState<'idle' | 'recording' | 'working'>('idle')
  const [secs, setSecs] = useState(0)
  const [err, setErr] = useState('')
  const rec = useRef<MediaRecorder | null>(null)
  const chunks = useRef<Blob[]>([])
  const stream = useRef<MediaStream | null>(null)
  const timer = useRef<ReturnType<typeof setInterval> | null>(null)
  const discard = useRef(false)

  const release = useCallback(() => {
    if (timer.current) { clearInterval(timer.current); timer.current = null }
    stream.current?.getTracks().forEach((t) => t.stop())
    stream.current = null
  }, [])

  // Leaving the page mid-recording throws the recording away.
  useEffect(() => () => {
    discard.current = true
    try { if (rec.current && rec.current.state !== 'inactive') rec.current.stop() } catch { /* already stopped */ }
    release()
  }, [release])

  const stop = useCallback(() => {
    try { if (rec.current && rec.current.state !== 'inactive') rec.current.stop() } catch { /* already stopped */ }
  }, [])

  async function begin() {
    setErr('')
    discard.current = false
    let s: MediaStream
    try {
      s = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch {
      setErr("The microphone is blocked. Allow it in your browser, or just type instead.")
      return
    }
    stream.current = s
    chunks.current = []
    const mime = pickMime()
    let r: MediaRecorder
    try {
      r = mime ? new MediaRecorder(s, { mimeType: mime }) : new MediaRecorder(s)
    } catch {
      release()
      setErr("Recording doesn't work in this browser. Please type instead.")
      return
    }
    rec.current = r
    r.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunks.current.push(e.data) }
    r.onstop = async () => {
      release()
      if (discard.current) { setState('idle'); return }
      const type = (r.mimeType || mime || 'audio/webm').split(';')[0]
      const blob = new Blob(chunks.current, { type })
      chunks.current = []
      setState('working')
      try {
        const form = new FormData()
        form.append('file', blob, type.includes('mp4') ? 'voice.m4a' : type.includes('ogg') ? 'voice.ogg' : 'voice.webm')
        const out = await api<{ text: string }>('/vendor/voice/transcribe', { form, as: 'vendor', method: 'POST' })
        if (!discard.current) onText(out.text)
      } catch (e: any) {
        if (!discard.current) setErr(e.message || "We couldn't turn that into words. Please try again, or type it.")
      } finally {
        if (!discard.current) setState('idle')
      }
    }
    r.start(1000)
    setSecs(0)
    setState('recording')
    timer.current = setInterval(() => {
      setSecs((n) => {
        if (n + 1 >= MAX_SECONDS) stop()
        return n + 1
      })
    }, 1000)
  }

  if (!supported()) return null

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex flex-wrap items-center gap-2">
        {state === 'idle' && (
          <button type="button" className="btn-quiet btn-sm" onClick={begin} disabled={disabled}>
            <span aria-hidden="true">🎙 </span>Record instead of typing
          </button>
        )}
        {state === 'recording' && (
          <>
            <button type="button" className="btn-primary btn-sm" onClick={stop} aria-label={`Stop recording, ${clock(secs)} so far`}>
              <span aria-hidden="true" className="mr-1.5 inline-block h-2.5 w-2.5 animate-pulse rounded-full bg-card" />Stop · {clock(secs)}
            </button>
            <span className="text-[13px] text-soft">Take your time. Up to five minutes.</span>
          </>
        )}
        {state === 'working' && (
          <span className="inline-flex items-center gap-2 text-[14px] text-soft" role="status">
            <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-sky/30 border-t-sky" />Turning it into words…
          </span>
        )}
      </div>
      {state === 'idle' && <p className="hint">We turn your voice into words for you to check. We don't keep the recording.</p>}
      {err && <p className="text-[13px] text-rust" role="alert">{err}</p>}
    </div>
  )
}
