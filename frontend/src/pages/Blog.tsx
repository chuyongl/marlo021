import { useNavigate } from 'react-router-dom'

export const BLOG_POSTS = [
  {
    slug: 'how-marlo-thinks',
    title: 'How Marlo thinks: inside the content generation pipeline',
    subtitle: 'A look at the multi-agent system behind every post Marlo creates — from triage to quality check to feedback loop.',
    category: 'Engineering',
    date: 'April 2026',
    readTime: '6 min read',
    featured: true,
  },
  {
    slug: 'content-strategy',
    title: 'How Marlo decides what to post (and when)',
    subtitle: 'The strategy agent reads your metrics, approval history, and brand profile before writing a single word. Here\'s how.',
    category: 'Engineering',
    date: 'Coming soon',
    readTime: '5 min read',
    featured: false,
    comingSoon: true,
  },
  {
    slug: 'morning-briefing',
    title: 'Building the morning briefing: what runs at 8am every day',
    subtitle: 'How Marlo pulls overnight data, generates recommendations, and sends a personalized briefing — all before you wake up.',
    category: 'Product',
    date: 'Coming soon',
    readTime: '4 min read',
    featured: false,
    comingSoon: true,
  },
]

export function Blog() {
  const navigate = useNavigate()

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
        .blog-page { min-height:100vh; background:#0a0a0a; color:#f0ece4; font-family:'DM Sans',sans-serif; }
        .blog-nav { position:sticky; top:0; z-index:100; display:flex; align-items:center; justify-content:space-between; padding:20px 48px; background:rgba(10,10,10,0.9); backdrop-filter:blur(16px); border-bottom:1px solid rgba(255,255,255,0.08); }
        .blog-logo { font-family:'Instrument Serif',serif; font-size:22px; color:#f0ece4; text-decoration:none; letter-spacing:-0.5px; }
        .blog-logo span { color:#c8f060; }
        .blog-nav-back { font-size:13px; color:#666; text-decoration:none; transition:color 0.2s; }
        .blog-nav-back:hover { color:#f0ece4; }
        .blog-header { max-width:860px; margin:0 auto; padding:80px 24px 48px; }
        .blog-label { font-size:11px; font-weight:600; letter-spacing:2px; text-transform:uppercase; color:#c8f060; margin-bottom:16px; }
        .blog-header h1 { font-family:'Instrument Serif',serif; font-size:clamp(36px,5vw,56px); line-height:1.05; letter-spacing:-1.5px; color:#ffffff; margin-bottom:16px; }
        .blog-header p { font-size:17px; color:#666; line-height:1.6; max-width:520px; }
        .blog-grid { max-width:860px; margin:0 auto; padding:0 24px 100px; display:grid; gap:2px; }
        .blog-card { background:#141414; border:1px solid rgba(255,255,255,0.06); border-radius:16px; padding:32px; cursor:pointer; transition:border-color 0.2s, background 0.2s; position:relative; overflow:hidden; }
        .blog-card:hover { border-color:rgba(255,255,255,0.15); background:#181818; }
        .blog-card.featured { border-color:rgba(200,240,96,0.2); }
        .blog-card.featured::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,transparent,#c8f060,transparent); }
        .blog-card.coming-soon { opacity:0.5; cursor:default; }
        .blog-card.coming-soon:hover { border-color:rgba(255,255,255,0.06); background:#141414; }
        .blog-card-meta { display:flex; align-items:center; gap:12px; margin-bottom:16px; }
        .blog-category { font-size:11px; font-weight:600; letter-spacing:1.5px; text-transform:uppercase; color:#c8f060; }
        .blog-date { font-size:12px; color:#555; }
        .blog-readtime { font-size:12px; color:#555; }
        .blog-card h2 { font-family:'Instrument Serif',serif; font-size:clamp(22px,3vw,30px); line-height:1.2; letter-spacing:-0.5px; color:#ffffff; margin-bottom:12px; }
        .blog-card p { font-size:14px; color:#888; line-height:1.7; margin-bottom:20px; }
        .blog-card-cta { font-size:13px; color:#c8f060; font-weight:500; display:flex; align-items:center; gap:6px; }
        .coming-badge { display:inline-block; background:rgba(255,255,255,0.06); border-radius:100px; padding:4px 12px; font-size:11px; color:#555; font-weight:500; }
        @media (max-width:600px) { .blog-nav { padding:16px 20px; } .blog-header { padding:60px 20px 32px; } }
      `}</style>

      <div className="blog-page">
        <nav className="blog-nav">
          <a className="blog-logo" href="/">marlo<span>021.</span></a>
          <a className="blog-nav-back" href="/">← Back to home</a>
        </nav>

        <div className="blog-header">
          <div className="blog-label">Blog</div>
          <h1>How Marlo works</h1>
          <p>Deep dives into the systems, decisions, and engineering behind Marlo's AI marketing agent.</p>
        </div>

        <div className="blog-grid">
          {BLOG_POSTS.map(post => (
            <div
              key={post.slug}
              className={`blog-card ${post.featured ? 'featured' : ''} ${post.comingSoon ? 'coming-soon' : ''}`}
              onClick={() => !post.comingSoon && navigate(`/blog/${post.slug}`)}
            >
              <div className="blog-card-meta">
                <span className="blog-category">{post.category}</span>
                <span className="blog-date">{post.date}</span>
                <span className="blog-readtime">{post.readTime}</span>
              </div>
              <h2>{post.title}</h2>
              <p>{post.subtitle}</p>
              {post.comingSoon
                ? <span className="coming-badge">Coming soon</span>
                : <div className="blog-card-cta">Read article →</div>
              }
            </div>
          ))}
        </div>
      </div>
    </>
  )
}