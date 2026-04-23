"""Render the digest as a single self-contained HTML document.

Pure-Python f-string templating (no Jinja2) — matches the repo's
existing style. CSS is GitHub-dark, adapted from
ipl-2025-pressconference-rag-bot/docs/system-design.html.
"""

from __future__ import annotations

from datetime import datetime
from html import escape

from fetcher import Article


CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg:#0d1117; --surface:#161b22; --surface2:#21262d;
  --border:#30363d; --text:#e6edf3; --muted:#8b949e;
  --accent:#58a6ff; --accent2:#3fb950; --warn:#d29922;
  --purple:#bc8cff; --radius:8px; --sidebar-w:260px;
  --font-mono:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;
}
html { scroll-behavior:smooth; }
body {
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  background:var(--bg); color:var(--text); line-height:1.65; display:flex;
}
nav#sidebar {
  position:fixed; top:0; left:0; width:var(--sidebar-w); height:100vh;
  background:var(--surface); border-right:1px solid var(--border);
  overflow-y:auto; padding:24px 0; z-index:100;
}
.nav-logo { padding:0 20px 20px; border-bottom:1px solid var(--border); margin-bottom:12px; }
.nav-logo .badge {
  font-size:11px; font-weight:600; letter-spacing:.05em;
  background:#1c3a5e; color:var(--accent);
  padding:2px 8px; border-radius:20px; border:1px solid var(--accent);
  display:inline-block; margin-bottom:8px;
}
.nav-logo h2 { font-size:14px; color:var(--text); line-height:1.4; }
.nav-section {
  font-size:11px; font-weight:600; letter-spacing:.08em;
  text-transform:uppercase; color:var(--muted); padding:16px 20px 4px;
}
nav#sidebar a {
  display:block; padding:6px 20px; color:var(--muted);
  text-decoration:none; font-size:13px; transition:all .15s;
  border-left:3px solid transparent;
}
nav#sidebar a:hover, nav#sidebar a.active {
  color:var(--accent); background:rgba(88,166,255,.08);
  border-left-color:var(--accent);
}
main {
  margin-left:var(--sidebar-w); max-width:980px;
  padding:48px 48px 120px; flex:1;
}
.hero {
  background:linear-gradient(135deg,#0d2137 0%,#0d1117 60%);
  border:1px solid var(--border); border-radius:var(--radius);
  padding:36px 44px; margin-bottom:40px; position:relative; overflow:hidden;
}
.hero::before {
  content:'\\1F4F0'; position:absolute; right:36px; top:24px;
  font-size:72px; opacity:.12;
}
.hero h1 { font-size:26px; font-weight:700; margin-bottom:8px; line-height:1.3; }
.hero p { color:var(--muted); font-size:15px; max-width:640px; }
.hero .meta { margin-top:24px; display:flex; gap:24px; flex-wrap:wrap; }
.meta-item { font-size:13px; color:var(--muted); }
.meta-item strong { color:var(--text); }
section { margin-bottom:48px; }
h2 {
  font-size:22px; font-weight:700; padding-bottom:10px;
  margin-bottom:20px; border-bottom:1px solid var(--border);
  scroll-margin-top:24px;
}
.card {
  background:var(--surface); border:1px solid var(--border);
  border-radius:var(--radius); padding:20px 22px; margin-bottom:14px;
  transition:border-color .15s;
}
.card:hover { border-color:var(--accent); }
.card-title {
  font-size:16px; font-weight:600; margin-bottom:6px; line-height:1.4;
}
.card-title a { color:var(--text); text-decoration:none; }
.card-title a:hover { color:var(--accent); text-decoration:underline; }
.card-meta {
  font-size:12px; color:var(--muted); margin-bottom:10px;
  display:flex; flex-wrap:wrap; gap:12px;
}
.card-meta .author { color:var(--accent); }
.card-meta .claps::before { content:'\\1F44F  '; }
.card-meta .read::before { content:'\\23F1\\FE0F  '; }
.card-meta .tag-pill {
  font-size:10px; font-weight:600; padding:1px 8px; border-radius:20px;
  background:#2a1f4e; color:var(--purple); border:1px solid var(--purple);
  letter-spacing:.04em; text-transform:lowercase;
}
.card-snippet {
  font-size:14px; color:var(--text); margin-bottom:10px; line-height:1.6;
}
.card-link {
  font-size:13px; color:var(--accent); text-decoration:none;
  font-weight:500;
}
.card-link:hover { text-decoration:underline; }
.empty {
  border:1px dashed var(--border); border-radius:var(--radius);
  padding:24px; color:var(--muted); text-align:center; font-size:14px;
}
.warn-banner {
  background:#2d2005; border:1px solid var(--warn);
  color:var(--warn); padding:10px 14px; border-radius:var(--radius);
  font-size:13px; margin-bottom:14px;
}
table.summary {
  width:100%; border-collapse:collapse; margin-top:8px;
  font-size:13px; background:var(--surface);
  border:1px solid var(--border); border-radius:var(--radius);
  overflow:hidden;
}
table.summary thead {
  background:var(--surface2); font-family:var(--font-mono);
  font-size:12px; letter-spacing:.04em; text-transform:uppercase;
}
table.summary th {
  text-align:left; padding:12px 14px; color:var(--muted);
  font-weight:600; border-bottom:1px solid var(--border);
}
table.summary td {
  padding:12px 14px; border-bottom:1px solid var(--border);
  vertical-align:top; color:var(--text);
}
table.summary tbody tr:last-child td { border-bottom:none; }
table.summary tbody tr:nth-child(even) { background:rgba(255,255,255,.015); }
table.summary td.idx { color:var(--muted); font-family:var(--font-mono); width:32px; }
table.summary td.topic { color:var(--purple); white-space:nowrap; }
table.summary td.title a { color:var(--text); text-decoration:none; font-weight:500; }
table.summary td.title a:hover { color:var(--accent); text-decoration:underline; }
table.summary td.author { color:var(--muted); white-space:nowrap; }
table.summary td.url a {
  color:var(--accent); text-decoration:none; font-family:var(--font-mono);
  font-size:11px;
}
table.summary td.url a:hover { text-decoration:underline; }
footer {
  margin-top:64px; padding-top:24px; border-top:1px solid var(--border);
  color:var(--muted); font-size:12px; text-align:center;
}
@media (max-width:900px) {
  nav#sidebar { display:none; }
  main { margin-left:0; padding:24px; }
}
"""


JS = """
const links = document.querySelectorAll('nav#sidebar a');
const sections = document.querySelectorAll('main section[id]');
const obs = new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (e.isIntersecting) {
      const id = e.target.id;
      links.forEach(l => l.classList.toggle('active', l.getAttribute('href') === '#' + id));
    }
  });
}, { rootMargin: '-30% 0px -60% 0px' });
sections.forEach(s => obs.observe(s));
"""


def _topic_anchor(topic: str) -> str:
    return "topic-" + topic.lower().replace(" ", "-").replace("/", "-").replace("(", "").replace(")", "")


def _card(article: Article) -> str:
    parts = [f'<span class="author">{escape(article.author)}</span>']
    if article.read_time_min:
        parts.append(f'<span class="read">{article.read_time_min} min read</span>')
    if article.claps:
        parts.append(f'<span class="claps">{article.claps:,}</span>')
    if article.source_tag:
        parts.append(f'<span class="tag-pill">#{escape(article.source_tag)}</span>')
    meta = " ".join(parts)

    snippet_html = (
        f'<div class="card-snippet">{escape(article.snippet)}</div>'
        if article.snippet
        else ""
    )

    return f"""
    <article class="card">
      <div class="card-title"><a href="{escape(article.url)}" target="_blank" rel="noopener">{escape(article.title)}</a></div>
      <div class="card-meta">{meta}</div>
      {snippet_html}
      <a class="card-link" href="{escape(article.url)}" target="_blank" rel="noopener">Read on Medium →</a>
    </article>
    """


def _section(topic: str, articles: list[Article]) -> str:
    anchor = _topic_anchor(topic)
    if not articles:
        body = '<div class="empty">No new articles in the last 24 hours for this topic.</div>'
    else:
        body = "\n".join(_card(a) for a in articles)
    return f"""
    <section id="{anchor}">
      <h2>{escape(topic)}</h2>
      {body}
    </section>
    """


def _summary_table(results: dict[str, list[Article]]) -> str:
    rows: list[str] = []
    idx = 1
    for topic, articles in results.items():
        for art in articles:
            rows.append(f"""
            <tr>
              <td class="idx">{idx}</td>
              <td class="topic">{escape(topic)}</td>
              <td class="title"><a href="{escape(art.url)}" target="_blank" rel="noopener">{escape(art.title)}</a></td>
              <td class="author">{escape(art.author)}</td>
              <td class="url"><a href="{escape(art.url)}" target="_blank" rel="noopener">{escape(art.url)}</a></td>
            </tr>
            """)
            idx += 1
    if not rows:
        rows.append('<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:24px;">No articles fetched today.</td></tr>')
    return f"""
    <table class="summary">
      <thead>
        <tr><th>#</th><th>Topic</th><th>Article Title</th><th>Author</th><th>URL</th></tr>
      </thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
    """


def render_html(date: datetime, results: dict[str, list[Article]]) -> str:
    """Build the full HTML document for `results` keyed by topic display name."""
    total = sum(len(v) for v in results.values())
    populated_topics = sum(1 for v in results.values() if v)
    date_str = date.strftime("%A, %B %d, %Y")

    sidebar_links = "\n".join(
        f'<a href="#{_topic_anchor(t)}">{escape(t)}</a>' for t in results
    )
    sections = "\n".join(_section(t, arts) for t, arts in results.items())
    table = _summary_table(results)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Field Monitor — {escape(date_str)}</title>
  <style>{CSS}</style>
</head>
<body>
  <nav id="sidebar">
    <div class="nav-logo">
      <span class="badge">Field Monitor</span>
      <h2>Daily Medium Digest</h2>
      <div style="font-size:12px; color:var(--muted); margin-top:6px;">{escape(date_str)}</div>
    </div>
    <div class="nav-section">Topics</div>
    {sidebar_links}
    <div class="nav-section">Index</div>
    <a href="#index">All Articles</a>
  </nav>
  <main>
    <div class="hero">
      <h1>Software Architecture — Daily Digest</h1>
      <p>Curated from Medium, grouped by topic. Top {total} articles from the last 24 hours.</p>
      <div class="meta">
        <div class="meta-item"><strong>{date_str}</strong></div>
        <div class="meta-item"><strong>{total}</strong> articles</div>
        <div class="meta-item"><strong>{populated_topics} / {len(results)}</strong> topics with new content</div>
      </div>
    </div>
    {sections}
    <section id="index">
      <h2>All Articles</h2>
      {table}
    </section>
    <footer>Generated by Field Monitor · {date.strftime("%Y-%m-%d %H:%M")} local</footer>
  </main>
  <script>{JS}</script>
</body>
</html>
"""
