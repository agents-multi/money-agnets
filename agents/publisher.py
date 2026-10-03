import html as H, json, re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

CSS = ("body{font-family:Arial,sans-serif;max-width:760px;margin:0 auto;padding:16px;line-height:1.65;color:#222}"
       "a{color:#0b5fff}h1,h2{line-height:1.25}footer{margin-top:40px;font-size:.85em;color:#666}")


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:80]


def page(cfg, title, desc, body, canonical="", home="index.html"):
    can = f'<link rel="canonical" href="{canonical}">' if canonical else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{H.escape(title)}</title><meta name="description" content="{H.escape(desc)}">{can}
<style>{CSS}</style></head><body>
<nav><a href="{home}">&larr; {H.escape(cfg['site_name'])}</a></nav>
{body}
<footer>{H.escape(cfg['disclosure'])}</footer></body></html>"""


def run(cfg, topic, html_body):
    slug = slugify(topic["title"])
    posts_file = DOCS / "posts.json"
    posts = json.loads(posts_file.read_text()) if posts_file.exists() else []
    if any(p["slug"] == slug for p in posts):          # idempotent: never double-publish
        return None
    text = re.sub(r"<[^>]+>", " ", html_body)
    desc = " ".join(text.split())[:155]
    base = cfg.get("site_url", "").rstrip("/")
    body = f"<h1>{H.escape(topic['title'])}</h1>\n{html_body}"
    (DOCS / "posts").mkdir(parents=True, exist_ok=True)
    (DOCS / "posts" / f"{slug}.html").write_text(
        page(cfg, topic["title"], desc, body, f"{base}/posts/{slug}.html" if base else "", home="../index.html"),
        encoding="utf-8")
    posts.insert(0, {"slug": slug, "title": topic["title"], "date": date.today().isoformat(), "desc": desc})
    posts_file.write_text(json.dumps(posts, indent=2))
    _rebuild_index(cfg, posts, base)
    return f"{base}/posts/{slug}.html" if base else f"posts/{slug}.html"


def _rebuild_index(cfg, posts, base):
    items = "\n".join(
        f'<li><a href="posts/{p["slug"]}.html">{H.escape(p["title"])}</a> <small>({p["date"]})</small></li>'
        for p in posts)
    body = f"<h1>{H.escape(cfg['site_name'])}</h1><p>{H.escape(cfg['site_tagline'])}</p><ul>{items}</ul>"
    (DOCS / "index.html").write_text(
        page(cfg, cfg["site_name"], cfg["site_tagline"], body, home="index.html"), encoding="utf-8")
    if base:
        urls = [f"{base}/"] + [f"{base}/posts/{p['slug']}.html" for p in posts]
        sm = ('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
              + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>")
        (DOCS / "sitemap.xml").write_text(sm)
        (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")
