#!/usr/bin/env python3
"""Static checks on a built dist/ folder (no browser needed). Run: python3 tests/check_dist.py dist [--production]
Checks: pages exist, one H1 per page, no heading jumps, JSON-LD parses, no FAQPage, internal links/assets resolve,
titles and descriptions unique, forbidden strings absent, no unresolved template syntax in attributes, every WhatsApp link\nstatic-correct (number + message), every visible email a mailto link, composer wording and no-JS fallback, privacy-policy\nrequired wording, no backend artefacts, guide hero mapping, sitemap coverage, robots/noindex mode, dist hygiene."""
import sys, os, re, json, html, datetime, urllib.parse

dist = sys.argv[1] if len(sys.argv) > 1 else "dist"
production = "--production" in sys.argv
problems = []
pages = []
for root, _, files in os.walk(dist):
    for f in files:
        if f.endswith(".html"): pages.append(os.path.join(root, f))
WA_NUMBER = "8619042799025"
DEFAULT_WA = "Hi, I'm interested in sourcing a product from China and would like some help."
wa_links = 0
EXPECTED_HEROES = {
    "how-to-find-reliable-chinese-factories": "factory-floor-visit",
    "supplier-verification-checklist": "supplier-showroom-meeting",
    "quality-inspection-guide": "product-sample-review",
    "china-sourcing-costs": "buyer-briefing-guangzhou",
    "importing-from-china-to-the-uk": "branded-importing-uk",      # no genuine logistics photograph supplied yet
    "importing-from-china-to-uae-saudi-arabia": "gulf-buyers-trade-exhibition",
    "product-compliance-guide-china-imports": "vehicle-test-chamber-visit",
    "canton-fair-buyers-guide": "guangzhou-skyline-meeting-space",
}
FORBIDDEN = ["offic" + "al@flawlesseffect.com", "Chinese manufacturing", "[CLIENT:", "Needs client confirmation", "FAQPage", "placeholder-note", "iso.org/standard/1141",
             # no server-side enquiry system: none of these may appear in generated pages
             "/api/enquiry", "challenges.cloudflare.com", "cf-turnstile", "Resend", "Send enquiry", "Message sent", "Successfully submitted",
             "has been sent", "Your enquiry has been sent", "Sending your enquiry", 'type="file"', "Pazhou Exhibition Industrial Park"]
EMAIL = "info@flawlesseffect.com"
PRIVACY_REQUIRED = ["does not submit or store the information entered in the WhatsApp enquiry form", "WhatsApp will open with that draft",
                    "The website itself does not send or store the email", "WhatsApp and Meta will process", "Zoho Mail",
                    "flawlesseffect LLC", "Chongqing Fulelisi Cross-Border E-Commerce Center (Individual Proprietorship)", "92500103MAK2D0DN7B",
                    "operational team in China", "24 months from receipt", "Information Commissioner", "supervisory authority in their member state",
                    "local data-protection authority", "Effective date: 12 September 2026", "www.whatsapp.com/legal/privacy-policy"]
titles, descs = {}, {}
all_targets = set()
for p in sorted(pages):
    s = open(p, encoding="utf-8").read()
    rel = "/" + os.path.relpath(p, dist).replace(os.sep, "/").replace("index.html", "")
    for bad in FORBIDDEN:
        if bad in s: problems.append(f"{rel}: contains forbidden text {bad!r}")
    h = [int(m) for m in re.findall(r"<h([1-6])\b", s)]
    if h.count(1) != 1: problems.append(f"{rel}: {h.count(1)} H1")
    prev = 0
    for i, l in enumerate(h):
        if prev and l > prev + 1: problems.append(f"{rel}: heading jump h{prev}->h{l} at #{i}")
        prev = l
    today = datetime.date.today().isoformat()
    for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try: obj = json.loads(blk)
        except Exception as e: problems.append(f"{rel}: invalid JSON-LD ({e})"); continue
        nodes = obj.get("@graph", [obj]) if isinstance(obj, dict) else obj
        for n in nodes:
            if isinstance(n, dict) and n.get("@type") == "Article":
                pub, mod = n.get("datePublished", ""), n.get("dateModified", "")
                if mod < pub: problems.append(f"{rel}: dateModified {mod} before datePublished {pub}")
                if pub > today or mod > today: problems.append(f"{rel}: future date in Article schema ({pub}, {mod})")
                vis = re.findall(r'<time datetime="(\d{4}-\d{2}-\d{2})"', s)
                if vis and (vis[0] != pub or vis[-1] != mod): problems.append(f"{rel}: visible dates {vis} disagree with schema ({pub}, {mod})")
    # TOC labels must not start with a number (the <ol> numbers them)
    for lbl in re.findall(r'<nav class="guide-toc".*?</nav>', s, re.S):
        for txt in re.findall(r'<a href="#[^"]+">([^<]+)</a>', lbl):
            if re.match(r"^\s*\d+[.)]", txt): problems.append(f"{rel}: TOC label starts with a number: {txt!r}")
    # guide heroes: approved photographs mapped to their intended guides; the UK guide keeps its branded image
    for slug, expect in EXPECTED_HEROES.items():
        if rel == f"/guides/{slug}/":
            hero = re.search(r'<figure class="guide-hero">.*?<img [^>]*src="([^"]+)"', s, re.S)
            og = re.search(r'<meta property="og:image" content="([^"]+)"', s)
            if not hero or f"/assets/img/guides/{expect}-" not in hero.group(1): problems.append(f"{rel}: hero is not {expect}")
            if not og or f"/assets/img/guides/og/{slug}." not in og.group(1): problems.append(f"{rel}: og:image is not the guide's own card")
            for m in re.finditer(r'<img [^>]*class="focal-(\d+)"', s):
                if int(m.group(1)) not in (20, 30, 35, 40, 50, 55, 60): problems.append(f"{rel}: unknown focal class {m.group(0)}")
    # every visible occurrence of the public email address must be a mailto link
    text = re.sub(r"<script.*?</script>", "", s, flags=re.S)
    visible = len(re.findall(re.escape(EMAIL), re.sub(r"<[^>]+>", " ", text)))
    linked = len(re.findall(r'<a [^>]*href="mailto:' + re.escape(EMAIL) + r'"[^>]*>(?:(?!</a>).)*?' + re.escape(EMAIL), text, re.S))
    if visible != linked: problems.append(f"{rel}: {visible} visible email occurrences but {linked} mailto-linked")
    if re.search(r"mailto:(?!" + re.escape(EMAIL) + r")", s): problems.append(f"{rel}: mailto link to a different address")
    # forms never post anywhere: no action/method, and no server-only controls
    for ftag in re.findall(r"<form [^>]*>", s):
        if re.search(r'\b(action|method|enctype)=', ftag): problems.append(f"{rel}: form has a submission target: {ftag[:80]}")
        if "data-inquiry" not in ftag: problems.append(f"{rel}: unexpected form {ftag[:80]}")
    for ftag in re.findall(r'<form [^>]*data-inquiry[^>]*>.*?</form>', s, re.S):
        if re.search(r'name="(email|phone|attachments|website|t0|page)"', ftag): problems.append(f"{rel}: composer contains a removed field")
        if "Continue on WhatsApp" not in ftag: problems.append(f"{rel}: composer submit button copy wrong")
        if "Your message is not sent to Flawless Effect until you press Send in WhatsApp" not in ftag: problems.append(f"{rel}: composer draft note missing")
        if "where WhatsApp/Meta will process the information entered" not in ftag: problems.append(f"{rel}: composer consent wording missing")
        if 'href="/privacy-policy/"' not in ftag: problems.append(f"{rel}: composer consent lacks the Privacy Policy link")
        if not re.search(r'<div class="form-nojs">.*?href="https://wa\.me/.*?href="mailto:' + re.escape(EMAIL), s, re.S): problems.append(f"{rel}: no-JavaScript fallback missing")
    if rel == "/privacy-policy/":
        for phrase in PRIVACY_REQUIRED:
            if phrase not in html.unescape(s): problems.append(f"{rel}: privacy policy lacks {phrase!r}")
        prose = re.search(r'<div class="container prose">.*?</div></section>', s, re.S).group(0)
        for m in re.finditer(r'<a href="https?://[^"]+"[^>]*>', prose):
            if 'target="_blank"' not in m.group(0) or 'rel="noopener noreferrer"' not in m.group(0): problems.append(f"{rel}: external link without target/rel: {m.group(0)[:80]}")
        if "Standard Contractual Clauses" in s or "IDTA" in s or "Data Privacy Framework" in s: problems.append(f"{rel}: claims a specific transfer mechanism")
    # unresolved template syntax must never reach generated attributes (href, src, content, action, data-*)
    for attr, val in re.findall(r'\b(href|src|srcset|imagesrcset|poster|content|action|data-[a-z-]+)="([^"]*)"', s):
        if re.search(r"%7B|%7D|\{|\}|\.lower\(\)|\.upper\(\)|\.title\(\)|\{title|\{t\.", val, re.I):
            problems.append(f"{rel}: unresolved template syntax in {attr}: {val[:80]!r}")
    # every WhatsApp link: correct number, decoded static message equals the data-wa message (or the page-context
    # message for valueless data-wa, exactly what main.js applies), so no-JavaScript and JavaScript agree
    page_ctx = re.search(r'<body[^>]* data-wa-message="([^"]*)"', s)
    page_ctx = html.unescape(page_ctx.group(1)) if page_ctx else DEFAULT_WA
    for tag in re.findall(r'<a [^>]*\bdata-wa(?:="[^"]*")?(?=[\s>])[^>]*>', s):  # data-wa only, not data-wa-ref (rewritten after a submission)
        href = re.search(r'href="([^"]*)"', tag); dw = re.search(r'data-wa="([^"]*)"', tag)
        if not href: problems.append(f"{rel}: data-wa link without href"); continue
        u = urllib.parse.urlparse(html.unescape(href.group(1)))
        text = urllib.parse.parse_qs(u.query).get("text", [""])[0]
        expect = html.unescape(dw.group(1)) if dw and dw.group(1) else page_ctx
        if u.scheme != "https" or u.netloc != "wa.me" or u.path.strip("/") != WA_NUMBER: problems.append(f"{rel}: WhatsApp link has wrong number/host: {href.group(1)[:60]}")
        if text != expect: problems.append(f"{rel}: static WhatsApp message {text[:50]!r} != expected {expect[:50]!r}")
        wa_links += 1
    # exactly one /guides/ link in the global footer
    foot = re.search(r'<footer class="footer">.*?</footer>', s, re.S)
    guides_links = foot.group(0).count('href="/guides/"') if foot else 0
    if foot and guides_links != 1: problems.append(f"{rel}: footer has {guides_links} /guides/ links")
    if foot and re.search(r'href="/guides/[a-z]', foot.group(0)): problems.append(f"{rel}: footer links to an individual guide")
    t = re.search(r"<title>(.*?)</title>", s); d = re.search(r'<meta name="description" content="(.*?)"', s)
    if t: titles.setdefault(html.unescape(t.group(1)), []).append(rel)
    if d: descs.setdefault(html.unescape(d.group(1)), []).append(rel)
    if t and len(html.unescape(t.group(1))) > 65: problems.append(f"{rel}: title too long ({len(html.unescape(t.group(1)))})")
    if d and len(html.unescape(d.group(1))) > 160: problems.append(f"{rel}: description too long ({len(html.unescape(d.group(1)))})")
    noindex = 'name="robots" content="noindex' in s
    if rel == "/404.html":
        if not noindex: problems.append("404 page must be noindex")
    elif production and noindex: problems.append(f"{rel}: noindex present in production build")
    elif not production and not noindex: problems.append(f"{rel}: preview build must be noindex")
    # internal targets
    for u in re.findall(r'(?:href|src|poster|data-webm|data-mp4|content|imagesrcset)="([^"]+)"', s):
        for cand in (u.split(",") if "imagesrcset" in u or " " in u and "w" in u else [u]):
            cand = cand.strip().split(" ")[0]
            if cand.startswith("/") and not cand.startswith("//"): all_targets.add(cand.split("#")[0].split("?")[0])
for k, v in titles.items():
    if len(v) > 1: problems.append(f"duplicate title {k!r}: {v}")
for k, v in descs.items():
    if len(v) > 1: problems.append(f"duplicate description {k!r}: {v}")
for tgt in sorted(all_targets):
    if tgt in ("/", "") : continue
    path = os.path.join(dist, tgt.lstrip("/"))
    if tgt.endswith("/"): path = os.path.join(path, "index.html")
    if not os.path.exists(path): problems.append(f"missing target {tgt}")
# sitemap
sm = open(os.path.join(dist, "sitemap.xml"), encoding="utf-8").read()
locs = re.findall(r"<loc>https://flawlesseffect.com(.*?)</loc>", sm)
if "/404.html" in locs: problems.append("sitemap contains 404")
content_pages = [("/" + os.path.relpath(p, dist).replace(os.sep, "/").replace("index.html", "")) for p in pages if not p.endswith("404.html")]
for cp in content_pages:
    if cp not in locs: problems.append(f"sitemap missing {cp}")
robots = open(os.path.join(dist, "robots.txt"), encoding="utf-8").read()
if production and "Disallow: /\n" in robots: problems.append("production robots.txt disallows everything")
if not production and "Disallow: /\n" not in robots: problems.append("preview robots.txt must disallow")
# no backend artefacts in the output, no /api rules or robots entries
if os.path.isdir(os.path.join(dist, "functions")) or os.path.isdir(os.path.join(dist, "api")): problems.append("dist contains backend directories")
hdrs = open(os.path.join(dist, "_headers"), encoding="utf-8").read()
if "/api/" in hdrs or "challenges.cloudflare.com" in hdrs: problems.append("_headers still references the removed backend")
if "/api/" in robots: problems.append("robots.txt still references /api/")
# hygiene
for root, _, files in os.walk(dist):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), dist)
        if re.search(r"(^|/)(_build|functions|tests|node_modules|\.github)/|\.py$|\.md$|\.mjs$|\.DS_Store| 2\.webp$|\.pyc$|\.env|\.pem$", rel): problems.append(f"dist contains non-deployment file {rel}")
print(f"checked {len(pages)} pages, {len(all_targets)} internal targets, {len(locs)} sitemap URLs, {wa_links} WhatsApp links ({'production' if production else 'preview'} mode)")
if problems:
    print("\n".join("- " + x for x in problems)); sys.exit(1)
print("all checks passed")
