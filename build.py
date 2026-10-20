#!/usr/bin/env python3
"""Static site generator for reconnaissancetechnologies.com.

Reads content/site.json and content/pages/*.json and writes the site to dist/.
No dependencies beyond the Python 3 standard library:

    python3 build.py            # build into dist/
    python3 build.py --serve    # build, then serve dist/ on http://localhost:8000
"""
import html
import json
import math
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
DIST = ROOT / "dist"
SITE = json.loads((CONTENT / "site.json").read_text(encoding="utf-8"))
PAGES = {
    p.stem.replace("--", "/"): json.loads(p.read_text(encoding="utf-8"))
    for p in sorted((CONTENT / "pages").glob("*.json"))
}
CONTACT_HREF = "/our-company/contact-us"


def e(text):
    return html.escape(str(text or ""), quote=True)


# ---------------------------------------------------------------- icons
ARROW_R = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
ARROW_DIAG = '<svg class="arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M7 7l10 10M17 8v9H8"/></svg>'
ARROW_OUT = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M7 17L17 7M8 7h9v9"/></svg>'
CHEVRON = '<svg viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M2 3.5l3 3 3-3"/></svg>'
DOTS = '<svg class="dots" viewBox="0 0 22 12" fill="currentColor" aria-hidden="true"><circle cx="3" cy="9" r="1.6"/><circle cx="9" cy="3" r="1.6"/><circle cx="15" cy="9" r="1.6"/></svg>'


# ---------------------------------------------------------------- helpers
class Ctx:
    """Per-page rendering context: knows how deep the page sits so every
    internal link can be relative (works on any host, sub-path or file://)."""

    def __init__(self, slug):
        self.slug = slug.strip("/")
        depth = len(self.slug.split("/")) if self.slug else 0
        self.rel = "../" * depth

    def url(self, href):
        if not href:
            return "#"
        if href.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            return href
        path = href.strip("/")
        return f"{self.rel}{path}/" if path else (self.rel or "./")

    def asset(self, path):
        return f"{self.rel}assets/{path}"


def two_tone(title, accent=None):
    """Orbit-style heading: the tail of the sentence switches to the accent colour."""
    title = title.strip()
    if accent and accent in title:
        head, tail = title.split(accent, 1)
        return f'{e(head)}<span class="accent">{e(accent)}</span>{e(tail)}'
    for sep in (" — ", ": ", " – "):
        if sep in title:
            head, tail = title.split(sep, 1)
            return f'{e(head)}{e(sep.rstrip())} <span class="accent">{e(tail)}</span>'
    words = title.split()
    if len(words) < 4:
        return e(title)
    cut = math.ceil(len(words) * 0.5)
    return f'{e(" ".join(words[:cut]))} <span class="accent">{e(" ".join(words[cut:]))}</span>'


def wordmark(word, cls="wordmark"):
    """Giant word whose last letters smear sideways like a motion blur."""
    word = word.strip()
    letters = word.replace(" ", "")
    tail = 2 if len(letters) > 4 else 1
    if len(word) <= tail:
        return f'<p class="{cls}" aria-hidden="true">{e(word)}</p>'
    long_cls = " is-long" if len(word) > 7 else ""
    return (f'<p class="{cls}{long_cls}" aria-hidden="true">{e(word[:-tail])}'
            f'<span class="trail">{e(word[-tail:])}</span></p>')


def stat_value(value):
    m = re.match(r"^([\d.,]+)\s*([kKmM]?)(\+?)$", value)
    if not m:
        return e(value)
    num, unit, plus = m.groups()
    return f'{e(num)}{e(unit)}<small>{e(plus)}</small>' if plus else f"{e(num)}{e(unit)}"


def initials(name):
    return "".join(w[0] for w in name.split()[:2]).upper()


def para(text, cls="lede"):
    return f'<p class="{cls}">{e(text)}</p>' if text else ""


def page_hero_body(slug):
    p = PAGES.get(slug)
    return p["body"] if p else ""


# ---------------------------------------------------------------- chrome
def nav_menus(c):
    by_group = {}
    for s in SITE["services"]:
        by_group.setdefault(s["group"], []).append(s)

    def links(items):
        return "".join(f'<li><a href="{c.url(i["slug"])}">{e(i["name"])}</a></li>' for i in items)

    services = f'''
      <div><h4>Offering</h4><ul>{links(by_group["Offering"])}</ul></div>
      <div><h4>Trending Services</h4><ul>{links(by_group["Trending"])}</ul>
        <h4 style="margin-top:20px">Service Models</h4><ul>{links(SITE["service_models"])}</ul></div>
      <div><h4>Industries We Serve</h4><ul>{links(SITE["industries"])}</ul></div>'''
    products = "".join(
        f'<li><a href="{e(p["href"])}" target="_blank" rel="noopener">{e(p["name"])}'
        f'{f"<span class=badge>{e(p["badge"])}</span>" if p["badge"] else ARROW_OUT}</a></li>'
        for p in SITE["products"])
    sols = "".join(f'<li><a href="{c.url(s["industry"])}">{e(s["name"])}</a></li>' for s in SITE["solutions"])
    solutions = f'''
      <div><h4>Product Offerings</h4><ul>{products}</ul></div>
      <div><h4>Solutions</h4><ul>{sols}</ul></div>
      <div class="menu-feature"><p>Discover how our expertise has helped elevate businesses and streamline processes.</p>
        <a class="link-underline" href="{c.url("our-solutions")}">Products &amp; Solutions Overview</a></div>'''
    company = f'''
      <div><h4>Who We Are</h4><ul>{links(SITE["company"])}</ul></div>
      <div><h4>Insights</h4><ul>{links(SITE["insights"])}
        <li><a href="{c.url("our-work/portfolio")}">Our Work</a></li></ul></div>
      <div class="menu-feature"><h4 style="margin:0">Talk to an Expert</h4>
        <p>One of our experts would love to respond to your queries.</p>
        <a class="pill pill--ink" href="{c.url(CONTACT_HREF)}">Speak to an Expert</a></div>'''
    return services, solutions, company


def header(c, current):
    services, solutions, company = nav_menus(c)

    def item(key, label, menu):
        return f'''<div class="nav-item">
          <button class="nav-link" type="button" aria-expanded="false" aria-controls="menu-{key}"
            {'aria-current="page"' if current == key else ''}>{label}{CHEVRON}</button>
          <div class="menu" id="menu-{key}">{menu}</div></div>'''

    def drawer_group(title, items):
        lis = "".join(f'<li><a href="{c.url(i["slug"]) if "slug" in i else e(i["href"])}">{e(i["name"])}</a></li>' for i in items)
        return f"<details><summary>{e(title)}</summary><ul>{lis}</ul></details>"

    drawer = "".join([
        drawer_group("Services", SITE["services"]),
        drawer_group("Industries", SITE["industries"]),
        drawer_group("Solutions", SITE["products"] + [{"slug": "our-solutions", "name": "Products & Solutions Overview"}]),
        drawer_group("Who We Are", SITE["company"] + SITE["service_models"]),
        drawer_group("Insights", SITE["insights"] + [{"slug": "our-work/portfolio", "name": "Our Work"}]),
    ])
    return f'''
<header class="site-header">
  <div class="frame"><div class="bar">
    <a class="brand" href="{c.url("/")}" aria-label="Reconnaissance Technologies home">
      <img src="{c.asset("img/logo-white.svg")}" alt="Reconnaissance Technologies" width="128" height="30">
      <span class="brand-meta micro"><span>Est. 2020</span><span>Abuja, NG</span></span>
    </a>
    <nav class="nav" aria-label="Main">
      <div class="nav-col">{item("services", "Services", services)}{item("solutions", "Solutions", solutions)}</div>
      <div class="nav-col">{item("company", "Who We Are", company)}
        <a class="nav-link" href="{c.url("our-work/portfolio")}" {'aria-current="page"' if current == "work" else ''}>Our Work</a></div>
    </nav>
    <a class="pill pill--white header-cta" href="{c.url(CONTACT_HREF)}">Get in Touch</a>
    <button class="burger" type="button" aria-label="Open menu" aria-controls="drawer" aria-expanded="false"><span></span><span></span></button>
  </div></div>
</header>
<div class="sticky-bar" aria-hidden="true">
  <a href="{c.url("/")}" tabindex="-1"><img src="{c.asset("img/logo-white.svg")}" alt="" width="94" height="22"></a>
  <nav>
    <a class="nav-link" tabindex="-1" href="{c.url("our-services")}">Services</a>
    <a class="nav-link" tabindex="-1" href="{c.url("our-solutions")}">Solutions</a>
    <a class="nav-link" tabindex="-1" href="{c.url("our-company/about-us")}">Who We Are</a>
    <a class="nav-link" tabindex="-1" href="{c.url("our-work/portfolio")}">Our Work</a>
  </nav>
  <a class="pill pill--white" tabindex="-1" href="{c.url(CONTACT_HREF)}">Get in Touch</a>
</div>
<div class="drawer" id="drawer" role="dialog" aria-modal="true" aria-label="Menu">
  <div class="drawer-top">
    <img src="{c.asset("img/logo-white.svg")}" alt="Reconnaissance Technologies" width="110" height="26">
    <button class="burger" type="button" aria-label="Close menu" data-close style="display:block"><span style="transform:translateY(3px) rotate(45deg)"></span><span style="transform:translateY(-3px) rotate(-45deg)"></span></button>
  </div>
  <a class="drawer-home micro" href="{c.url("/")}">Home</a>
  {drawer}
  <a class="pill pill--white" href="{c.url(CONTACT_HREF)}">Get in Touch</a>
</div>'''


def footer(c):
    ct = SITE["contact"]

    def col(title, items):
        lis = "".join(f'<li><a href="{c.url(i["slug"])}">{e(i["name"])}</a></li>' for i in items)
        return f"<div><h4>{e(title)}</h4><ul>{lis}</ul></div>"

    social = "".join(f'<li><a href="{e(s["href"])}" target="_blank" rel="noopener">{e(s["label"])}</a></li>' for s in SITE["social"])
    return f'''
<footer class="site-footer on-dark">
  <div class="frame">
    <div class="footer-top">
      <div>
        <span class="eyebrow">Enquiry</span>
        <h2 class="h-l" style="margin-top:18px">Transform <span class="accent">Your Business</span></h2>
        <div class="contact-lines">
          <span>{e(", ".join(ct["address"]))}</span>
          <a href="{e(ct["phone_href"])}">{e(ct["phone"])}</a>
          <a href="mailto:{e(ct["email"])}">{e(ct["email"])}</a>
        </div>
        <div style="margin-top:28px"><a class="pill pill--white" href="{c.url(CONTACT_HREF)}">Speak with an Expert {ARROW_R}</a></div>
      </div>
      <div class="footer-cols">
        {col("Services", SITE["services"][:7])}
        {col("Industries", SITE["industries"])}
        {col("Company", SITE["company"] + SITE["service_models"])}
        <div><h4>Follow</h4><ul>{social}</ul></div>
      </div>
    </div>
  </div>
  <p class="footer-word" aria-hidden="true">Reconnaissan<span class="trail">ce</span></p>
  <div class="footer-bottom"><div class="frame" style="display:flex;flex-wrap:wrap;justify-content:space-between;gap:16px">
    <span>&copy; <span data-year>2026</span> {e(SITE["legal"])}. All Rights Reserved.</span>
    <nav aria-label="Legal"><a href="{c.url("our-company/privacy-policy")}">Privacy Policy</a><a href="{c.url(CONTACT_HREF)}">Contact</a><a href="{c.url("our-company/career-overview")}">Careers</a></nav>
  </div></div>
</footer>'''


def document(c, title, description, body, current=""):
    full_title = title if title.startswith(SITE["name"]) else f"{title} | {SITE['name']}"
    canonical = SITE["url"] + ("/" + c.slug if c.slug else "")
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description[:300])}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(description[:300])}">
<meta property="og:type" content="website">
<meta property="og:url" content="{e(canonical)}">
<meta name="theme-color" content="#04050c">
<link rel="icon" type="image/png" href="{c.asset("img/favicon.png")}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Sora:wght@300;400;500&display=swap">
<link rel="stylesheet" href="{c.asset("css/style.css")}">
<script>document.documentElement.classList.add('js')</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">
  <!-- horizontal-only blur for the hero wordmark: a real motion smear that tapers off -->
  <filter id="motion-lg" x="-20%" y="-40%" width="280%" height="180%" color-interpolation-filters="sRGB">
    <feGaussianBlur in="SourceGraphic" stdDeviation="5 3" result="near"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="16 6" result="mid0"/>
    <feOffset in="mid0" dx="18" result="mid1"/>
    <feComponentTransfer in="mid1" result="mid"><feFuncA type="linear" slope=".75"/></feComponentTransfer>
    <feGaussianBlur in="SourceGraphic" stdDeviation="34 10" result="far0"/>
    <feOffset in="far0" dx="48" result="far1"/>
    <feComponentTransfer in="far1" result="far"><feFuncA type="linear" slope=".45"/></feComponentTransfer>
    <feMerge><feMergeNode in="far"/><feMergeNode in="mid"/><feMergeNode in="near"/></feMerge>
  </filter>
  <filter id="motion-sm" x="-20%" y="-60%" width="300%" height="220%" color-interpolation-filters="sRGB">
    <feGaussianBlur in="SourceGraphic" stdDeviation="3 2.5" result="near"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="9 5" result="mid0"/>
    <feOffset in="mid0" dx="8" result="mid1"/>
    <feComponentTransfer in="mid1" result="mid"><feFuncA type="linear" slope=".7"/></feComponentTransfer>
    <feGaussianBlur in="SourceGraphic" stdDeviation="18 7" result="far0"/>
    <feOffset in="far0" dx="20" result="far1"/>
    <feComponentTransfer in="far1" result="far"><feFuncA type="linear" slope=".4"/></feComponentTransfer>
    <feMerge><feMergeNode in="far"/><feMergeNode in="mid"/><feMergeNode in="near"/></feMerge>
  </filter>
</svg>
{header(c, current)}
<main id="main">
{body}
</main>
{footer(c)}
<script src="{c.asset("js/main.js")}" defer></script>
</body>
</html>
'''


# ---------------------------------------------------------------- blocks
def hero(c, word, title, body="", cta=None, kicker="", crumbs=None, extra="", tag=None, title_html=None, word_html=None):
    crumbs_html = ""
    if crumbs:
        parts = [f'<a href="{c.url(h)}">{e(n)}</a>' if h else f"<span>{e(n)}</span>" for n, h in crumbs]
        crumbs_html = f'<nav class="crumbs micro" aria-label="Breadcrumb">{" <span>/</span> ".join(parts)}</nav>'
    cta_html = ""
    if cta:
        cta_html = f'<div class="hero-actions"><a class="link-underline" href="{c.url(cta["href"])}">{e(cta["label"])} {ARROW_R}</a></div>'
    words = title.split()
    if title_html is None:
        cut = max(1, math.ceil(len(words) * 0.55))
        title_html = f'{e(" ".join(words[:cut]))} <span class="fade">{e(" ".join(words[cut:]))}</span>'
    tag = tag or ([kicker, "Reconnaissance", "Technologies"] if kicker else ["Future Ready", "Software", "Development"])
    tag_html = "".join(f"<span>{e(t)}</span>" for t in tag)
    return f'''
<div class="hero-wrap"><div class="frame">
  <section class="hero on-dark" aria-labelledby="page-title">
    <video class="hero-video" autoplay muted loop playsinline preload="metadata" poster="{c.asset("video/hero-poster.jpg")}" aria-hidden="true" tabindex="-1">
      <source src="{c.asset("video/hero.webm")}" type="video/webm">
      <source src="{c.asset("video/hero.mp4")}" type="video/mp4">
    </video>
    {extra}
    <div class="hero-copy">
      {crumbs_html}
      <h1 class="hero-title" id="page-title">{title_html}</h1>
      {para(body, "hero-body")}
      {cta_html}
    </div>
    <div class="hero-tag micro">{tag_html}</div>
    {word_html or wordmark(word)}
  </section>
</div></div>'''


def head_block(sec, dark=False, level="h-l"):
    eyebrow = f'<span class="eyebrow">{e(sec["eyebrow"])}</span>' if sec.get("eyebrow") else ""
    side = f'<div class="head-side">{eyebrow}{para(sec.get("body"))}</div>'
    return f'''<div class="panel-head">{side}<h2 class="{level}">{two_tone(sec["title"], sec.get("accent"))}</h2></div>'''


def stats_block(items, feature_last=True):
    n = len(items)
    cells = []
    for i, s in enumerate(items):
        feature = " stat--feature" if feature_last and i == n - 1 else ""
        cells.append(f'''<div class="stat{feature}">
          <div class="stat-value">{stat_value(s["value"])}</div>
          <div class="stat-label">{e(s.get("label", ""))}</div>
          {para(s.get("body"), "stat-body")}
          {DOTS}
        </div>''')
    return f'<div class="stats" style="--n:{n}">{"".join(cells)}</div>'


def sec_stats(c, sec, first=False, caption=None):
    caption = caption or "Live metrics from projects delivered by our teams"
    return f'''
<section class="{'rise' if first else 'section--tight'}"><div class="frame"><div class="panel reveal">
  <div class="stats-wrap">
    <div class="stats-top">
      <h2 class="h-l">{two_tone(sec["title"], sec.get("accent"))}</h2>
      <div class="side">{f'<span class="eyebrow">{e(sec["eyebrow"])}</span>' if sec.get("eyebrow") else ""}{para(sec.get("body"))}</div>
    </div>
    {stats_block(sec["items"])}
    <div class="stats-foot"><span class="micro">{e(caption)}</span>
      <a class="link-underline" href="{c.url(CONTACT_HREF)}" style="color:var(--ink)">Speak with an Expert</a></div>
  </div>
</div></div></section>'''


def row_item(c, idx, item, label, open_=False, cta=None):
    """One accordion row: number, label + title, teaser, arrow. Opens into a lavender panel."""
    title = item["title"]
    body = item.get("body", "")
    points = item.get("points") or []
    cta = cta or {"label": "Speak with an Expert", "href": CONTACT_HREF}
    left = ""
    if item.get("stat"):
        st = item["stat"]
        left = f'''<div class="mini"><div class="stat-value">{stat_value(st["value"])}</div>
          <div class="mini-foot">{DOTS}<span>{e(st["label"])}</span></div></div>'''
    elif points:
        left = f'<div class="mini"><ul class="points">{"".join(f"<li>{e(p)}</li>" for p in points)}</ul></div>'
    big = ""
    if item.get("stat2"):
        s2 = item["stat2"]
        big = f'<div class="big">{stat_value(s2["value"])}<small>{e(s2["label"])}</small></div>'
    main = f'<div class="row-main">{big}{para(body, "")}</div>'
    plain = ""
    if not left:
        left, main, plain = main, "", " row-panel--plain"
    return f'''
<details class="row"{' open' if open_ else ''}>
  <summary>
    <span class="num-circle">{idx:02d}</span>
    <span><span class="row-label">{e(label)}</span><span class="row-title">{e(title)}</span></span>
    <span class="row-teaser">{e(body)}</span>
    {ARROW_DIAG}
  </summary>
  <div class="row-panel{plain}">{left}{main}<a class="pill pill--ink" href="{c.url(cta["href"])}">{e(cta["label"])}</a></div>
</details>'''


def sec_rows(c, sec, label, first=False, rows=None):
    rows = rows or "".join(row_item(c, i + 1, it, label, open_=(i == 0)) for i, it in enumerate(sec["items"]))
    return f'''
<section class="{'rise' if first else 'section--tight'}"><div class="frame"><div class="panel reveal">
  {head_block(sec)}
  <div class="rows">{rows}</div>
</div></div></section>'''


def rail_card(c, idx, item, active=False):
    href = item.get("href") or CONTACT_HREF
    external = href.startswith("http")
    points = item.get("points") or []
    pts = f'<ul class="card-points">{"".join(f"<li>{e(p)}</li>" for p in points[:6])}</ul>' if points else ""
    target = ' target="_blank" rel="noopener"' if external else ""
    return f'''
<article class="rail-card{' is-active' if active else ''}" tabindex="0">
  <span class="num">{idx:02d}</span>
  <div style="display:grid;gap:14px">
    {DOTS}
    <h3>{e(item["title"])}</h3>
    <div class="card-body">{para(item.get("body"), "")}{pts}</div>
  </div>
  <div class="card-foot">
    <a class="link-underline" href="{c.url(href)}"{target}>{e(item.get("cta", "Explore more"))}</a>
    <a class="circle-btn" href="{c.url(href)}"{target} aria-label="{e(item["title"])}">{ARROW_R}</a>
  </div>
</article>'''


def sec_rail(c, sec):
    cards = "".join(rail_card(c, i + 1, it, i == 0) for i, it in enumerate(sec["items"]))
    eyebrow = f'<span class="eyebrow">{e(sec["eyebrow"])}</span>' if sec.get("eyebrow") else ""
    return f'''
<section class="section rail-section on-dark"><div class="frame">
  <div class="section-head section-head--split reveal">
    <div class="head-side">{eyebrow}{para(sec.get("body"))}</div>
    <h2 class="h-l">{e(sec["title"])}</h2>
  </div>
  <div class="rail" data-rail>{cards}</div>
</div></section>'''


def sec_cta(c, sec, word="Recon"):
    cta = sec.get("cta") or {"label": "Speak with an Expert", "href": CONTACT_HREF}
    return f'''
<section class="section--tight"><div class="frame">
  <div class="cta-band on-dark reveal">
    <h2 class="h-xl">{e(sec["title"])}</h2>
    <div class="side">{para(sec.get("body"))}
      <a class="pill pill--white" href="{c.url(cta["href"])}">{e(cta["label"])} {ARROW_R}</a></div>
    <span class="ghost-word" aria-hidden="true">{e(word)}</span>
  </div>
</div></section>'''


def sec_intro(c, sec, first=False):
    aside = ""
    if sec.get("aside"):
        a = sec["aside"]
        aside = f'''<div class="g-card g-card--feature" style="min-height:0"><h3 class="h-s">{e(a["title"])}</h3>{para(a.get("body"), "")}</div>'''
    stats = f'<div style="margin-top:clamp(28px,4vw,56px)">{stats_block(sec["stats"])}</div>' if sec.get("stats") else ""
    body = sec.get("body", "")
    return f'''
<section class="{'rise' if first else 'section--tight'}"><div class="frame"><div class="panel reveal">
  <div class="panel-head">
    <div class="head-side">{f'<span class="eyebrow">{e(sec["eyebrow"])}</span>' if sec.get("eyebrow") else ""}</div>
    <div style="display:grid;gap:clamp(20px,2.5vw,32px)">
      <h2 class="h-l">{two_tone(sec["title"], sec.get("accent"))}</h2>
      {f'<div class="prose"><p>{e(body)}</p></div>' if body else ""}
      {aside}
    </div>
  </div>
  {stats}
</div></div></section>'''


def sec_grid(c, sec, first=False):
    cards = "".join(f'''<article class="g-card{' g-card--feature' if i == 0 else ''}">
        <span class="num">{i + 1:02d}</span>
        <div style="display:grid;gap:10px">{DOTS}<h3 class="h-s">{e(it["title"])}</h3>{para(it.get("body"), "")}
        {f'<span class="micro" style="color:var(--accent)">{e(it["year"])}</span>' if it.get("year") else ""}</div>
      </article>''' for i, it in enumerate(sec["items"]))
    return f'''
<section class="{'rise' if first else 'section--tight'}"><div class="frame"><div class="panel reveal">
  {head_block(sec)}
  <div class="grid-cards">{cards}</div>
</div></div></section>'''


def sec_tabs(c, sec, groups, dark=False, uid="tabs"):
    tabs, panels = [], []
    for i, (name, items) in enumerate(groups):
        tid = f"{uid}-{i}"
        tabs.append(f'<button class="tab" role="tab" id="t-{tid}" aria-controls="p-{tid}" aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">{e(name)}</button>')
        chips = "".join(f'<span class="chip">{e(x)}</span>' for x in items)
        panels.append(f'<div class="chips" role="tabpanel" id="p-{tid}" aria-labelledby="t-{tid}"{"" if i == 0 else " hidden"}>{chips}</div>')
    inner = f'<div class="tabs" role="tablist" aria-label="{e(sec["title"])}">{"".join(tabs)}</div>{"".join(panels)}'
    if dark:
        eyebrow = f'<span class="eyebrow">{e(sec["eyebrow"])}</span>' if sec.get("eyebrow") else ""
        return f'''
<section class="section on-dark"><div class="frame">
  <div class="section-head section-head--split reveal"><div class="head-side">{eyebrow}{para(sec.get("body"))}</div>
    <h2 class="h-l" style="justify-self:end;max-width:20ch">{e(sec["title"])}</h2></div>
  <div class="reveal" data-tabs>{inner}</div>
</div></section>'''
    return f'''
<section class="section--tight"><div class="frame"><div class="panel reveal">
  {head_block(sec)}<div data-tabs>{inner}</div>
</div></div></section>'''


def sec_team(c, sec):
    members = "".join(f'''<article class="member">
        <div class="avatar" aria-hidden="true">{e(initials(m["name"]))}</div>
        <div style="display:grid;gap:8px"><span class="micro role">{e(m["role"])}</span><h3 class="h-m">{e(m["name"])}</h3>{para(m["body"], "")}</div>
        {f'<a class="link-underline" href="{e(m["linkedin"])}" target="_blank" rel="noopener">LinkedIn</a>' if m.get("linkedin") else ""}
      </article>''' for m in sec["items"])
    return f'''
<section class="section--tight"><div class="frame"><div class="panel reveal">
  {head_block(sec)}<div class="team">{members}</div>
</div></div></section>'''


def sec_prose(c, sec, first=False):
    intro = "".join(f"<p>{e(p)}</p>" for p in sec.get("intro", []))
    blocks = "".join(f'''<div class="prose-block"><h3>{e(b["title"])}</h3><div class="prose">
        {"".join(f"<p>{e(p)}</p>" for p in b.get("body", []))}
        {f'<ul class="points">{"".join(f"<li>{e(x)}</li>" for x in b["points"])}</ul>' if b.get("points") else ""}
      </div></div>''' for b in sec["blocks"])
    privacy = SITE["contact"]["privacy"]
    blocks = blocks.replace(e(privacy), f'<a href="mailto:{e(privacy)}" style="color:var(--accent)">{e(privacy)}</a>', 1)
    return f'''
<section class="{'rise' if first else 'section--tight'}"><div class="frame"><div class="panel reveal">
  <div class="panel-head"><div class="head-side"><span class="eyebrow">{e(sec["eyebrow"])}</span></div>
    <div style="display:grid;gap:24px"><h2 class="h-l">{two_tone(sec["title"])}</h2><div class="prose">{intro}</div></div></div>
  <div class="prose-blocks">{blocks}</div>
</div></div></section>'''


def contact_form(c, full=False):
    ct = SITE["contact"]
    services = "".join(f"<option>{e(s['name'])}</option>" for s in SITE["services"])
    extra = ""
    if full:
        extra = f'''
      <div class="field field--full"><label for="f-service">Interested Service</label>
        <select id="f-service" name="service"><option value="">Select interested service</option>{services}</select></div>'''
    nda = '<label class="check field--full"><input type="checkbox" name="nda" value="yes"> I want a copy of a signed NDA</label>' if full else ""
    return f'''
<form class="form" id="enquiry" action="mailto:{e(ct["email"])}" method="post" enctype="text/plain" data-enquiry data-to="{e(ct["email"])}">
  <div class="field"><label for="f-name">Name</label><input id="f-name" name="name" autocomplete="name" required></div>
  <div class="field"><label for="f-email">Email address</label><input id="f-email" name="email" type="email" autocomplete="email" required></div>
  <div class="field"><label for="f-phone">Mobile</label><input id="f-phone" name="mobile" type="tel" autocomplete="tel" placeholder="+234-123-456-7890"></div>
  <div class="field"><label for="f-company">Company</label><input id="f-company" name="company" autocomplete="organization" placeholder="ex. Google"></div>
  {extra}
  <div class="field field--full"><label for="f-msg">{"Project Brief / Enquiries" if full else "Enquiries"}</label><textarea id="f-msg" name="message" required></textarea></div>
  <label class="check field--full"><input type="checkbox" name="privacy" required> <span>I agree with the <a href="{c.url("our-company/privacy-policy")}">privacy policy</a>.</span></label>
  {nda}
  <div class="form-foot"><span class="form-status" role="status" aria-live="polite"></span>
    <button class="pill pill--ink" type="submit">Send Message {ARROW_R}</button></div>
</form>'''


def sec_contact(c, sec, first=False):
    ct = SITE["contact"]
    stats = "".join(f'''<div class="contact-card"><span class="micro" style="color:var(--muted)">{e(s["label"])}</span>
        <div class="stat-value" style="font-size:44px">{stat_value(s["value"])}</div><p>{e(s["body"])}</p></div>''' for s in sec.get("stats", []))
    return f'''
<section class="{'rise' if first else 'section--tight'}" id="contact"><div class="frame"><div class="panel reveal">
  <div class="contact-grid">
    <div class="contact-side">
      <span class="eyebrow">{e(sec.get("eyebrow", "Enquiry"))}</span>
      <h2 class="h-l">{two_tone(sec.get("title", "Get In Touch With Us"))}</h2>
      <div class="contact-card"><h3>{e(ct["country"])}</h3>
        {"".join(f"<span>{e(l)}</span>" for l in ct["address"])}</div>
      <div class="contact-card"><h3>Quick Contact</h3>
        <a href="{e(ct["phone_href"])}">{e(ct["phone"])}</a><a href="{e(ct["quick_href"])}">{e(ct["quick"])}</a></div>
      <div class="contact-card"><h3>General Enquiries</h3><a href="mailto:{e(ct["email"])}">{e(ct["email"])}</a>
        <h3 style="margin-top:12px">Career Opportunities</h3><a href="mailto:{e(ct["careers"])}">{e(ct["careers"])}</a></div>
      {stats}
    </div>
    <div>{contact_form(c, sec.get("full", False))}</div>
  </div>
</div></div></section>'''


def sec_badges(c, sec):
    badges = "".join(f'<a href="{e(a["href"])}" target="_blank" rel="noopener" title="{e(a["name"])}"><img src="{c.asset("img/" + a["img"])}" alt="{e(a["name"])}" loading="lazy"></a>' for a in SITE["awards"])
    return f'''
<section class="section on-dark"><div class="frame">
  <div class="section-head reveal"><div class="head-side"><span class="eyebrow">{e(sec.get("eyebrow", "Recognition"))}</span></div>
    <h2 class="h-l" style="justify-self:end">{e(sec["title"])}</h2></div>
  <div class="badges reveal">{badges}</div>
</div></section>'''


def sec_openings(c, sec):
    return f'''
<section class="section--tight"><div class="frame"><div class="panel reveal">
  {head_block(sec)}
  <div class="empty"><span class="eyebrow">Current Openings</span><h3 class="h-m">{e(sec["empty"])}</h3>
    <p class="lede">We are always happy to hear from talented people. Send your CV to <a href="mailto:{e(sec["email"])}" style="color:var(--accent)">{e(sec["email"])}</a>.</p>
    <a class="pill pill--ink" href="mailto:{e(sec["email"])}">Send your CV</a></div>
</div></div></section>'''


def label_for(page):
    return {"Services": "Service", "Industries": "Solution", "Service Models": "Model", "Who We Are": "Reconnaissance",
            "Insights": "Insight"}.get(page.get("kicker"), "Reconnaissance")


def render_sections(c, page):
    """Turn a page's sections into the Orbit rhythm: the first block is a white
    panel rising over the hero; card groups alternate between white accordion
    lists and dark numbered rails; CTA blocks become dark bands."""
    out, tone = [], "white"
    label = label_for(page)
    for i, sec in enumerate(page["sections"]):
        first = i == 0
        t = sec["type"]
        if t == "stats":
            out.append(sec_stats(c, sec, first)); tone = "dark"
        elif t == "cta":
            out.append(sec_cta(c, sec, page["word"])); tone = "white"
        elif t == "intro":
            out.append(sec_intro(c, sec, first)); tone = "dark"
        elif t == "tabs":
            out.append(sec_tabs(c, sec, [(g["title"], g["points"]) for g in sec["items"]], dark=(tone == "dark" and not first), uid=f"s{i}"))
            tone = "white" if tone == "dark" else "dark"
        elif t == "team":
            out.append(sec_team(c, sec)); tone = "dark"
        elif t == "prose":
            out.append(sec_prose(c, sec, first)); tone = "dark"
        elif t == "contact":
            out.append(sec_contact(c, sec, first)); tone = "dark"
        elif t == "badges":
            out.append(sec_badges(c, sec)); tone = "white"
        elif t == "openings":
            out.append(sec_openings(c, sec)); tone = "dark"
        elif t == "cards":
            items = sec.get("items", [])
            has_points = any(it.get("points") for it in items)
            if first or tone == "white" or has_points:
                if len(items) <= 2 and not has_points:
                    out.append(sec_grid(c, sec, first))
                elif page.get("kicker") == "Insights":
                    out.append(sec_grid(c, sec, first))
                else:
                    out.append(sec_rows(c, sec, label, first))
                tone = "dark"
            else:
                out.append(sec_rail(c, sec)); tone = "white"
    return "".join(out)


# ---------------------------------------------------------------- pages
def crumbs_for(page):
    slug = page["slug"]
    top = slug.split("/")[0]
    parent = {"our-services": ("Services", "our-services"), "industries": ("Industries", "our-services#industries"),
              "service-model": ("Service Models", "service-model/delivery-model"), "our-company": ("Who We Are", "our-company/about-us")}.get(top)
    trail = [("Home", "/")]
    if parent and parent[1] != slug:
        trail.append(parent)
    trail.append((page["title"], ""))
    return trail


def current_for(slug):
    if slug.startswith(("our-services", "industries", "service-model")):
        return "services"
    if slug.startswith("our-company"):
        return "company"
    if slug.startswith("our-work"):
        return "work"
    if slug.startswith("our-solutions"):
        return "solutions"
    return ""


def build_content_page(page):
    c = Ctx(page["slug"])
    body = hero(c, page["word"], page["title"], page["body"], page.get("cta"), page.get("kicker", ""), crumbs_for(page))
    body += render_sections(c, page)
    return document(c, page["title"], page["body"], body, current_for(page["slug"]))


def industry_rows(c):
    rows = []
    for i, ind in enumerate(SITE["industries"]):
        p = PAGES.get(ind["slug"], {})
        stats = next((s["items"] for s in p.get("sections", []) if s["type"] == "stats"), [])
        item = {"title": p.get("title", ind["name"]), "body": p.get("body", "")}
        if stats:
            item["stat"] = stats[0]
            if len(stats) > 1:
                item["stat2"] = stats[1]
        rows.append(row_item(c, i + 1, item, f'Industry · {ind["name"]}', open_=(i == 2), cta={"label": "Learn more", "href": ind["slug"]}))
    for j, name in enumerate(SITE["more_industries"]):
        rows.append(row_item(c, len(rows) + 1, {"title": name, "body": "Talk to our specialists about custom software solutions for this industry."},
                             "Industry", cta={"label": "Talk to us", "href": CONTACT_HREF}))
    return "".join(rows)


def build_home():
    c = Ctx("")
    h = SITE["home"]
    badges = "".join(f'<a href="{e(a["href"])}" target="_blank" rel="noopener" title="{e(a["name"])}"><img src="{c.asset("img/" + a["img"])}" alt="{e(a["name"])}" width="54" height="54"></a>' for a in SITE["awards"])
    body = hero(c, "Recon", f'{h["eyebrow"]} {h["title"]}', h["body"],
                {"label": "Get in touch", "href": CONTACT_HREF},
                extra=f'<div class="hero-badges">{badges}</div>',
                title_html=f'{e(h["eyebrow"])} <span class="fade">{e(h["title"])}</span>',
                tag=["Smart software systems", "& intelligent solutions", "Abuja · Worldwide"],
                word_html='<p class="wordmark wordmark--full" aria-hidden="true">Reconnaissan<span class="trail">ce</span></p>')

    # 1. Client logos (white panel rising over the hero)
    body += clients_block(c, "Our Clients", "Trusted by Customers Worldwide", quotes_on=False, first=True)

    # 2. About + stats
    about = "".join(f"<p>{e(p)}</p>" for p in h["about_body"])
    body += f'''
<section class="section--tight"><div class="frame"><div class="panel reveal">
  <div class="stats-wrap">
    <div class="stats-top">
      <div style="display:grid;gap:22px;align-content:start"><span class="eyebrow">{e(h["about_eyebrow"])}</span>
        <h2 class="h-xl">An End-to-End <span class="accent">Software Solutions Company</span></h2></div>
      <div class="side" style="justify-items:start;text-align:left"><div class="prose about-copy">{about}</div>
        <a class="link-underline" href="{c.url("our-company/about-us")}" style="color:var(--ink)">Know More {ARROW_R}</a></div>
    </div>
    <div class="stats-foot" style="align-items:end"><span class="micro">Numbers from teams<br>already building with<br>Reconnaissance</span>
      {stats_block(h["stats"])}</div>
  </div>
</div></div></section>'''

    # 2. Services rail (dark)
    services = []
    for s in SITE["services"]:
        p = PAGES.get(s["slug"], {})
        services.append({"title": s["name"], "body": p.get("body", ""), "href": s["slug"]})
    body += sec_rail(c, {"eyebrow": h["services_eyebrow"], "title": h["services_title"], "body": h["services_body"], "items": services})
    body += f'<div class="frame" style="margin-top:-40px;margin-bottom:40px"><a class="link-underline" href="{c.url("our-services")}">View More Services</a></div>'

    # 3. Industries list (white)
    body += sec_rows(c, {"eyebrow": h["industries_eyebrow"], "title": h["industries_title"], "body": h["industries_body"]},
                     "Industry", rows=industry_rows(c)).replace('<div class="panel reveal">', '<div class="panel reveal" id="industries">', 1)

    # 4. Tech stack (dark tabs)
    body += sec_tabs(c, {"eyebrow": h["stack_eyebrow"], "title": h["stack_title"], "body": h["stack_body"]},
                     list(SITE["stack"].items()), dark=True, uid="stack")

    # 5. Insights (white grid)
    insights = "".join(f'''<a class="g-card{' g-card--feature' if i == 0 else ''}" href="{c.url(it["href"])}">
        <span class="num">{i + 1:02d}</span>
        <div style="display:grid;gap:10px">{DOTS}<h3 class="h-s">{e(it["title"])}</h3><p>{e(it["body"])}</p></div>
        <span class="circle-btn">{ARROW_R}</span></a>''' for i, it in enumerate(h["insights"]))
    body += f'''
<section class="section--tight"><div class="frame"><div class="panel reveal">
  {head_block({"eyebrow": h["insights_eyebrow"], "title": h["insights_title"]})}
  <div class="grid-cards">{insights}</div>
</div></div></section>'''

    # 6. Clients & testimonials
    body += clients_block(c, "Testimonials", h["clients_eyebrow"], logos_on=False)

    # 7. CTA + contact
    body += sec_cta(c, {"title": "Ready to start your dream project?", "body": "Experience the power of our Team's prowess and engage in Next-Level Business Success!",
                        "cta": {"label": "Speak with an Expert", "href": CONTACT_HREF}}, "Recon")
    body += sec_contact(c, {"eyebrow": "Enquiry", "title": "Get In Touch With Us"})
    return document(c, f'{SITE["name"]} — {SITE["tagline"]}', h["body"] + ". " + h["about_body"][0], body)


def clients_block(c, eyebrow, title, logos_on=True, quotes_on=True, first=False):
    logos = "".join(
        (f'<a href="{e(cl["href"])}" target="_blank" rel="noopener" title="{e(cl["name"])}">' if cl["href"] else f'<div title="{e(cl["name"])}">')
        + f'<img src="{c.asset("img/" + cl["logo"])}" alt="{e(cl["name"])} logo" loading="lazy">'
        + ("</a>" if cl["href"] else "</div>") for cl in SITE["clients"])
    # second copy for the seamless loop: hidden from assistive tech and the tab order
    logos_dup = logos.replace('<a href', '<a tabindex="-1" href').replace(' logo" loading', '" loading').replace('alt="', 'alt="" data-alt="')
    quotes = "".join(f'''<figure class="quote" style="margin:0">
        <div style="display:grid;gap:12px">{DOTS}<h3>{e(t["title"])}</h3><blockquote>{e(t["quote"])}</blockquote></div>
        <footer><span>{f"<strong>{e(t['name'])}</strong>" if t["name"] else ""}{e(", ".join(x for x in [t["org"], t["place"]] if x))}</span></footer>
      </figure>''' for t in SITE["testimonials"])
    return f'''
<section class="{'rise' if first else 'section--tight'}"><div class="frame"><div class="panel reveal">
  {head_block({"eyebrow": eyebrow, "title": title})}
  {f'<div class="marquee"><div class="marquee-track"><div class="logos logos--row">{logos}</div><div class="logos logos--row" aria-hidden="true">{logos_dup}</div></div></div>' if logos_on else ""}
  {f'<div class="quotes">{quotes}</div>' if quotes_on else ""}
</div></div></section>'''


def build_services_index():
    slug = "our-services"
    c = Ctx(slug)
    page = {"slug": slug, "title": "Our Services", "kicker": "Services"}
    body = hero(c, "Services", "Our Services",
                "Elevate your business with our cutting-edge IT solutions. From software development to cybersecurity, we've got you covered at Reconnaissance Technologies.",
                {"label": "Speak with an Expert", "href": CONTACT_HREF}, "Services", [("Home", "/"), ("Our Services", "")])
    rows = "".join(row_item(c, i + 1, {"title": s["name"], "body": PAGES[s["slug"]]["body"]}, f'{s["group"]} service',
                            open_=(i == 0), cta={"label": "Learn more", "href": s["slug"]}) for i, s in enumerate(SITE["services"]))
    body += sec_rows(c, {"eyebrow": "Our Offerings", "title": "We offer professional IT Services",
                         "body": "Whether it's intricate enterprise software development or seamless software integration, our IT consulting services and software development will elevate your business to the next level of success"},
                     "Service", first=True, rows=rows)
    inds = [{"title": i["name"], "body": PAGES[i["slug"]]["body"], "href": i["slug"]} for i in SITE["industries"]]
    body += sec_rail(c, {"eyebrow": "Industries We Serve", "title": "Specialized software solutions tailored to specific industries",
                         "body": SITE["home"]["industries_body"], "items": inds}).replace('class="section rail-section on-dark"', 'class="section rail-section on-dark" id="industries"', 1)
    models = "".join(row_item(c, i + 1, {"title": m["name"], "body": PAGES[m["slug"]]["body"]}, "Service model",
                              open_=(i == 0), cta={"label": "Learn more", "href": m["slug"]}) for i, m in enumerate(SITE["service_models"]))
    body += sec_rows(c, {"eyebrow": "Service Models", "title": "Delivery and engagement models to meet your business needs"}, "Model", rows=models)
    body += sec_cta(c, {"title": "Transform Your Business", "body": "Experience the power of technology as we leverage on it to build solutions that stands the test of time"}, "Services")
    return slug, document(c, "Our Services", page_hero_body("our-services/software-devlopment"), body, "services")


def build_portfolio():
    slug = "our-work/portfolio"
    c = Ctx(slug)
    h = SITE["home"]
    work = h["insights"][0]
    body = hero(c, "Our Work", "Our Work & Portfolio", work["body"], {"label": "Start your project", "href": CONTACT_HREF},
                "Our Work", [("Home", "/"), ("Our Work", "")])
    body += clients_block(c, h["clients_eyebrow"], h["clients_title"]).replace('section--tight', 'rise', 1)
    products = [{"title": p["name"], "body": "One of Reconnaissance Technologies' own product offerings.", "href": p["href"], "cta": "Visit product"} for p in SITE["products"]]
    body += sec_rail(c, {"eyebrow": "Product Offerings", "title": "Products built in-house by our team", "body": "", "items": products})
    body += sec_cta(c, {"title": "Ready to start your dream project?", "body": "Experience the power of our Team's prowess and engage in Next-Level Business Success!"}, "Work")
    return slug, document(c, "Our Work", work["body"], body, "work")


def build_solutions():
    slug = "our-solutions"
    c = Ctx(slug)
    sol = SITE["home"]["insights"][1]
    body = hero(c, "Solutions", "Products & Solutions Overview", sol["body"], {"label": "Speak with an Expert", "href": CONTACT_HREF},
                "Solutions", [("Home", "/"), ("Solutions", "")])
    rows = "".join(row_item(c, i + 1, {"title": s["name"], "body": PAGES[s["industry"]]["body"]}, "Solution",
                            open_=(i == 0), cta={"label": "Learn more", "href": s["industry"]}) for i, s in enumerate(SITE["solutions"]))
    body += sec_rows(c, {"eyebrow": "Solutions", "title": "Industry-ready solutions that elevate businesses and streamline processes"}, "Solution", first=True, rows=rows)
    products = [{"title": p["name"], "body": ("New — " if p["badge"] else "") + "A Reconnaissance Technologies product offering.", "href": p["href"], "cta": "Visit product"} for p in SITE["products"]]
    body += sec_rail(c, {"eyebrow": "Product Offerings", "title": "Our products", "body": "", "items": products})
    body += sec_cta(c, {"title": "Transform Your Business", "body": "Experience the power of technology as we leverage on it to build solutions that stands the test of time"}, "Solutions")
    return slug, document(c, "Products & Solutions", sol["body"], body, "solutions")


def build_csr():
    slug = "our-company/csr"
    c = Ctx(slug)
    csr = SITE["home"]["insights"][3]
    body = hero(c, "CSR", "Corporate Social Responsibility", csr["body"], {"label": "Partner with us", "href": CONTACT_HREF},
                "Insights", [("Home", "/"), ("Who We Are", "our-company/about-us"), ("CSR", "")])
    body += sec_intro(c, {"eyebrow": "CSR", "title": "Creating lasting change with The Iwoni Foundation", "body": csr["body"],
                          "aside": {"title": "Social Responsibility", "body": "Contribute positively to society by engaging in ethical business practices, promoting environmental sustainability, and actively participating in community initiatives."}},
                      first=True)
    body += sec_cta(c, {"title": "Transform Your Business", "body": "Experience the power of technology as we leverage on it to build solutions that stands the test of time"}, "CSR")
    return slug, document(c, "Corporate Social Responsibility", csr["body"], body, "company")


def build_404():
    c = Ctx("")
    body = hero(c, "404", "This page drifted out of orbit", "The page you are looking for doesn't exist or has moved.",
                {"label": "Back to home", "href": "/"})
    return document(c, "Page not found", "Page not found", body)


# ---------------------------------------------------------------- main
def write(slug, html_text):
    target = DIST / slug / "index.html" if slug else DIST / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html_text, encoding="utf-8")


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT / "assets", DIST / "assets")
    write("", build_home())
    for slug, page in PAGES.items():
        write(slug, build_content_page(page))
    for builder in (build_services_index, build_portfolio, build_solutions, build_csr):
        slug, text = builder()
        write(slug, text)
    (DIST / "404.html").write_text(build_404(), encoding="utf-8")
    urls = [""] + list(PAGES) + ["our-services", "our-work/portfolio", "our-solutions", "our-company/csr"]
    sitemap = "".join(f"<url><loc>{SITE['url']}/{u}</loc></url>" for u in urls)
    (DIST / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sitemap}</urlset>\n', encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE['url']}/sitemap.xml\n", encoding="utf-8")
    print(f"Built {len(urls)} pages into {DIST.relative_to(ROOT)}/")

    if "--serve" in sys.argv:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
        print("Serving on http://localhost:8000")
        http.server.ThreadingHTTPServer(("", 8000), handler).serve_forever()


if __name__ == "__main__":
    main()
