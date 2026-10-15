import { Link, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import { Notice, Page, QR, SampleTag, Spinner, useLoad } from '../ui/kit'

export default function Report() {
  const { token = '' } = useParams()
  const { data, error } = useLoad(() => api(`/public/report/${token}`), [token])
  if (error) return <Page narrow><div className="py-12"><Notice kind="bad">{error}</Notice></div></Page>
  if (!data) return <Page narrow><Spinner /></Page>
  const t = data.totals
  const max = Math.max(1, ...data.weeks.map((w: any) => w.new_follows))
  return (
    <Page>
      <section className="wrap pb-6 pt-10">
        <p className="eyebrow">{data.publication} · market report</p>
        <div className="mt-2 flex flex-wrap items-end justify-between gap-4">
          <h1 className="font-serif text-[40px] font-medium leading-tight">{data.venue.name}</h1>
          <p className="text-[13px] text-soft">Live numbers · updated {new Date(data.generated_at).toLocaleString()}</p>
        </div>
        {t.sample_vendors > 0 && (
          <div className="mt-4"><Notice>{t.sample_vendors} of these vendors are sample profiles used to demonstrate Brown Bag. Their numbers come from test activity.</Notice></div>
        )}
      </section>

      <section className="wrap">
        <div className="card grid grid-cols-2 gap-px overflow-hidden bg-line sm:grid-cols-3 lg:grid-cols-6">
          {[
            ['Readers following your vendors', t.readers], ['New follows, 7 days', t.new_follows_7], ['New follows, 30 days', t.new_follows_30],
            ['Story clicks, 30 days', t.clicks_30], ['QR scans, 30 days', t.scans_30], ['Reader photos', t.reader_shares],
          ].map(([k, v]) => (
            <div key={k as string} className="bg-card px-5 py-4"><p className="num text-[30px] font-semibold">{(v as number).toLocaleString()}</p><p className="text-[13px] leading-snug text-soft">{k}</p></div>
          ))}
        </div>
      </section>

      <section className="wrap mt-6 grid gap-6 lg:grid-cols-[1fr_1.4fr]">
        <div className="card p-5">
          <p className="mb-4 font-semibold">New follows per week</p>
          <div className="flex h-44 items-end gap-2">
            {data.weeks.map((w: any, i: number) => (
              <div key={w.week_ending} className="flex h-full flex-1 flex-col items-center justify-end gap-1" title={`Week ending ${w.week_ending}: ${w.new_follows}`}>
                <span className="num text-[11px] text-soft">{w.new_follows}</span>
                <div className={`w-full rounded-t ${i === data.weeks.length - 1 ? 'bg-kraft' : 'bg-kraft/35'}`} style={{ height: `${Math.max(2, (w.new_follows / max) * 100)}%` }} />
                <span className="text-[10px] text-soft">{w.week_ending.slice(5)}</span>
              </div>
            ))}
          </div>
          <p className="mt-4 text-[13px] text-soft">Issues sent so far: {t.issues_sent}</p>
        </div>
        <div className="card overflow-x-auto p-5">
          <p className="mb-3 font-semibold">Vendors ({t.vendors})</p>
          <table className="w-full min-w-[520px] text-[14px]">
            <thead><tr className="text-left text-[12px] text-soft">
              <th className="py-1 pr-2 font-medium">Vendor</th><th className="num py-1 pr-2 text-right font-medium">Followers</th>
              <th className="num py-1 pr-2 text-right font-medium">Stories</th><th className="num py-1 pr-2 text-right font-medium">Updates</th>
              <th className="num py-1 pr-2 text-right font-medium">Clicks 30d</th><th className="num py-1 text-right font-medium">Reader photos</th>
            </tr></thead>
            <tbody>
              {data.vendors.sort((a: any, b: any) => b.followers - a.followers).map((v: any) => (
                <tr key={v.scan_code} className="border-t border-line">
                  <td className="py-2 pr-2"><Link to={`/v/${v.scan_code}`} className="text-ink">{v.name}</Link> <SampleTag show={v.is_sample} /></td>
                  <td className="num py-2 pr-2 text-right">{v.followers}</td><td className="num py-2 pr-2 text-right">{v.stories}</td>
                  <td className="num py-2 pr-2 text-right">{v.updates}</td><td className="num py-2 pr-2 text-right">{v.clicks_30}</td>
                  <td className="num py-2 text-right">{v.reader_shares}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data.vendors.length && <p className="text-soft">No vendors have joined yet.</p>}
        </div>
      </section>

      <section className="wrap mt-6 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="card p-5">
          <p className="mb-3 font-semibold">Recent stories from your vendors</p>
          {data.recent_stories.map((s: any) => (
            <Link key={s.id} to={`/s/${s.slug}`} className="block border-t border-line py-3 text-ink no-underline first:border-0 hover:text-kraftdeep">
              <span className="font-serif text-[19px]">{s.headline}</span>
              <span className="block text-[13px] text-soft">{s.vendor?.name}</span>
            </Link>
          ))}
          {!data.recent_stories.length && <p className="text-soft">The first stories are being written.</p>}
        </div>
        <div className="card flex flex-col items-center p-5 text-center">
          <p className="font-semibold">Your market's QR code</p>
          <p className="mt-1 text-[13px] text-soft">Shoppers scan it, tick the vendors they visited, and follow them.</p>
          <QR value={data.qr_url + '?qr=1'} size={180} className="mt-4" />
          <p className="mt-2 break-all font-mono text-[12px] text-soft">{data.qr_url.replace('https://', '')}</p>
        </div>
      </section>
    </Page>
  )
}
