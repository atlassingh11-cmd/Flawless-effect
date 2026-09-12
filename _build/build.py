#!/usr/bin/env python3
"""
Static site builder for flawlesseffect.com
Run:  python3 _build/build.py                      -> dist/ (preview, noindex)
      SITE_MODE=production python3 _build/build.py -> dist/ (indexable; refuses to run if a LAUNCH_REQUIRED value is empty)
      SITE_MODE=production AUDIT_ONLY=1 ...        -> dist-audit/ (indexable copy for local Lighthouse only)
Everything under dist/ is generated; edit this file, _build/guides.py, assets/ and rebuild.
"""
import os, re, datetime, hashlib, json, html, sys, shutil, struct, base64
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")

# ============================================================================
# CONFIGURATION — the only block you should need to edit.
# Every value is HTML-escaped where it is inserted; write plain text here.
# ============================================================================
SITE_URL = "https://flawlesseffect.com"
BRAND = "Flawless Effect"
PHONE_DISPLAY = "+86 190 4279 9025"
PHONE_TEL = "+8619042799025"
EMAIL = "info@flawlesseffect.com"      # CONFIRMED public address (client, 11 Sep 2026)
WECHAT_ID = "flawlesseffect"            # CONFIRMED by client 11 Sep 2026
WECHAT_QR = ""                          # e.g. "/assets/img/wechat-qr.png" — genuine QR image only; leave empty until supplied
WECHAT_NAME = "FLAWLESSeffect ®"        # display name on the WeChat profile (confirmed)
WECHAT_CHANNEL = "FLAWLESSeffect"       # WeChat Channels account (confirmed)
INSTAGRAM = "https://instagram.com/flawlesseffect.sourcingagent"
LINKEDIN_URL = ""                       # footer link renders only when set
ADDRESS = "Pazhou Digital Science and Technology Industrial Park, Guangzhou, China"   # public operational office (confirmed by the owner, 12 Sep 2026); not the registered address
MAPS_URL = "https://www.google.com/maps/search/?api=1&query=Pazhou+Digital+Science+and+Technology+Industrial+Park+Guangzhou"
HOURS = "9:00 – 18:00 (China Standard Time)"
HOURS_LONG = "9:00 to 18:00 China time. That is 02:00–11:00 UK summer time or 01:00–10:00 UK winter time; 05:00–14:00 in the UAE and Oman; 04:00–13:00 in Saudi Arabia, Qatar, Kuwait and Bahrain."
FEE_MODEL = ""                          # plain-text description of how fees work — the “How we charge” module is hidden until set
# Contact model: no server-side enquiry system. The form composes a WhatsApp draft in the browser; the email address is a mailto link.
# Legal / privacy facts — confirmed by the owner on 12 September 2026. Production builds refuse to run while any LAUNCH_REQUIRED value is empty.
LEGAL_ENTITY_US = "flawlesseffect LLC"                                                        # US registration number and address are deliberately not published
LEGAL_ENTITY_CN = "Chongqing Fulelisi Cross-Border E-Commerce Center (Individual Proprietorship)"
REGISTRATION_NO_CN = "92500103MAK2D0DN7B"                                                   # Unified Social Credit Code
REGISTERED_ADDRESS_CN = "No. 229, 2-2#, Changjiang Binjiang Road, Nanjimen Subdistrict, Yuzhong District, Chongqing, 400010, China"
EMAIL_PROVIDER = "Zoho Mail"
WHATSAPP_PRIVACY_URL = "https://www.whatsapp.com/legal/privacy-policy"
RETENTION_PERIOD = "24 months from receipt"
PRIVACY_EFFECTIVE_DATE = "12 September 2026"
LAUNCH_REQUIRED = {"LEGAL_ENTITY_US": LEGAL_ENTITY_US, "LEGAL_ENTITY_CN": LEGAL_ENTITY_CN, "REGISTRATION_NO_CN": REGISTRATION_NO_CN, "REGISTERED_ADDRESS_CN": REGISTERED_ADDRESS_CN, "RETENTION_PERIOD": RETENTION_PERIOD, "PRIVACY_EFFECTIVE_DATE": PRIVACY_EFFECTIVE_DATE}

# Build mode. Preview (default) = noindex + robots disallow. Production = indexable, only when every LAUNCH_REQUIRED value is set.
#   python3 _build/build.py                 -> preview
#   SITE_MODE=production python3 _build/build.py  (or --production)
SITE_MODE = "production" if ("--production" in sys.argv or os.environ.get("SITE_MODE") == "production") else "preview"
PREVIEW = SITE_MODE != "production"
AUDIT_ONLY = os.environ.get("AUDIT_ONLY") == "1"   # local Lighthouse/SEO measurement of an indexable build; output goes to dist-audit/, which Cloudflare never publishes
if AUDIT_ONLY: DIST = os.path.join(ROOT, "dist-audit")

# Optional genuine authorship for the guides. Renders only when populated; otherwise the organisation byline is used.
AUTHOR = {"name": "", "role": "", "experience": "", "bio": "", "url": ""}
REVIEWER = {"name": "", "role": "", "url": ""}
# Photographs containing identifiable third parties. The client confirmed publication permission for every placement
# on 11 September 2026 (see IMAGE_USAGE.md). Keep False. Setting True swaps them for non-identifying images site-wide
# if permission is ever withdrawn; guide heroes are configured separately in _build/guides.py.
USE_SAFE_IMAGE_FALLBACKS = False
IMG_FALLBACKS = {
    "factory-tour": ("meeting-skyline", "The Guangzhou skyline seen from Flawless Effect’s meeting space"),
    "showroom-meeting": ("lobby-wood", "Sunlit lobby of Flawless Effect’s Guangzhou meeting space"),
    "sample-review": ("lounge-a", "Lounge area at Flawless Effect’s meeting space in Guangzhou"),
    "client-dinner": ("dining-table", "Round dining table at the Guangzhou meeting space"),
    "exhibition-middle-east": ("leap-east-hk", "Flawless Effect at LEAP East, Hong Kong Convention and Exhibition Centre, July 2026"),
    "exhibition-meeting": ("leap-conference", "Flawless Effect at the LEAP conference main stage"),
    "buyer-briefing": ("lobby-overhead", "Overhead view of the lobby at the Guangzhou meeting space"),
}

# Genuine trust evidence — each module renders only when populated. Never invent entries.
EVIDENCE = {
    "team": [],            # {"name": "…", "role": "…", "languages": "…", "photo": "asset-name"}
    "registration": "",
    "case_studies": [],    # {"title": "…", "summary": "…", "facts": ["…"]}
    "reviews": [],         # {"quote": "…", "name": "…", "company": "…", "country": "…"}
    "reports": [],         # {"title": "…", "file": "/assets/docs/…pdf", "note": "…"}
}

E = html.escape                         # escape any configurable value inserted into HTML/attributes
def _ver(rel):
    try: return hashlib.md5(open(os.path.join(ROOT, rel), "rb").read()).hexdigest()[:8]
    except Exception: return "1"
CSS_VER = _ver("assets/css/style.css"); JS_VER = _ver("assets/js/main.js")
YEAR = datetime.date.today().year
BUILD_DATE = datetime.date.today().strftime("%-d %B %Y") if os.name != "nt" else datetime.date.today().strftime("%d %B %Y")

def wa_link(message=None):
    """Static WhatsApp URL (works without JavaScript). Never put personal data here."""
    msg = message or "Hi, I'm interested in sourcing a product from China and would like some help."
    return f"https://wa.me/{PHONE_TEL.lstrip('+')}?text={quote(msg, safe='')}"

SERVICE_OPTIONS = ["Product sourcing", "Factory verification", "Price negotiation", "Samples & product development", "Quality inspection", "Compliance & certification support", "Packaging & private label", "Logistics & delivery", "On-site support (visiting China)", "Virtual sourcing (remote)", "Not sure yet"]
CATEGORY_OPTIONS = ["Automotive & Auto Parts", "Home Furniture & Building Materials", "Apparel, Jewelry & Fashion Accessories", "Electronics", "Beauty & Health Care", "Other / Not sure yet"]
CAT_ALTS = {"automotive": "Flawless Effect in a vehicle test chamber during an automotive factory inspection", "furniture": "Furniture and building-materials showroom with sofas, dining set and tile samples", "apparel": "Fashion showroom with apparel, jewelry and accessories on display", "electronics": "Consumer electronics including laptop, phones and accessories laid out on a table", "beauty": "Skincare and cosmetics products arranged on a marble surface", "other": "Retail store shelving with a wide range of household goods"}
CATEGORY_FORM_NAMES = {"automotive": "Automotive & Auto Parts", "furniture": "Home Furniture & Building Materials", "apparel": "Apparel, Jewelry & Fashion Accessories", "electronics": "Electronics", "beauty": "Beauty & Health Care", "other": "Other / Not sure yet"}

# ----------------------------------------------------------------------------
# Icons (inline SVG, 24px grid, stroke)
# ----------------------------------------------------------------------------
def ic(name, cls=""):
    paths = {
        "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
        "factory": '<path d="M3 21V9l6 4V9l6 4V9l6 4v8H3z"/><path d="M8 21v-4h3v4M14 21v-4h3v4"/>',
        "badge-check": '<path d="M12 2.5 14.6 4.4 17.8 4.1 18.9 7.1 21.5 9 20.4 12 21.5 15 18.9 16.9 17.8 19.9 14.6 19.6 12 21.5 9.4 19.6 6.2 19.9 5.1 16.9 2.5 15 3.6 12 2.5 9 5.1 7.1 6.2 4.1 9.4 4.4z"/><path d="m9 12 2 2 4-4"/>',
        "tag": '<path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
        "flask": '<path d="M9 3h6M10 3v6L4.5 19a1.5 1.5 0 0 0 1.3 2.3h12.4a1.5 1.5 0 0 0 1.3-2.3L14 9V3"/><path d="M7.5 15h9"/>',
        "shield": '<path d="M12 2.5 4 5.5v6c0 5 3.4 8.4 8 10 4.6-1.6 8-5 8-10v-6z"/><path d="m9 12 2 2 4-4"/>',
        "file-check": '<path d="M14 2.5H6a2 2 0 0 0-2 2v15a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8.5z"/><path d="M14 2.5v6h6"/><path d="m9 15 2 2 4-4"/>',
        "package": '<path d="M12 2.5 3.5 7v10L12 21.5 20.5 17V7z"/><path d="M3.5 7 12 11.5 20.5 7M12 11.5v10"/><path d="m7.5 4.8 8.5 4.6"/>',
        "ship": '<path d="M3 17c1.5 1.2 3 1.2 4.5 0 1.5 1.2 3 1.2 4.5 0 1.5 1.2 3 1.2 4.5 0 1.5 1.2 3 1.2 4.5 0"/><path d="M4 14V9h16v5M8 9V5h8v4M12 5V3"/><path d="M4 21c1.5 1.2 3 1.2 4.5 0 1.5 1.2 3 1.2 4.5 0 1.5 1.2 3 1.2 4.5 0"/>',
        "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.8 3 2.8 15 0 18M12 3c-2.8 3-2.8 15 0 18"/>',
        "message": '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 21l1.9-5.4A8 8 0 1 1 21 12z"/>',
        "phone": '<path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A17 17 0 0 1 3 5a2 2 0 0 1 2-2z"/>',
        "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
        "pin": '<path d="M12 21s7-6.2 7-11.5A7 7 0 0 0 5 9.5C5 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
        "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
        "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
        "check": '<path d="m5 12 5 5L20 7"/>',
        "chevron": '<path d="m6 9 6 6 6-6"/>',
        "chevron-r": '<path d="m9 6 6 6-6 6"/>',
        "x": '<path d="M18 6 6 18M6 6l12 12"/>',
        "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
        "plus": '<path d="M12 5v14M5 12h14"/>',
        "upload": '<path d="M12 16V4M6 10l6-6 6 6"/><path d="M4 20h16"/>',
        "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M21.5 20a6.5 6.5 0 0 0-4.5-6.2"/>',
        "eye": '<path d="M2 12s3.5-6.5 10-6.5S22 12 22 12s-3.5 6.5-10 6.5S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
        "video": '<rect x="3" y="6" width="13" height="12" rx="2"/><path d="m16 10 5-3v10l-5-3z"/>',
        "handshake": '<path d="m11 17 2 2a1.5 1.5 0 0 0 2-2l-2-2"/><path d="m14 14 1.5 1.5a1.5 1.5 0 0 0 2-2L15 11"/><path d="M2 8.5 7 6l5 2.5 2-1 4.5 2.5 3.5-2"/><path d="M12 8.5 8.5 12a1.5 1.5 0 0 0 2 2L13 11.5"/><path d="M2 8.5v7l3 2M22 8v7l-3 2"/>',
        "clipboard": '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2.5h6V4"/><path d="m9 13 2 2 4-4"/>',
        "layers": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5M3 17.5l9 5 9-5"/>',
        "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
        "sparkle": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6.3 6.3l2.8 2.8M14.9 14.9l2.8 2.8M6.3 17.7l2.8-2.8M14.9 9.1l2.8-2.8"/>',
        "trending": '<path d="m3 17 6-6 4 4 8-8"/><path d="M14 7h7v7"/>',
        "chat-dots": '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 21l1.9-5.4A8 8 0 1 1 21 12z"/><path d="M8.5 12h.01M12 12h.01M15.5 12h.01"/>',
    }
    return f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths[name]}</svg>'

WA_SVG = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5.1-1.3A10 10 0 1 0 12 2zm0 1.8a8.2 8.2 0 1 1-4.2 15.3l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 0 1 12 3.8zm-3.1 4.3c-.2 0-.5 0-.8.4-.3.3-1 1-1 2.4s1 2.8 1.2 3c.1.2 2 3.2 5 4.3 2.5 1 3 .8 3.5.7.5 0 1.7-.7 2-1.4.2-.7.2-1.3.2-1.4-.1-.1-.3-.2-.6-.3l-2-1c-.3-.1-.5-.1-.7.1l-.9 1.1c-.2.2-.3.2-.6.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.2-.4.7-1.4.1-.2 0-.4 0-.5l-.9-2.2c-.2-.6-.5-.5-.7-.5h-.6z"/></svg>'
WC_SVG = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M9.3 3.5C5.3 3.5 2 6.3 2 9.7c0 1.9 1 3.6 2.6 4.7l-.6 2 2.3-1.2c.9.3 1.9.4 2.9.4h.3a5.5 5.5 0 0 1-.2-1.5c0-3.3 3.1-6 7-6h.3c-.7-2.7-3.7-4.6-7.3-4.6zM6.8 7.3a.9.9 0 1 1 0 1.8.9.9 0 0 1 0-1.8zm5 0a.9.9 0 1 1 0 1.8.9.9 0 0 1 0-1.8zM16.2 9.5c-3.2 0-5.8 2.2-5.8 4.9s2.6 4.9 5.8 4.9c.7 0 1.4-.1 2.1-.3l1.9 1-.5-1.6c1.4-.9 2.3-2.3 2.3-4 0-2.7-2.6-4.9-5.8-4.9zm-2 2.9a.8.8 0 1 1 0 1.6.8.8 0 0 1 0-1.6zm4 0a.8.8 0 1 1 0 1.6.8.8 0 0 1 0-1.6z"/></svg>'
IG_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>'

# ----------------------------------------------------------------------------
# Image helper — responsive WebP
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# Assets: cross-platform image dimensions (no external tools) + content-hashed URLs
# ----------------------------------------------------------------------------
ASSET_MAP = {}   # source path relative to ROOT -> published path (with content hash)

def image_size(path):
    """Return (width, height) for WebP, PNG, JPEG or SVG using only the standard library."""
    with open(path, "rb") as f: head = f.read(64 * 1024)
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        chunk = head[12:16]
        if chunk == b"VP8X":
            w = int.from_bytes(head[24:27], "little") + 1; h = int.from_bytes(head[27:30], "little") + 1; return w, h
        if chunk == b"VP8L":
            b = head[21:25]; bits = int.from_bytes(b, "little"); return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if chunk == b"VP8 ":
            w, h = struct.unpack("<HH", head[26:30]); return w & 0x3FFF, h & 0x3FFF
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", head[16:24])
    if head[:2] == b"\xff\xd8":
        data = open(path, "rb").read(); i = 2
        while i < len(data):
            if data[i] != 0xFF: i += 1; continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2): h, w = struct.unpack(">HH", data[i + 5:i + 9]); return w, h
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    if b"<svg" in head[:2048]:
        txt = head.decode("utf-8", "ignore")
        m = re.search(r'viewBox="[\d.\-]+\s+[\d.\-]+\s+([\d.]+)\s+([\d.]+)"', txt)
        if m: return int(float(m.group(1))), int(float(m.group(2)))
        mw, mh = re.search(r'\swidth="([\d.]+)', txt), re.search(r'\sheight="([\d.]+)', txt)
        if mw and mh: return int(float(mw.group(1))), int(float(mh.group(1)))
    raise SystemExit(f"build error: cannot read image dimensions of {path}")

def asset(rel):
    """Register a file under assets/ for publishing with a content hash in its name; return the public URL."""
    rel = rel.lstrip("/")
    if rel in ASSET_MAP: return ASSET_MAP[rel]
    src = os.path.join(ROOT, rel)
    if not os.path.isfile(src): raise SystemExit(f"build error: missing asset {rel}")
    h = hashlib.sha256(open(src, "rb").read()).hexdigest()[:10]
    base, ext = os.path.splitext(rel)
    ASSET_MAP[rel] = f"/{base}.{h}{ext}"
    return ASSET_MAP[rel]

IMG_WIDTHS = {}
def _widths(name):
    if name not in IMG_WIDTHS:
        ws = []
        for f in os.listdir(os.path.join(ROOT, "assets/img")):
            m = re.match(re.escape(name) + r"-(\d+)\.webp$", f)
            if m: ws.append(int(m.group(1)))
        IMG_WIDTHS[name] = sorted(ws)
    return IMG_WIDTHS[name]

DIMS = {}
def _dims(name, w_):
    key = f"{name}-{w_}"
    if key not in DIMS: DIMS[key] = image_size(os.path.join(ROOT, f"assets/img/{key}.webp"))
    return DIMS[key]

def img(name, alt, sizes="(min-width: 960px) 50vw, 100vw", lazy=True, cls="", w=None, h=None, fetchpriority=None):
    if USE_SAFE_IMAGE_FALLBACKS and name in IMG_FALLBACKS: name, alt = IMG_FALLBACKS[name]
    ws = _widths(name)
    if not ws: raise SystemExit(f"missing image: {name}")
    if not (w and h): w, h = _dims(name, ws[-1])
    srcset = ", ".join(f"{asset(f'assets/img/{name}-{w_}.webp')} {w_}w" for w_ in ws)
    attrs = [f'src="{asset(f"assets/img/{name}-{ws[-1]}.webp")}"', f'srcset="{srcset}"', f'sizes="{sizes}"', f'alt="{E(alt)}"']
    if cls: attrs.append(f'class="{cls}"')
    if w and h: attrs += [f'width="{w}"', f'height="{h}"']
    attrs.append('loading="lazy" decoding="async"' if lazy else 'decoding="async"')
    if fetchpriority: attrs.append(f'fetchpriority="{fetchpriority}"')
    return "<img " + " ".join(attrs) + ">"

def brand_img(file, alt, height, cls=""):
    """Approved logo SVG with accurate intrinsic dimensions, scaled by CSS height."""
    w, h = image_size(os.path.join(ROOT, "assets/img/brand", file))
    return f'<img src="{asset(f"assets/img/brand/{file}")}" alt="{E(alt)}" width="{w}" height="{h}" class="{cls}" style="" decoding="async">'.replace(' style=""', '')

def frame(name, alt, ratio="4x3", caption=None, sizes="(min-width: 960px) 50vw, 100vw", lazy=True, cls=""):
    if USE_SAFE_IMAGE_FALLBACKS and name in IMG_FALLBACKS: caption = None
    cap = f'<span class="img-caption">{caption}</span>' if caption else ""
    has = " has-caption" if caption else ""
    return f'<div class="img-frame img-frame--{ratio}{has} {cls}">{img(name, alt, sizes, lazy)}{cap}</div>'

# ----------------------------------------------------------------------------
# Navigation & layout
# ----------------------------------------------------------------------------
NAV = [
    ("Home", "/"),
    ("About", "/about-us/"),
    ("Services", "/sourcing-services/"),
    ("Product Categories", "/product-categories/"),
    ("How It Works", "/#how-it-works"),
    ("Regional Support", "/regional-support/"),
    ("Certifications", "/certifications/"),
    ("Guides", "/guides/"),
    ("Contact", "/contact-us/"),
]

def nav_links(current, drawer=False):
    out = []
    for label, href in NAV:
        cur = ' aria-current="page"' if href == current else ""
        if drawer:
            out.append(f'<li><a class="drawer__link" href="{href}"{cur}>{label}{ic("chevron-r")}</a></li>')
        else:
            out.append(f'<li><a class="nav__link" href="{href}"{cur}>{label}</a></li>')
    return "\n".join(out)

def header(current):
    return f'''
<a class="skip-link" href="#main">Skip to content</a>
<header class="header">
  <div class="container header__inner">
    <a class="brand" href="/" aria-label="{BRAND} — home">{brand_img("fe-logo.svg", BRAND, 36)}</a>
    <nav class="nav" aria-label="Primary"><ul class="nav__list">{nav_links(current)}</ul></nav>
    <div class="header__actions">
      <a class="icon-btn icon-btn--wa header__wa" data-wa href="{wa_link()}" aria-label="Chat on WhatsApp">{WA_SVG}</a>
      <a class="btn btn--primary btn--sm header__cta" href="/contact-us/">Get a quote</a>
      <button class="icon-btn nav-toggle" id="nav-open" aria-label="Open menu" aria-expanded="false" aria-controls="drawer">{ic("menu")}</button>
    </div>
  </div>
</header>
<div class="drawer" id="drawer" aria-hidden="true" role="dialog" aria-modal="true" aria-label="Menu">
  <div class="drawer__backdrop"></div>
  <div class="drawer__panel">
    <div class="drawer__head">{brand_img("fe-logo.svg", BRAND, 30)}<button class="icon-btn" id="nav-close" aria-label="Close menu">{ic("x")}</button></div>
    <ul class="drawer__list">{nav_links(current, drawer=True)}</ul>
    <div class="drawer__foot">
      <a class="btn btn--primary" href="/contact-us/">Get a quote</a>
      <a class="btn btn--wa" data-wa href="{wa_link()}">{WA_SVG} WhatsApp us</a>
      <button class="btn btn--outline" data-wechat type="button">{WC_SVG} WeChat</button>
      <div class="drawer__contact"><span>Email <a href="mailto:{E(EMAIL)}">{E(EMAIL)}</a></span><span>Call <a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a></span><span>WeChat ID <strong>{E(WECHAT_ID)}</strong></span></div>
    </div>
  </div>
</div>'''

def legal_line():
    """Footer legal row: the two operating entities and the Chinese registration. The US registration number is not published."""
    return f"{E(LEGAL_ENTITY_US)} · {E(LEGAL_ENTITY_CN)} · Unified Social Credit Code {E(REGISTRATION_NO_CN)}"
def linkedin_li():
    return f'<li><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9h4v12H3zM9 9h3.8v1.7h.1c.5-1 1.8-2 3.7-2 4 0 4.7 2.6 4.7 6V21h-4v-5.5c0-1.3 0-3-1.8-3s-2.1 1.4-2.1 2.9V21H9z"/></svg><a href="{E(LINKEDIN_URL)}" target="_blank" rel="noopener">LinkedIn</a></li>' if LINKEDIN_URL else ""

def footer():
    services = [("Product Sourcing", "/sourcing-services/#product-sourcing"), ("Factory Verification", "/sourcing-services/#factory-verification"), ("Samples & Development", "/sourcing-services/#samples"), ("Quality Inspection", "/sourcing-services/#quality-inspection"), ("Compliance Support", "/certifications/"), ("Logistics & Delivery", "/sourcing-services/#logistics")]
    cats = [("Automotive & Auto Parts", "/product-categories/#automotive"), ("Furniture & Building Materials", "/product-categories/#furniture"), ("Apparel, Jewelry & Accessories", "/product-categories/#apparel"), ("Electronics", "/product-categories/#electronics"), ("Beauty & Health Care", "/product-categories/#beauty"), ("Other Categories", "/product-categories/#other")]
    li = lambda items: "".join(f'<a href="{h}">{l}</a>' for l, h in items)
    return f'''
<footer class="footer">
  <div class="container">
    <div class="footer__grid">
      <div class="footer__brand">
        {brand_img("fe-logo-white.svg", BRAND, 34)}
        <p>{BRAND} is a China sourcing agent based in Guangzhou. We connect international buyers with dependable Chinese factories: supplier screening, negotiation, samples, quality control, documentation support and delivery coordination, managed on the ground.</p>
        <div class="footer__chat">
          <a class="btn btn--wa" data-wa href="{wa_link()}">{WA_SVG} WhatsApp</a>
          <button class="btn btn--outline" data-wechat type="button">{WC_SVG} WeChat</button>
        </div>
      </div>
      <div><h3>Services</h3><div class="footer__links">{li(services)}</div></div>
      <div><h3>Product Categories</h3><div class="footer__links">{li(cats)}</div></div>
      <div><h3>Explore</h3><div class="footer__links">{li([("About", "/about-us/"), ("Guides", "/guides/"), ("Regional Support", "/regional-support/"), ("Certifications", "/certifications/"), ("Contact", "/contact-us/")])}</div></div>
      <div class="footer__contact-col">
        <h3>Contact</h3>
        <ul class="footer__contact">
          <li>{ic("mail")}<a href="mailto:{E(EMAIL)}">{E(EMAIL)}</a></li>
          <li>{ic("phone")}<a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a></li>
          <li>{WC_SVG}<span>WeChat ID: <strong class="on-ink">{E(WECHAT_ID)}</strong></span></li>
          <li>{ic("pin")}<span>{ADDRESS}</span></li>
          <li>{ic("clock")}<span>{HOURS}</span></li>
          <li>{IG_SVG}<a href="{INSTAGRAM}" target="_blank" rel="noopener">@flawlesseffect.sourcingagent</a></li>{linkedin_li()}
        </ul>
      </div>
    </div>
    <div class="footer__bottom">
      <span>© <span data-year>{YEAR}</span> {BRAND}. All rights reserved. {legal_line()}</span>
      <div class="footer__legal"><a href="/privacy-policy/">Privacy Policy</a></div>
    </div>
  </div>
</footer>
<div class="fab" id="fab" role="region" aria-label="Chat options">
  <div class="fab__menu" id="fab-menu" hidden>
    <a class="fab__item" data-wa href="{wa_link()}"><span class="ico ico--wa">{WA_SVG}</span><span>WhatsApp<small>Fastest reply</small></span></a>
    <button class="fab__item" data-wechat type="button"><span class="ico ico--wc">{WC_SVG}</span><span>WeChat<small>Scan to chat</small></span></button>
  </div>
  <button class="fab__toggle" aria-label="Chat with us" aria-expanded="false" aria-controls="fab-menu">{ic("chat-dots","i-chat")}{ic("x","i-close")}<span class="fab__badge" aria-hidden="true"></span></button>
</div>
<nav class="mobile-bar" aria-label="Contact shortcuts">
  <a class="btn btn--wa btn--wa-solid" data-wa href="{wa_link()}">{WA_SVG} <span class="long">WhatsApp us</span><span class="short">WhatsApp</span></a>
  <a class="btn btn--primary" href="/contact-us/"><span class="long">Get a quote</span><span class="short">Quote</span></a>
</nav>
<div class="modal" id="wechat-modal" aria-hidden="true" role="dialog" aria-modal="true" aria-labelledby="wechat-title">
  <div class="modal__backdrop"></div>
  <div class="modal__panel">
    <button class="icon-btn modal__close" aria-label="Close">{ic("x")}</button>
    <div class="modal__badge">{WC_SVG}</div>
    <p class="modal__title" id="wechat-title">Prefer WeChat?</p>
    <p class="modal__intro"></p>
    <p class="modal__name">Display name: <strong>{E(WECHAT_NAME)}</strong></p>
    <div class="modal__qr" hidden></div>
    <p class="modal__id"></p>
    <div class="modal__copy"><button class="btn btn--outline btn--sm" type="button" data-copy-wechat>Copy WeChat ID</button><span class="modal__copied" role="status" aria-live="polite"></span><input class="modal__id-field" type="text" value="{E(WECHAT_ID)}" readonly aria-label="WeChat ID" hidden></div>
    <p class="modal__help"></p>
    <p class="modal__channels">Watch our factory visits on WeChat Channels: search <strong>{E(WECHAT_CHANNEL)}</strong>.</p>
    <div class="btn-row"><a class="btn btn--wa btn--sm" data-wa href="{wa_link()}">{WA_SVG} WhatsApp us</a></div>
  </div>
</div>
<script src="/assets/js/main.js?v={JS_VER}" defer></script>'''

NOJS_SCRIPT = 'document.documentElement.className="js"'
NOJS_HASH = "sha256-" + base64.b64encode(hashlib.sha256(NOJS_SCRIPT.encode()).digest()).decode()

def layout(*, path, title, description, body, current, wa_message=None, schema=None, og_image="/assets/img/og-card.jpg", noindex=False, preload_img=None, preload_html=""):
    canonical = SITE_URL + path
    preload = preload_html
    if preload_img:
        pn, psizes = preload_img
        srcset = ", ".join(asset("assets/img/%s-%d.webp" % (pn, w_)) + " %dw" % w_ for w_ in _widths(pn))
        preload = f'<link rel="preload" as="image" imagesrcset="{srcset}" imagesizes="{psizes}" fetchpriority="high">\n'
    ld = ""
    if schema:
        blocks = schema if isinstance(schema, list) else [schema]
        for blk in blocks:
            obj = json.loads(blk) if isinstance(blk, str) else blk   # validate every block at build time
            ld += '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>\n"
    wa = f' data-wa-message="{E(wa_message)}"' if wa_message else ""
    robots = '<meta name="robots" content="noindex, nofollow">' if (PREVIEW or noindex) else ''
    cfg = (f' data-whatsapp="{E(PHONE_TEL.lstrip("+"))}" data-email="{E(EMAIL)}" data-wechat-id="{E(WECHAT_ID)}" data-wechat-qr="{E(asset(WECHAT_QR.lstrip("/")) if WECHAT_QR else "")}"'
           f' data-wechat-name="{E(WECHAT_NAME)}" data-wechat-channel="{E(WECHAT_CHANNEL)}"')
    og_url = SITE_URL + asset(og_image.lstrip("/"))
    doc = f'''<!DOCTYPE html>
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>{NOJS_SCRIPT}</script>
<title>{E(title)}</title>
<meta name="description" content="{E(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{E(BRAND)}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_url}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{E(title)}">
<meta name="twitter:description" content="{E(description)}">
<meta name="twitter:image" content="{og_url}">
<meta name="theme-color" content="#12161f">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" type="image/png" sizes="32x32">
<link rel="icon" href="/favicon-16.png" type="image/png" sizes="16x16">
<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180">
<link rel="manifest" href="/site.webmanifest">
{robots}
{preload}<link rel="preload" href="/assets/fonts/sora-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/inter-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/style.css?v={CSS_VER}">
{ld}</head>
<body{wa}{cfg}>
{header(current)}
<main id="main">
{body}
</main>
{footer()}
</body>
</html>'''
    if wa_message:
        # Generic WhatsApp links (header, hero, footer, chat menu, mobile bar) carry the page-context message statically,
        # so the no-JavaScript href and the JavaScript-enhanced href are identical.
        doc = doc.replace(f'data-wa href="{wa_link()}"', f'data-wa href="{wa_link(wa_message)}"')
    return doc

def breadcrumb(items):
    parts = ['<a href="/">Home</a>']
    for i, (label, href) in enumerate(items):
        parts.append(ic("chevron-r"))
        if i == len(items) - 1: parts.append(f'<span aria-current="page">{label}</span>')
        else: parts.append(f'<a href="{href}">{label}</a>')
    return f'<nav class="breadcrumb" aria-label="Breadcrumb">{"".join(parts)}</nav>'

def breadcrumb_schema(items):
    els = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"}]
    for i, (label, href) in enumerate(items, start=2):
        els.append({"@type": "ListItem", "position": i, "name": label, "item": SITE_URL + href})
    import json
    return json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": els})

def page_hero(title, lead, crumbs, image, alt, caption=None, ctas=None):
    ctas = ctas or f'<a class="btn btn--primary" href="/contact-us/">Get a quote</a><a class="btn btn--wa" data-wa href="{wa_link()}">{WA_SVG} WhatsApp us</a>'
    return f'''
<section class="page-hero">
  <div class="container page-hero__inner">
    <div>
      {breadcrumb(crumbs)}
      <h1>{title}</h1>
      <p class="lead">{lead}</p>
      <div class="btn-row">{ctas}</div>
    </div>
    {frame(image, alt, "3x4", caption, "(min-width: 960px) 40vw, 100vw", lazy=False)}
  </div>
</section>'''

def cta_band(title, text, primary=("Get a quote", "/contact-us/"), wa_label="WhatsApp us"):
    return f'''
<section class="section section--sm"><div class="container">
  <div class="cta-band reveal">
    <div><h2 class="h2">{title}</h2><p>{text}</p></div>
    <div class="btn-row"><a class="btn btn--primary btn--lg" href="{primary[1]}">{primary[0]}</a><a class="btn btn--wa btn--lg" data-wa href="{wa_link()}">{WA_SVG} {wa_label}</a></div>
  </div>
</div></section>'''

def inquiry_form(form_id="inquiry-form", compact=False):
    """WhatsApp composer. JavaScript builds a pre-filled wa.me draft from the fields and opens WhatsApp; nothing is posted to
    a server. Without JavaScript the form is hidden and a plain WhatsApp link plus the mailto address are shown instead."""
    countries = sorted(["Albania","Andorra","Australia","Austria","Bahrain","Belgium","Bosnia and Herzegovina","Bulgaria","Canada","Croatia","Cyprus","Czech Republic","Denmark","Estonia","Finland","France","Germany","Greece","Hungary","Iceland","Ireland","Italy","Jordan","Kuwait","Latvia","Liechtenstein","Lithuania","Luxembourg","Malta","Moldova","Monaco","Montenegro","Netherlands","New Zealand","North Macedonia","Norway","Oman","Poland","Portugal","Qatar","Romania","Saudi Arabia","Serbia","Slovakia","Slovenia","Spain","Sweden","Switzerland","Turkey","Ukraine","United Arab Emirates","United Kingdom","United States"]) + ["Other"]
    opts = "".join(f'<option value="{E(c)}">{E(c)}</option>' for c in countries)
    copts = "".join(f'<option value="{E(c)}">{E(c)}</option>' for c in CATEGORY_OPTIONS)
    sopts = "".join(f'<option value="{E(c)}">{E(c)}</option>' for c in SERVICE_OPTIONS)
    f = form_id
    def field(name, label, inp, err=None, opt=False):
        lab = f'<label for="{f}-{name}">{label}' + (' <span class="opt">(optional)</span>' if opt else '') + '</label>'
        errspan = f'<span class="err" id="{f}-{name}-err">{err}</span>' if err else ''
        return f'<div class="field">{lab}{inp}{errspan}</div>'
    name_f = field("name", "Name", f'<input id="{f}-name" name="name" required maxlength="80" autocomplete="name" data-label="Name" aria-describedby="{f}-name-err">', "Please enter your name.")
    company_f = field("company", "Company", f'<input id="{f}-company" name="company" maxlength="80" autocomplete="organization" data-label="Company">', opt=True)
    country_f = field("country", "Country", f'<select id="{f}-country" name="country" required data-label="Country" aria-describedby="{f}-country-err"><option value="">Select…</option>{opts}</select>', "Please choose your country.")
    category_f = field("category", "Product category", f'<select id="{f}-category" name="category" required data-label="Product category" aria-describedby="{f}-category-err"><option value="">Select…</option>{copts}</select>', "Please choose a category.")
    service_f = field("service", "Service required", f'<select id="{f}-service" name="service" data-label="Service required"><option value="">Select…</option>{sopts}</select>', opt=True)
    budget_f = field("budget", "Approximate budget or order quantity", f'<input id="{f}-budget" name="budget" maxlength="80" data-label="Approximate budget or quantity" placeholder="e.g. 500 units, or about £8,000" aria-describedby="{f}-budget-hint">' + ('' if compact else f'<span class="hint" id="{f}-budget-hint">A rough figure is enough. It helps us judge which factories fit.</span>'), opt=True)
    message_f = (f'<div class="field"><label for="{f}-message">Requirements</label><textarea id="{f}-message" name="message" required maxlength="1200" data-label="Requirements" aria-describedby="{f}-message-err {f}-message-count" placeholder="Describe the product, materials, target market, packaging or private-label needs, timelines — anything useful."></textarea>'
                 f'<div class="char-row"><span class="char-count" id="{f}-message-count" aria-live="polite" data-count></span></div><span class="err" id="{f}-message-err">Please tell us a little about your project.</span></div>')
    ack = (f'<div class="consent-wrap"><label class="consent"><input type="checkbox" id="{f}-ack" name="ack" value="yes" required aria-describedby="{f}-ack-err"><span>I have read the <a href="/privacy-policy/">Privacy Policy</a> and understand that continuing will open WhatsApp, where WhatsApp/Meta will process the information entered.</span></label>'
           f'<span class="err" id="{f}-ack-err">Please confirm you have read the Privacy Policy.</span></div>')
    layout_rows = (f'<div class="form__row">{name_f}{country_f}</div><div class="form__row">{category_f}{budget_f}</div>{message_f}'
                   if compact else
                   f'<div class="form__row">{name_f}{company_f}</div><div class="form__row">{country_f}{category_f}</div><div class="form__row">{service_f}{budget_f}</div>{message_f}')
    heading = '<h3 class="h3">Tell us what you need</h3>' if compact else '<h2 class="h3">Tell us what you need</h2>'
    intro = heading + '<p class="contact-summary form-intro">Complete the form and we’ll prepare a WhatsApp message for you. Review it and press Send in WhatsApp to contact our team.</p>'
    draft_note = f'<p class="form__note" id="{f}-draft-note">Continuing will open WhatsApp with a pre-filled draft. Your message is not sent to {E(BRAND)} until you press Send in WhatsApp.</p>'
    care_note = ('<p class="form__note form__note--files">Need to send photos or documents? Continue to WhatsApp and attach them directly in the conversation.</p>'
                 '<p class="form__note">Please do not include identification documents, payment-card details, sensitive personal information or confidential product files in the WhatsApp message. We can agree a secure way to share confidential documents once we are in touch.</p>')
    actions = f'<div class="form__actions"><button class="btn btn--wa-solid btn--lg" type="submit" aria-describedby="{f}-draft-note">{WA_SVG} Continue on WhatsApp</button><span class="form__status" role="status" aria-live="polite"></span></div>'
    next_box = (f'<div class="form-next" role="status" tabindex="-1" hidden><h3 class="h3">Your WhatsApp draft is ready</h3>'
                f'<p>WhatsApp should now be open with your draft. Review it and press Send in WhatsApp to contact our team. Nothing reaches {E(BRAND)} until you press Send.</p>'
                f'<p class="form-next__fallback">If WhatsApp did not open, use this link:</p>'
                f'<div class="btn-row"><a class="btn btn--wa-solid" data-wa-draft href="{wa_link()}" target="_blank" rel="noopener noreferrer">{WA_SVG} Open WhatsApp with my draft</a><a class="btn btn--outline" href="mailto:{E(EMAIL)}">{ic("mail")} Email us instead</a></div></div>')
    nojs = (f'<div class="form-nojs"><h3 class="h3">Contact us on WhatsApp or by email</h3><p>The enquiry form needs JavaScript to prepare a WhatsApp draft. You can message us directly instead:</p>'
            f'<div class="btn-row"><a class="btn btn--wa-solid" data-wa href="{wa_link()}">{WA_SVG} WhatsApp us</a><a class="btn btn--outline" href="mailto:{E(EMAIL)}">{ic("mail")} {E(EMAIL)}</a></div></div>')
    return f'\n{intro}\n<form class="form" id="{f}" data-inquiry novalidate>\n  {layout_rows}\n  {ack}\n  {draft_note}\n  {actions}\n  {care_note}\n</form>\n{next_box}\n{nojs}'

def quick_inquiry(title="Start your sourcing project", eyebrow="Quick enquiry", text=None, dark=False, grey=True):
    text = text or "Tell us what you want to source and where you sell. We will come back with the right suppliers, indicative pricing and next steps."
    cls = "section section--ink on-dark" if dark else ("section section--grey" if grey else "section")
    return f'''
<section class="{cls}" id="inquiry"><div class="container quick">
  <div class="reveal">
    <span class="eyebrow">{eyebrow}</span>
    <h2 class="h2">{title}</h2>
    <p class="lead mt-2">{text}</p>
    <ul class="contact-list">
      <li><span class="ico">{WA_SVG}</span><div><strong>WhatsApp</strong><a data-wa href="{wa_link()}">{PHONE_DISPLAY}</a></div></li>
      <li><span class="ico">{ic("mail")}</span><div><strong>Email</strong><a href="mailto:{E(EMAIL)}">{E(EMAIL)}</a></div></li>
      <li><span class="ico">{WC_SVG}</span><div><strong>WeChat</strong><button class="link-arrow" data-wechat type="button">WeChat ID: {E(WECHAT_ID)} {ic("arrow")}</button></div></li>
      <li><span class="ico">{ic("pin")}</span><div><strong>Office</strong><span class="val">{E(ADDRESS)}</span></div></li>
      <li><span class="ico">{ic("clock")}</span><div><strong>Hours</strong><span class="val">{E(HOURS)}</span></div></li>
    </ul>
  </div>
  <div class="form-card reveal" data-delay="1">
    {inquiry_form("quick-form", compact=True)}
    <div class="wa-alt mt-3"><div><strong>Prefer to talk now?</strong><span>Send a photo or link of the product and we will take it from there.</span></div><a class="btn btn--wa-solid btn--sm" data-wa href="{wa_link()}">{WA_SVG} WhatsApp us</a></div>
  </div>
</div></section>'''

# ----------------------------------------------------------------------------
# HOME
# ----------------------------------------------------------------------------
SERVICES = [
    ("product-sourcing", "search", "Product Sourcing", "Tell us the product, spec and target market. We identify manufacturers that already make it well, not just the ones with the loudest listings."),
    ("factory-verification", "factory", "Factory Verification", "Supplier screening before you commit: business records, production capability, export history and, where needed, an in-person visit."),
    ("negotiation", "tag", "Price Negotiation", "Local negotiation in Chinese, directly with the factory, so quotes are benchmarked against the real cost base rather than accepted at face value."),
    ("samples", "flask", "Samples & Product Development", "Sample coordination, revisions and virtual sample approval, so you can confirm materials, finish and function before production starts."),
    ("quality-inspection", "shield", "Quality Inspection", "Production checks and pre-shipment inspection against your agreed specification, with photos and reports before anything ships."),
    ("compliance", "file-check", "Compliance Support", "We help identify the documentation your market may require and coordinate it with the supplier and test bodies before goods leave China."),
    ("packaging", "package", "Packaging & Private Label", "Coordination of branded packaging, labelling and private-label requirements with the factory, so your product arrives retail-ready."),
    ("logistics", "ship", "Logistics & Delivery", "Consolidation, export documentation support and freight arrangement to Europe, the Middle East and beyond, tracked through to delivery."),
]

STEPS = [
    ("Tell us what you need", "Share a product link, photo, sample or spec and where you sell. A short WhatsApp message is enough to start."),
    ("We find & screen suppliers", "We shortlist manufacturers, screen them and confirm capability, so you only see options worth your time."),
    ("Samples & pricing", "You receive negotiated quotes and samples. Approve in person, or remotely with photos and video."),
    ("Production", "We coordinate the order, timelines and any packaging or private-label requirements with the factory."),
    ("Quality inspection", "Goods are checked against your specification before shipment, with a photo report for your sign-off."),
    ("Shipping & delivery", "Consolidation, export documentation support and freight to your door, with the documentation your market may require coordinated in advance."),
]

CATEGORIES = [
    ("automotive", "inspection-emc", "Automotive & Auto Parts", "Vehicles, replacement parts, accessories and mobility products.", "EU · GCC"),
    ("furniture", "cat-furniture", "Home Furniture & Building Materials", "Furniture, fixtures and materials for residential, hospitality and commercial projects.", "CE · REACH · GCC"),
    ("apparel", "cat-apparel", "Apparel, Jewelry & Fashion Accessories", "Ready-to-wear, fine jewelry and trend-driven accessories, mass or small batch.", "Private label"),
    ("electronics", "cat-electronics", "Electronics", "Consumer electronics, smart devices and components with pre-shipment testing.", "CE · RoHS · FCC"),
    ("beauty", "cat-beauty", "Beauty & Health Care", "Cosmetics, skincare and personal care with ingredient and regulatory documentation.", "GMP · CPNP · GSO"),
    ("other", "cat-other", "Other Sourcing Categories", "Flexible one-stop sourcing for miscellaneous goods based on your project brief.", "Custom"),
]

def testimonials_section():
    if not EVIDENCE["reviews"]: return ""
    cards = "".join(f'<blockquote class="testimonial reveal" data-delay="{i}"><p>“{E(r["quote"])}”</p><footer><div><strong>{E(r["name"])}</strong>{E(r.get("company",""))}{", " if r.get("company") else ""}{E(r.get("country",""))}</div></footer></blockquote>' for i, r in enumerate(EVIDENCE["reviews"]))
    return f'<section class="section section--grey" id="testimonials"><div class="container"><div class="section-head reveal"><span class="eyebrow">What buyers say</span><h2 class="h2">Client feedback</h2></div><div class="grid grid-3">{cards}</div></div></section>'

def home():
    facts = [
        ("Screened suppliers", "Factories are screened for capability, business records and export history before you speak to them."),
        ("Quality before shipment", "Production checks and pre-shipment inspection against your spec, with a photo report for sign-off."),
        ("Factory-direct pricing", "Negotiated locally, in Chinese, at the factory, with quotes benchmarked across suppliers and commercial terms agreed in writing."),
        ("Delivery coordination", "Consolidation, export documentation support and freight to Europe, the Middle East and beyond."),
    ]
    facts_html = "".join(f'<li class="fact reveal" data-delay="{i}"><span class="fact__num">0{i+1}</span><strong class="fact__title">{t}</strong><p>{d}</p></li>' for i, (t, d) in enumerate(facts))
    services_html = "".join(f'<li class="index-row reveal" data-delay="{i % 3}"><span class="index-row__num">0{i+1}</span><h3>{t}</h3><p>{d}</p><a class="link-arrow stretched" href="/sourcing-services/#{slug}">Learn more<span class="visually-hidden"> about {t.lower()}</span> {ic("arrow")}</a></li>' for i, (slug, icn, t, d) in enumerate(SERVICES))
    steps_html = "".join(f'<li class="step reveal" data-delay="{i % 3}"><span class="step__num">0{i+1}</span><div><h3>{t}</h3><p>{d}</p></div></li>' for i, (t, d) in enumerate(STEPS))
    cats_html = "".join(f'<a class="cat-card reveal" data-delay="{i % 3}" href="/product-categories/#{slug}">{img(im, CAT_ALTS[slug], "(min-width: 900px) 33vw, 50vw")}<span class="cat-card__num">0{i+1}</span><span class="cat-card__tag">{tag}</span><div class="cat-card__body"><h3>{t}</h3><p>{d}</p></div></a>' for i, (slug, im, t, d, tag) in enumerate(CATEGORIES))
    gallery = [
        ("span-2 row-2", "team-factory", "The Flawless Effect team with international partners inside a vehicle test chamber at an automotive factory", "Inside a vehicle test chamber with international partners during an automotive factory visit."),
        ("", "exhibition-middle-east", "Meeting buyers from the Gulf at a trade exhibition in China", "Meeting Gulf buyers at a trade exhibition."),
        ("", "leap-east-hk", "Attending LEAP East at the Hong Kong Convention and Exhibition Centre, July 2026", "LEAP East, Hong Kong Convention Centre, July 2026."),
        ("", "sample-review", "Working session with a visiting buyer at Flawless Effect’s meeting space in Guangzhou", "Working session with a visiting buyer in Guangzhou."),
        ("", "meeting-skyline", "Flawless Effect meeting and dining space in Guangzhou with the city skyline behind", "Our meeting space in Guangzhou, where buyers review samples and meet suppliers."),
    ]
    gallery_html = "".join(f'<figure class="{cls} reveal" data-delay="{i % 4}"><div class="img-frame">{img(im, alt, "(min-width: 900px) 25vw, 50vw")}</div><figcaption>{cap}</figcaption></figure>' for i, (cls, im, alt, cap) in enumerate(gallery))
    hero_img = img("factory-tour", "Flawless Effect on a factory floor in China with a group of visiting international buyers, all wearing hi-vis vests", "(min-width: 1280px) 1180px, 100vw", lazy=False, fetchpriority="high")
    body = f'''
<section class="hero">
  <div class="container">
    <div class="hero__top">
      <div class="reveal is-in">
        <span class="eyebrow">China sourcing agent · Guangzhou</span>
        <h1>China sourcing agent in Guangzhou. <span class="accent">Your bridge to trusted Chinese factories.</span></h1>
        <p class="hero__lead">{BRAND} helps international businesses source products from China. We find and screen factories, negotiate pricing, manage samples and production, inspect quality and coordinate delivery, from our base in Guangzhou.</p>
        <div class="hero__ctas"><a class="btn btn--primary btn--lg" href="/contact-us/">Get a quote {ic("arrow")}</a><a class="btn btn--wa-solid btn--lg" data-wa href="{wa_link()}">{WA_SVG} WhatsApp us</a></div>
      </div>
      <ul class="hero__facts reveal is-in" data-delay="1">
        <li><span>Based in</span><strong>Guangzhou, China</strong></li>
        <li><span>Markets supported</span><strong>Europe &amp; Middle East</strong></li>
        <li><span>Reach us on</span><strong>WhatsApp, WeChat, email</strong></li>
      </ul>
    </div>
    <div class="hero__band reveal is-in" data-delay="2">
      <div class="hero__photo">
        {hero_img}
        <div class="hero__photo-cap"><span>{ic("pin")}Factory floor visit with international buyers, China</span></div>
      </div>
      <div class="hero__video">
        <video muted loop playsinline preload="none" poster="{asset("assets/img/factory-line-poster.webp")}" width="360" height="640" data-webm="{asset("assets/video/factory-line.webm")}" data-mp4="{asset("assets/video/factory-line.mp4")}" aria-label="Robotic production line at an automotive factory visited by Flawless Effect"></video>
        <img src="{asset("assets/img/factory-line-poster-240.webp")}" srcset="{asset("assets/img/factory-line-poster-240.webp")} 240w, {asset("assets/img/factory-line-poster.webp")} 360w" sizes="118px" alt="Robotic production line at an automotive factory visited by Flawless Effect" width="240" height="427" loading="lazy" decoding="async">
        <span class="hero__video-cap"><span class="rec"></span>Production line, factory visit</span>
      </div>
    </div>
  </div>
</section>

<section class="section section--sm" aria-label="What Flawless Effect does for buyers"><div class="container"><ul class="facts">{facts_html}</ul></div></section>

<section class="section section--grey" id="services"><div class="container">
  <div class="section-head section-head--row reveal"><div><span class="eyebrow">Core services</span><h2 class="h2">End-to-end sourcing, from first brief to final delivery</h2></div><p class="lead">Use one service or the whole chain. Every step is managed by the same team, so nothing is lost between supplier, inspector and forwarder.</p></div>
  <ol class="index-list index-list--on-grey">{services_html}</ol>
  <div class="btn-row mt-5"><a class="btn btn--primary" href="/sourcing-services/">Explore all services {ic("arrow")}</a><a class="btn btn--outline" href="/certifications/">Compliance &amp; certifications</a></div>
</div></section>

<section class="section" id="presence"><div class="container">
  <div class="section-head section-head--row reveal"><div><span class="eyebrow">On the ground in China</span><h2 class="h2">Real people, real factories</h2></div><div><p class="lead">{BRAND} is based at Pazhou Digital Science and Technology Industrial Park in Guangzhou. We attend exhibitions, walk factory floors, sit in negotiations and check goods before they ship. The factory, exhibition and meeting photographs on this site are from our own visits.</p><a class="link-arrow mt-3" href="/about-us/">About {BRAND} {ic("arrow")}</a></div></div>
  <div class="gallery">{gallery_html}</div>
</div></section>

<section class="section section--ink on-dark" id="how-it-works"><div class="container">
  <div class="process">
    <div class="process__media reveal">
      <div class="img-frame">{img("showroom-meeting", "Two buyers in discussion at a supplier showroom in Guangzhou", "(min-width: 960px) 45vw, 100vw")}
        <div class="process__quote"><strong>Most projects start with one message.</strong>Send a product photo or link and we will tell you honestly whether it is a good fit for sourcing from China.</div>
      </div>
    </div>
    <div>
      <div class="section-head reveal"><span class="eyebrow">How sourcing works</span><h2 class="h2">Six steps from idea to delivered goods</h2><p class="lead">You stay in control of every decision. We handle the legwork in China.</p></div>
      <ol class="steps">{steps_html}</ol>
      <p class="steps-note reveal">Want the detail behind each step? Our guides cover <a href="/guides/how-to-find-reliable-chinese-factories/">finding reliable factories</a>, <a href="/guides/quality-inspection-guide/">quality inspection</a> and <a href="/guides/china-sourcing-costs/">landed costs</a>.</p>
      <div class="steps-cta reveal"><a class="btn btn--wa-solid" data-wa="Hi, I'd like to check whether a product is a good fit for sourcing from China. Can I send you the details?" href="{wa_link("Hi, I'd like to check whether a product is a good fit for sourcing from China. Can I send you the details?")}">{WA_SVG} Send us your product</a><a class="btn btn--outline" href="/contact-us/">Get a quote</a></div>
    </div>
  </div>
</div></section>

<section class="section" id="categories"><div class="container">
  <div class="section-head section-head--row reveal"><div><span class="eyebrow">Product categories</span><h2 class="h2">What we source</h2></div><p class="lead">Our core verticals, each with an understanding of the documentation that market may require. Do not see yours? We take on custom briefs too.</p></div>
  <div class="cat-scroller">{cats_html}</div>
</div></section>

<section class="section section--grey"><div class="container">
  <div class="section-head section-head--row reveal"><div><span class="eyebrow">Regional &amp; compliance support</span><h2 class="h2">Built for buyers in Europe and the Middle East</h2></div><p class="lead">Support is scoped around your product, destination market and the supplier documentation available, with communication aligned to your working hours. Requirements shown are examples and depend on the product; the importer should confirm them with the relevant authority or adviser.</p></div>
  <div class="grid grid-2">
    <article class="region-card reveal">{frame("exhibition-meeting", "Flawless Effect in conversation with a buyer at a trade exhibition", "auto", None, "(min-width: 720px) 200px, 100vw")}<div class="region-card__body"><h3>Europe</h3><p>Markets covered include Germany, France, Italy, Spain and the Netherlands. We coordinate supplier documentation for European requirements, quality control and production scheduling.</p><p class="chips-label">Requirements may include</p><div class="chips"><span class="chip">CE</span><span class="chip">REACH</span><span class="chip">RoHS</span><span class="chip">WVTA</span></div><a class="link-arrow mt-3" href="/regional-support/#europe">Europe support {ic("arrow")}</a></div></article>
    <article class="region-card reveal" data-delay="1">{frame("exhibition-middle-east", "Flawless Effect meeting buyers from the Gulf at a trade exhibition", "auto", None, "(min-width: 720px) 200px, 100vw")}<div class="region-card__body"><h3>Middle East</h3><p>Markets covered include the UAE, Saudi Arabia, Qatar, Kuwait, Bahrain, Oman and Jordan, across both GCC and non-GCC import rules.</p><p class="chips-label">Requirements may include</p><div class="chips"><span class="chip">GCC</span><span class="chip">GSO</span><span class="chip">Import consulting</span></div><a class="link-arrow mt-3" href="/regional-support/#middle-east">Middle East support {ic("arrow")}</a></div></article>
  </div>
</div></section>

{testimonials_section()}
{quick_inquiry(dark=False, grey=False)}
'''
    org = {"@type": "Organization", "@id": SITE_URL + "/#org", "name": BRAND, "url": SITE_URL + "/", "logo": SITE_URL + asset("assets/img/brand/fe-logo-3x.png"), "email": EMAIL, "telephone": "+86-190-4279-9025", "sameAs": [INSTAGRAM] + ([LINKEDIN_URL] if LINKEDIN_URL else []),
           "address": {"@type": "PostalAddress", "streetAddress": "Pazhou Digital Science and Technology Industrial Park", "addressLocality": "Guangzhou", "addressRegion": "Guangdong", "addressCountry": "CN"},
           "contactPoint": {"@type": "ContactPoint", "contactType": "sales", "telephone": "+86-190-4279-9025", "email": EMAIL}}
    schema = {"@context": "https://schema.org", "@graph": [org,
        {"@type": "ProfessionalService", "@id": SITE_URL + "/#business", "name": "Flawless Effect — China Sourcing Agent", "url": SITE_URL + "/", "image": SITE_URL + asset("assets/img/og-card.jpg"), "telephone": "+86-190-4279-9025", "email": EMAIL,
         "address": {"@type": "PostalAddress", "streetAddress": "Pazhou Digital Science and Technology Industrial Park", "addressLocality": "Guangzhou", "addressRegion": "Guangdong", "addressCountry": "CN"}, "areaServed": ["Europe", "Middle East"], "parentOrganization": {"@id": SITE_URL + "/#org"},
         "description": "China sourcing agent in Guangzhou providing supplier screening, price negotiation, samples, quality inspection, documentation support and logistics coordination for international buyers."},
        {"@type": "WebSite", "@id": SITE_URL + "/#website", "url": SITE_URL + "/", "name": BRAND, "publisher": {"@id": SITE_URL + "/#org"}}]}
    return layout(path="/", current="/", title="China Sourcing Agent in Guangzhou | Flawless Effect",
                  description="Source products from China with a Guangzhou sourcing agent: screened factories, negotiated pricing, samples, quality inspection and delivery coordination.",
                  body=body, schema=schema, preload_img=("factory-tour", "(min-width: 1280px) 1180px, 100vw"))

# ----------------------------------------------------------------------------
# ABOUT
# ----------------------------------------------------------------------------
# Genuine trust evidence — fill in when verified; each block renders only when populated.
EVIDENCE = {
    "team": [],            # e.g. {"name": "…", "role": "…", "photo": "team-name"}  (photo = asset name in assets/img)
    "registration": "",   # e.g. "Registered in Guangzhou, China. Business registration no. …"
    "case_studies": [],    # e.g. {"title": "…", "summary": "…", "image": "asset-name", "facts": ["…", "…"]}
    "reviews": [],         # e.g. {"quote": "…", "name": "…", "company": "…", "country": "…"}
    "reports": [],         # e.g. {"title": "Redacted inspection report", "file": "/assets/docs/…pdf", "note": "…"}
}

def team_section():
    if not EVIDENCE["team"]: return ""
    cards = "".join(f'<article class="team-card reveal" data-delay="{i}"><div class="img-frame img-frame--4x5">{img(m["photo"], m["name"], "(min-width: 1024px) 33vw, (min-width: 720px) 50vw, 100vw")}</div><h3>{E(m["name"])}</h3><p>{E(m["role"])}</p>{"<p class=muted>Languages: " + E(m["languages"]) + "</p>" if m.get("languages") else ""}</article>' for i, m in enumerate(EVIDENCE["team"]))
    return f'<section class="section" id="team"><div class="container"><div class="section-head reveal"><span class="eyebrow">Meet the team</span><h2 class="h2">The people you will deal with</h2></div><div class="grid grid-3">{cards}</div></div></section>'

def evidence_section():
    parts = []
    if EVIDENCE["team"]:
        parts.append('<div class="grid grid-3">' + "".join(f'<div class="service-card"><h3>{m["name"]}</h3><p>{m["role"]}</p></div>' for m in EVIDENCE["team"]) + "</div>")
    if EVIDENCE["registration"]:
        parts.append(f'<p class="lead">{EVIDENCE["registration"]}</p>')
    if EVIDENCE["case_studies"]:
        parts.append('<div class="grid grid-2">' + "".join(f'<article class="service-card"><h3>{c["title"]}</h3><p>{c["summary"]}</p><ul class="check-list">{"".join(f"<li>{ic(chr(99)+chr(104)+chr(101)+chr(99)+chr(107))}<span>{x}</span></li>" for x in c.get("facts", []))}</ul></article>' for c in EVIDENCE["case_studies"]) + "</div>")
    if EVIDENCE["reviews"]:
        parts.append('<div class="grid grid-3">' + "".join(f'<blockquote class="testimonial"><p>“{r["quote"]}”</p><footer><div><strong>{r["name"]}</strong>{r["company"]}, {r["country"]}</div></footer></blockquote>' for r in EVIDENCE["reviews"]) + "</div>")
    if EVIDENCE["reports"]:
        parts.append('<ul class="check-list">' + "".join(f'<li>{ic("file-check")}<span><a href="{r["file"]}">{r["title"]}</a> — {r["note"]}</span></li>' for r in EVIDENCE["reports"]) + "</ul>")
    if not parts: return ""
    return f'<section class="section section--grey"><div class="container"><div class="section-head reveal"><span class="eyebrow">Evidence</span><h2 class="h2">Verified details</h2></div>{"".join(parts)}</div></section>'

def about():
    crumbs = [("About", "/about-us/")]
    spaces = ["lounge-a", "dining-table", "lounge-interior", "lobby-overhead", "buyer-briefing", "remote-work-laptop", "lobby-wood", "meeting-skyline"]
    alts = ["Lounge area at Flawless Effect’s meeting space in Guangzhou", "Round dining table at the Guangzhou meeting space", "Interior of the Guangzhou meeting lounge", "Overhead view of the lobby at the Guangzhou meeting space", "Buyers watching a presentation in the Guangzhou lounge", "Laptop set up for a remote factory tour at the Guangzhou meeting space", "Sunlit lobby of the Guangzhou meeting space", "Dining room with a view of the Guangzhou skyline"]
    spaces_html = "".join(f'<figure class="reveal" data-delay="{i % 4}"><div class="img-frame">{img(s, a, "(min-width: 900px) 25vw, 50vw")}</div></figure>' for i, (s, a) in enumerate(zip(spaces, alts)))
    events = [("leap-into-new-worlds", "Flawless Effect at LEAP East, Hong Kong Convention and Exhibition Centre, July 2026", "LEAP East, Hong Kong, July 2026"), ("exhibition-robot", "Flawless Effect with partners at a technology exhibition stand featuring a humanoid robot", "Technology exhibition, Hong Kong"), ("leap-conference", "Flawless Effect at the LEAP conference main stage", "LEAP conference"), ("great-wall-event", "Flawless Effect at an automotive industry event held at the Great Wall", "Automotive industry event, Great Wall")]
    events_html = "".join(f'<figure class="reveal" data-delay="{i % 4}"><div class="img-frame has-caption">{img(s, a, "(min-width: 900px) 25vw, 50vw")}<span class="img-caption">{c}</span></div></figure>' for i, (s, a, c) in enumerate(events))
    body = page_hero("The buyer’s bridge to Chinese factories", f"{BRAND} connects international buyers with dependable Chinese factories, combining local knowledge, careful screening and hands-on coordination from first brief to final delivery.", crumbs, "factory-tour", "Flawless Effect on a factory floor visit with a group of visiting buyers", "Factory floor visit with buyers") + f'''
<section class="section"><div class="container split">
  <div class="reveal">
    <span class="eyebrow">Who we are</span>
    <h2 class="h2">Sourcing with confidence, from Guangzhou</h2>
    <p class="lead mt-2">{BRAND} is a China sourcing agency based at Pazhou Digital Science and Technology Industrial Park in Guangzhou, the city that hosts the Canton Fair and sits at the centre of southern China’s manufacturing belt.</p>
    <p class="mt-2 muted">We work for the buyer, not the factory. Our job is to make a purchase from China behave like a purchase from a supplier down the road: a clear specification, a screened manufacturer, an agreed price, inspected goods and a delivery you can plan around.</p>
    <p class="mt-2 muted">Because we are here, we can attend exhibitions with you, walk factory floors, sit in negotiations and check goods before they ship. And when you cannot travel, we bring the factory to you through remote tours and virtual sample approval.</p>
  </div>
  <div class="reveal" data-delay="1">{frame("team-factory", "The Flawless Effect team with international partners inside a vehicle test chamber", "4x3", "Team visit, automotive test facility")}</div>
</div></section>

<section class="section section--grey"><div class="container">
  <div class="section-head reveal"><span class="eyebrow">Our story</span><h2 class="h2">Built for buyers</h2></div>
  <div class="timeline">
    <div class="timeline__item reveal"><span class="year">Beginning</span><h3>Our start, in China</h3><p>{BRAND} started with a simple idea: local insight turns complex China sourcing into clear, controlled business decisions.</p></div>
    <div class="timeline__item reveal" data-delay="1"><span class="year">Guangzhou</span><h3>Our base</h3><p>Located in the Pazhou exhibition district, with meeting spaces where buyers review samples, meet suppliers and join remote factory tours.</p></div>
    <div class="timeline__item reveal" data-delay="2"><span class="year">Today</span><h3>Connected across borders</h3><p>Supporting buyers across Europe and the Middle East, with support scoped around each product, destination market and the supplier documentation available.</p></div>
  </div>
</div></section>

<section class="section"><div class="container">
  <div class="section-head reveal"><span class="eyebrow">Who we help</span><h2 class="h2">From a first product to a full supply chain</h2><p class="lead">We work with e-commerce and Amazon sellers, retailers, wholesalers, distributors, private-label brands and companies developing new products. The process scales from a first sample order to repeat production orders.</p></div>
  <div class="grid grid-3">
    <div class="service-card reveal"><span class="service-card__icon">{ic("sparkle")}</span><h3>Launching a product</h3><p>You have an idea, a reference product or a spec. We find who can make it, get samples and tell you what it will really cost.</p></div>
    <div class="service-card reveal" data-delay="1"><span class="service-card__icon">{ic("trending")}</span><h3>Scaling an existing line</h3><p>You already import but want better pricing, a second supplier or tighter quality control. We audit, negotiate and inspect.</p></div>
    <div class="service-card reveal" data-delay="2"><span class="service-card__icon">{ic("layers")}</span><h3>Managing complex orders</h3><p>Multiple factories, private-label packaging and certification across markets. We coordinate the whole chain from Guangzhou.</p></div>
  </div>
</div></section>

<section class="section section--grey"><div class="container">
  <div class="section-head reveal"><span class="eyebrow">Our meeting spaces</span><h2 class="h2">Where buyers meet suppliers in Guangzhou</h2><p class="lead">Visiting China? Our meeting spaces are where we host buyers, review samples and run negotiations with factories. Not travelling? The same rooms are set up for remote factory tours and video sample approval.</p></div>
  <div class="gallery">{spaces_html}</div>
</div></section>

<section class="section"><div class="container">
  <div class="section-head reveal"><span class="eyebrow">Exhibitions &amp; industry events</span><h2 class="h2">Where we keep our supplier network current</h2><p class="lead">We attend industry events and exhibitions across China and Hong Kong, so that when you ask for a category, we already know who is making it well this year.</p></div>
  <div class="gallery">{events_html}</div>
</div></section>
<section class="section section--grey"><div class="container quote-block">
  <div class="reveal">{frame("client-dinner", "Flawless Effect hosting visiting partners at dinner in China", "4x3", "Hosting visiting partners", "(min-width: 900px) 40vw, 100vw")}</div>
  <div class="reveal" data-delay="1"><blockquote>“Local insight turns complex China sourcing into clear, controlled business decisions.”</blockquote><cite>The principle {BRAND} was founded on</cite>
  <div class="btn-row mt-4"><a class="btn btn--primary" href="/contact-us/">Contact our China team {ic("arrow")}</a><a class="btn btn--outline" href="/sourcing-services/">Our services</a></div></div>
</div></section>
{team_section()}
'''+'''</div></section>
''' + evidence_section() + cta_band("Talk to a real person in Guangzhou", "Send a message on WhatsApp and you will be speaking with the team that visits the factories, not a call centre.", wa_label="WhatsApp us")
    return layout(path="/about-us/", current="/about-us/", title="About Our China Sourcing Team | Flawless Effect",
                  description="Meet the Guangzhou team behind Flawless Effect: factory visits, exhibitions, virtual tours and end-to-end procurement support for international buyers.",
                  body=body, schema=breadcrumb_schema(crumbs))

# ----------------------------------------------------------------------------
# SERVICES
# ----------------------------------------------------------------------------
def fee_section():
    if not FEE_MODEL: return ""
    return f'<section class="section section--sm section--grey" id="how-we-charge"><div class="container container--narrow"><div class="section-head reveal"><span class="eyebrow">How we charge</span><h2 class="h2">Clear fees, agreed before work starts</h2></div><div class="service-card reveal"><p>{E(FEE_MODEL)}</p></div></div></section>'

SERVICE_LINK_NAMES = {"product-sourcing": "Product sourcing", "factory-verification": "Factory verification", "negotiation": "Price negotiation", "samples": "Samples & product development", "quality-inspection": "Quality inspection", "compliance": "Compliance & certification support", "packaging": "Packaging & private label", "logistics": "Logistics & delivery"}

def services():
    crumbs = [("Sourcing Services", "/sourcing-services/")]
    rows = [
        ("product-sourcing", "search", "Product Sourcing", "factory-tour", "Flawless Effect walking a factory floor with visiting buyers",
         "You describe the product; we find who makes it well. Rather than scraping marketplace listings, we draw on factories we have visited, exhibitions we attend and a supplier network built from Guangzhou. Read <a href=\"/guides/how-to-find-reliable-chinese-factories/\">how we find reliable Chinese factories</a>.",
         ["Sourcing from a photo, link, sample or full specification", "Shortlist of capable manufacturers, not trading companies", "Honest feedback on whether a product is a good fit for China", "Exhibition and showroom visits, in person or on your behalf"],
         ["Less time", "Right supplier", "Lower risk"]),
        ("factory-verification", "factory", "Factory Verification", "inspection-emc", "Flawless Effect inside a vehicle test chamber during a factory inspection",
         "A good price from the wrong supplier is the most expensive mistake in sourcing. Before you commit, we screen the factory’s business records, production capability, export history and, where the order justifies it, visit in person. Our <a href=\"/guides/supplier-verification-checklist/\">supplier verification checklist</a> shows what we look for.",
         ["Business licence and registration checks", "Production capability and capacity review", "On-site visits with photo and video reporting", "Ongoing supplier relationship management"],
         ["Supplier certainty", "Fraud protection", "Peace of mind"]),
        ("negotiation", "tag", "Price Negotiation", "exhibition-meeting", "Flawless Effect negotiating with a supplier at a trade exhibition",
         "We negotiate in Chinese, at the factory, with knowledge of local cost structures. Negotiating directly with the factory, with quotes benchmarked across suppliers, gives you pricing you can build a business case on.",
         ["Quotes benchmarked across multiple factories", "MOQ, payment terms and lead times negotiated on your behalf", "Clear breakdown of unit cost, packaging, tooling and freight", "Commercial terms agreed in writing before work starts"],
         ["Lower cost", "Better terms", "Clarity"]),
        ("samples", "flask", "Samples & Product Development", "sample-review", "Working session reviewing product samples with a visiting buyer in Guangzhou",
         "Approve the product before the production run. We coordinate samples, revisions and pre-production units, and if you cannot fly in, we review them on camera with you so nothing is lost in translation.",
         ["Sample sourcing, consolidation and international shipping", "Virtual sample approval with photos and live video", "Revision management between you and the factory", "Support for custom products, tooling and moulds"],
         ["Right first time", "Fewer revisions", "Faster launch"]),
        ("quality-inspection", "shield", "Quality Inspection", "team-factory", "Flawless Effect team with partners at an automotive test facility",
         "Problems found in China are cheap to fix. Problems found at your warehouse are not. We check production and inspect finished goods against your agreed specification before anything is loaded; our <a href=\"/guides/quality-inspection-guide/\">quality inspection guide</a> explains how sampling and reports work.",
         ["During-production checks on larger orders", "Pre-shipment inspection with photo report for sign-off", "Function, finish, packaging and labelling checks", "Coordination of corrective action with the factory where issues are found"],
         ["Fewer defects", "No surprises", "Protected reputation"]),
        ("compliance", "file-check", "Compliance & Certification Support", "factory-credentials-wall", "Wall of qualification plaques photographed during a factory visit in China",
         "Every market has documentation requirements, and gaps can delay goods at the border. We help identify the requirements your destination is likely to have and coordinate supplier documentation and testing, working with the factory and test bodies. Requirements depend on the product and destination and should be confirmed by the importer with the relevant authority or adviser.",
         ["Requirements may include CE, RoHS or REACH for Europe and FCC or CARB for the US", "Requirements may include GCC or GSO conformity for Middle East markets", "Coordination of supplier documentation for approval questions such as WVTA for vehicles into Europe", "Review of supplier test reports and technical files for consistency"],
         ["Documentation support", "Market entry", "Start early"]),
        ("packaging", "package", "Packaging & Private Label", "cat-other", "Retail shelving with a wide range of consumer goods",
         "Your brand on the box, not the factory’s. We coordinate custom packaging, labelling, inserts and private-label requirements with the manufacturer and confirm them at inspection.",
         ["Custom retail and e-commerce packaging coordination", "Labelling to destination-market requirements", "Private-label and OEM project management", "Packaging checked at pre-shipment inspection"],
         ["Retail-ready", "Brand control", "One coordinator"]),
        ("logistics", "ship", "Logistics & Delivery", "lobby-wood", "Sunlit lobby of Flawless Effect’s Guangzhou meeting space",
         "We consolidate goods from multiple factories, support export documentation and arrange sea, air or express freight to your door, tracked through to delivery.",
         ["Consolidation of multiple suppliers into one shipment", "Support with commercial documentation for export", "Freight arrangement to Europe, the Middle East and beyond", "Delivery coordination and tracking until receipt"],
         ["Door to door", "Fewer shipments", "Tracked"]),
    ]
    rows_html = ""
    for i, (slug, icn, title, im, alt, text, points, tags) in enumerate(rows):
        rev = " rev" if i % 2 else ""
        pts = "".join(f"<li>{ic('check')}<span>{p}</span></li>" for p in points)
        tg = "".join(f"<span>{t}</span>" for t in tags)
        wa_msg = f"Hi, I'd like to ask about your {title.lower()} service."  # interpolated here: a plain string inside an f-string expression is not itself an f-string
        rows_html += f'''<article class="service-row{rev}" id="{slug}">
      <div class="service-row__media reveal">{frame(im, alt, "4x3")}</div>
      <div class="reveal" data-delay="1"><span class="service-card__icon">{ic(icn)}</span><h2>{title}</h2><p>{text}</p><ul class="check-list">{pts}</ul><div class="value-tags">{tg}</div>
      <div class="btn-row mt-4"><a class="btn btn--primary btn--sm" href="/contact-us/?service={quote(SERVICE_LINK_NAMES.get(slug, title))}">Get a quote</a><a class="btn btn--wa btn--sm" data-wa="{E(wa_msg)}" href="{wa_link(wa_msg)}">{WA_SVG} WhatsApp us</a></div></div>
    </article>'''
    modes = f'''
<section class="section section--grey"><div class="container">
  <div class="section-head reveal"><span class="eyebrow">Two ways to work with us</span><h2 class="h2">In China with you, or in China for you</h2></div>
  <div class="grid grid-2">
    <article class="service-card reveal"><span class="service-card__icon">{ic("users")}</span><h3>On-site support</h3><p>Coming to China? We coordinate exhibitions, factory visits and on-site negotiations with trusted local guidance and clear communication throughout your trip, from the airport to the factory gate.</p><a class="link-arrow" href="/contact-us/?service={quote("On-site support (visiting China)")}">Enquire about on-site support {ic("arrow")}</a></article>
    <article class="service-card reveal" data-delay="1"><span class="service-card__icon">{ic("video")}</span><h3>Virtual sourcing</h3><p>Not travelling? Tour factories remotely, confirm samples on video and meet screened suppliers from your desk. Our Guangzhou meeting rooms are set up for exactly this.</p><a class="link-arrow" href="/contact-us/?service={quote("Virtual sourcing (remote)")}">Enquire about virtual sourcing {ic("arrow")}</a></article>
  </div>
</div></section>'''
    body = page_hero("Sourcing services that reduce risk, time and cost", "Use one service or the whole chain. Each step is designed to remove a specific way that buying from China goes wrong.", crumbs, "showroom-meeting", "Two buyers in discussion at a supplier showroom in Guangzhou", "Supplier showroom, Guangzhou") + modes + f'''
<section class="section"><div class="container">{rows_html}</div></section>
{fee_section()}
'''+'''</div></section>
''' + quick_inquiry("Tell us what you need sourced", "Start a project", "Send a product link, photo or spec. We will reply with a view on feasibility, indicative pricing and the next step.")
    return layout(path="/sourcing-services/", current="/sourcing-services/", title="China Sourcing Services & QC | Flawless Effect",
                  description="Product sourcing, factory screening, negotiation, samples, quality inspection, documentation support, private label and logistics, managed from Guangzhou.",
                  body=body, schema=breadcrumb_schema(crumbs), wa_message="Hi, I'm interested in your China sourcing services and would like some help with a project.")

# ----------------------------------------------------------------------------
# PRODUCT CATEGORIES
# ----------------------------------------------------------------------------
def categories():
    crumbs = [("Product Categories", "/product-categories/")]
    details = [
        ("automotive", "inspection-emc", "Automotive & Auto Parts", "Reliable sourcing for vehicles, replacement parts, accessories and mobility products, with factory screening and coordinated quality checks for international buyers.", ["EU / WVTA", "GCC"], "Flawless Effect in a vehicle test chamber during an automotive factory inspection",
         {"Products that may be supported": ["Replacement and aftermarket parts", "Accessories, lighting, wheels and tyres", "Garage tools and workshop equipment", "Mobility products such as e-bikes and scooters", "Vehicles and used vehicles, subject to destination rules"],
          "What to send us": ["Part numbers or OEM references", "Photos, drawings or a reference product", "Vehicle make, model and year where relevant", "Quantity, target price and delivery destination"],
          "Typical supplier checks": ["Business licence and export history", "Manufacturer versus trading company", "Quality-system certificates checked against originals", "Production capability and lead time"],
          "Typical quality checks": ["Fit and dimensional checks against a reference part", "Material, finish and marking", "Function tests where applicable", "Packaging, labelling and pre-shipment sampling"],
          "Documentation considerations": ["E-mark or CE where applicable", "Approval questions for vehicles into Europe (WVTA-related)", "GCC conformity for Middle East shipments", "Commercial invoice, packing list and HS codes"]}),
        ("furniture", "cat-furniture", "Home Furniture & Building Materials", "Carefully sourced furniture, fixtures and workplace essentials from dependable Chinese manufacturers, tailored to hospitality, residential and commercial projects.", ["CE", "REACH", "CARB-P2", "GCC / GSO"], "Furniture and building-materials showroom with sofas, dining set and tile samples",
         {"Products that may be supported": ["Sofas, seating, tables and cabinetry", "Doors, tiles, flooring and wall finishes", "Lighting, sanitaryware and fixtures", "Contract furniture for hotels, offices and restaurants"],
          "What to send us": ["Drawings, renders or a purchase list (BOQ)", "Dimensions, materials and finishes", "Quantities and project timeline", "Delivery destination and site constraints"],
          "Typical supplier checks": ["Factory versus showroom-only trader", "Production visit and material sourcing", "Capacity against your project schedule", "Export packing and container-loading experience"],
          "Typical quality checks": ["Pre-production sample approval", "Dimensions, finish and colour match", "Structural and stability checks", "Moisture content for timber, packing for transit, loading supervision"],
          "Documentation considerations": ["CE and REACH for Europe", "CARB-P2 / formaldehyde compliance for the US", "GCC and GSO standards for building materials", "Fire-rating documentation for contract furniture where required"]}),
        ("apparel", "cat-apparel", "Apparel, Jewelry & Fashion Accessories", "Curated sourcing for ready-to-wear apparel, fine jewelry and trend-driven fashion accessories, supporting both mass production and small-batch custom orders.", ["Private label", "Small batch"], "Fashion showroom with apparel, jewelry and accessories on display",
         {"Products that may be supported": ["Ready-to-wear, knitwear and denim", "Bags, belts and small leather goods", "Fashion and fine jewelry", "Sunglasses, hair and seasonal accessories"],
          "What to send us": ["Tech packs or reference photos", "Sizes, size charts and colourways", "Quantity per style and per size", "Labelling, branding and packaging needs"],
          "Typical supplier checks": ["Specialism in your product type", "MOQ alignment for small-batch orders", "In-house versus subcontracted processes", "Social or ethical audit reports where available"],
          "Typical quality checks": ["Pre-production and size-set samples", "Measurement checks against the size spec", "Stitching, finishing and trims", "Plating and stone setting for jewelry, labelling and packing"],
          "Documentation considerations": ["Fibre-content and care labelling", "REACH and nickel-release limits for jewelry in the EU", "Country-of-origin marking", "Commercial documents for customs"]}),
        ("electronics", "cat-electronics", "Electronics", "We connect buyers with screened manufacturers of consumer electronics, smart gadgets and electronic components, with pre-shipment testing and a review of supplier documentation.", ["CE", "RoHS", "FCC", "GCC"], "Consumer electronics including laptop, phones and accessories laid out on a table",
         {"Products that may be supported": ["Consumer electronics and accessories", "Chargers, cables and power banks", "Smart-home and audio products", "Components and OEM / ODM projects"],
          "What to send us": ["Reference product or link and spec sheet", "Target certifications for your market", "Quantity, packaging and branding", "Any firmware, app or connectivity requirements"],
          "Typical supplier checks": ["R&amp;D capability versus assembly only", "Existing CE, FCC and RoHS reports for the model", "Test-lab access and capacity", "Handling of your designs and IP"],
          "Typical quality checks": ["Functional and safety testing on samples", "Burn-in or performance sampling where relevant", "Accessories, manuals and packaging", "Pre-shipment inspection to an agreed AQL"],
          "Documentation considerations": ["CE (LVD, EMC, RED) and RoHS for Europe", "FCC for the United States", "UN38.3 and MSDS for battery products", "GCC conformity and Declaration of Conformity files"]}),
        ("beauty", "cat-beauty", "Beauty & Health Care", "Sourcing for cosmetics, skincare, personal care and wellness goods, prioritising formula safety, ingredient documentation and a review of the regulatory documentation your market may require.", ["GMP", "FDA docs", "EU CPNP", "GSO"], "Skincare and cosmetics products arranged on a marble surface",
         {"Products that may be supported": ["Skincare, hair care and body care", "Colour cosmetics", "Personal-care devices and tools", "Packaging components for private label"],
          "What to send us": ["Product type and reference or formulation brief", "Packaging, branding and fill sizes", "Quantity and destination markets", "Any existing brand or regulatory documents"],
          "Typical supplier checks": ["GMP (ISO 22716) certification checked", "Facility registrations, for example FDA where relevant", "Formulation and private-label capability", "Stability and shelf-life testing capability"],
          "Typical quality checks": ["Batch sample review against approved sample", "Fill weight, seal and leak checks", "Packaging and labelling compliance", "Pre-shipment inspection and documentation check"],
          "Documentation considerations": ["Ingredient lists (INCI) and safety data", "EU CPNP notification and product information file", "GSO requirements for the Middle East", "FDA-related documentation for the US"]}),
        ("other", "cat-other", "Other Sourcing Categories", "Beyond our main verticals, we deliver flexible one-stop sourcing for miscellaneous goods based on your unique project brief, with supplier audits, sample follow-up and quality control.", ["Custom brief", "Supplier audit"], "Retail store shelving with a wide range of household goods",
         {"Products that may be supported": ["Household and kitchen goods", "Pet, sports and outdoor products", "Tools and hardware", "Promotional items and packaging"],
          "What to send us": ["A reference product, link or photos", "Specification or drawing if you have one", "Quantity and target price", "Delivery destination"],
          "Typical supplier checks": ["Business licence and export history", "Manufacturer versus trading company", "Capability for your product and volume", "Sample quality before shortlisting"],
          "Typical quality checks": ["Sample approval before production", "Material, finish and function", "Packaging and labelling", "Pre-shipment inspection with photo report"],
          "Documentation considerations": ["Depends on the product and destination", "We confirm requirements during supplier selection", "Test reports requested from the supplier", "Commercial documents for customs"]}),
    ]
    grid = "".join(f'''<a class="cat-card reveal" data-delay="{i % 3}" href="#{slug}">{img(im, alt, "(min-width: 900px) 33vw, 50vw")}<span class="cat-card__num">0{i+1}</span><div class="cat-card__body"><h3>{t}</h3></div></a>''' for i, (slug, im, t, d, marks, alt, blocks) in enumerate(details))
    det = ""
    for slug, im, t, d, marks, alt, blocks in details:
        chips = "".join(f'<span class="chip chip--accent">{m}</span>' for m in marks)
        cat_param = quote(CATEGORY_FORM_NAMES[slug])
        wa_msg = f"Hi, I'm interested in sourcing {t.lower()} from China and would like some help."
        blocks_html = "".join(f'<div class="cat-block"><h3>{h}</h3><ul>{"".join(f"<li>{x}</li>" for x in items)}</ul></div>' for h, items in blocks.items())
        det += f'''<article class="cat-detail" id="{slug}">
      <div class="reveal cat-detail__side">{frame(im, alt, "4x3", None, "(min-width: 900px) 340px, 100vw")}<div class="chips">{chips}</div>
        <div class="cat-detail__how"><h3>How it works</h3><p>Tell us what you need, we shortlist and verify suppliers, you approve samples and pricing, we manage production, inspect before shipment and arrange delivery. <a href="/#how-it-works">See the six steps</a>.</p></div></div>
      <div class="reveal" data-delay="1"><h2>{t}</h2><p>{d}</p>
      <div class="cat-blocks">{blocks_html}</div>
      <div class="btn-row"><a class="btn btn--primary btn--sm" href="/contact-us/?category={cat_param}">Get a quote</a><a class="btn btn--wa btn--sm" data-wa="{E(wa_msg)}" href="{wa_link(wa_msg)}">{WA_SVG} WhatsApp us</a></div></div>
    </article>'''
    body = page_hero("Product categories we source from China", "Five core verticals with market-specific certification knowledge, plus flexible sourcing for anything else your brief requires.", crumbs, "cat-furniture", "Furniture showroom in China with sofas, dining table and material samples") + f'''
<section class="section"><div class="container"><div class="section-head reveal"><span class="eyebrow">Browse</span><h2 class="h2">Six categories, one process</h2><p class="lead">Whatever the category, the same steps apply: find the right factory, verify it, agree costs, inspect and ship. Our <a href="/guides/">sourcing guides</a> walk through each one, starting with <a href="/guides/china-sourcing-costs/">what goes into the landed price</a>.</p></div><div class="cat-scroller">{grid}</div></div></section>
<section class="section section--grey"><div class="container">{det}</div></section>
''' + quick_inquiry("Sourcing something specific?", "Start a project", "Send us the product and target market. We will tell you which factories fit and what compliance the destination needs.")
    return layout(path="/product-categories/", current="/product-categories/", title="Products We Source from China | Flawless Effect",
                  description="Explore what we source from China: auto parts, furniture and building materials, apparel and jewelry, electronics, beauty products and custom briefs.",
                  body=body, schema=breadcrumb_schema(crumbs), wa_message="Hi, I'm interested in sourcing a product category from China and would like some help.")

# ----------------------------------------------------------------------------
# REGIONAL SUPPORT
# ----------------------------------------------------------------------------
def regional():
    crumbs = [("Regional Support", "/regional-support/")]
    body = page_hero("Regional support for Europe and the Middle East", "Tailored cross-border support: market-specific compliance guidance, certification coordination, import-requirement consulting, time-zone-aligned communication and logistics alignment.", crumbs, "buyer-briefing", "International buyers attending a briefing in Flawless Effect’s Guangzhou lounge", "Buyer briefing, Guangzhou") + f'''
<section class="section"><div class="container">
  <article class="service-row" id="europe">
    <div class="service-row__media reveal">{frame("exhibition-meeting", "Flawless Effect in conversation with a European buyer at a trade exhibition", "4x3", "Exhibition meeting")}</div>
    <div class="reveal" data-delay="1"><span class="eyebrow">Europe</span><h2>Sourcing support for European buyers</h2><p>Support for buyers across Europe is scoped around the product, destination market and available supplier documentation. Markets covered include Germany, France, Italy, Spain and the Netherlands. We help identify likely documentation requirements such as CE, coordinate them with suppliers, carry out product quality control and closely manage production schedules.</p>
    <p class="mt-2 muted">For UK-bound orders, see our guide to <a href="/guides/importing-from-china-to-the-uk/">importing from China to the UK</a>.</p><ul class="check-list"><li>{ic("check")}<span>Coordination of supplier documentation where CE, RoHS or REACH may apply</span></li><li>{ic("check")}<span>Support with approval questions such as WVTA for vehicle imports</span></li><li>{ic("check")}<span>Support with EU CPNP notification questions for cosmetics</span></li><li>{ic("check")}<span>Communication scheduled around European working hours</span></li></ul>
    <div class="btn-row mt-4"><a class="btn btn--primary btn--sm" href="/contact-us/">Start a European project</a><a class="btn btn--outline btn--sm" data-wa="Hi, I'm a buyer based in Europe and I'm interested in sourcing from China." href="{wa_link("Hi, I'm a buyer based in Europe and I'm interested in sourcing from China.")}">{WA_SVG} WhatsApp</a></div></div>
  </article>
  <article class="service-row rev" id="middle-east">
    <div class="service-row__media reveal">{frame("exhibition-middle-east", "Flawless Effect meeting buyers from the Gulf at a trade exhibition in China", "4x3", "Gulf buyers at a trade exhibition")}</div>
    <div class="reveal" data-delay="1"><span class="eyebrow">Middle East</span><h2>Sourcing support for Middle East buyers</h2><p>Support for buyers across the Middle East is scoped around the product, destination market and available supplier documentation. Markets covered include the UAE, Saudi Arabia, Qatar, Kuwait, Bahrain, Oman and Jordan, across both GCC member states and non-GCC markets. We help identify the product documentation likely to be required, coordinate it with suppliers, and manage quality assurance, production planning and order delivery.</p>
    <p class="mt-2 muted">Planning a Gulf shipment? Read our guide to <a href="/guides/importing-from-china-to-uae-saudi-arabia/">importing from China to the UAE and Saudi Arabia</a>.</p><ul class="check-list"><li>{ic("check")}<span>Coordination of supplier documentation where GCC conformity or GSO standards may apply</span></li><li>{ic("check")}<span>Guidance on differing GCC and non-GCC import rules</span></li><li>{ic("check")}<span>Automotive, building-material and cosmetics documentation</span></li><li>{ic("check")}<span>Communication aligned to Gulf working days and hours</span></li></ul>
    <div class="btn-row mt-4"><a class="btn btn--primary btn--sm" href="/contact-us/">Start a Middle East project</a><a class="btn btn--outline btn--sm" data-wa="Hi, I'm a buyer based in the Middle East and I'm interested in sourcing from China." href="{wa_link("Hi, I'm a buyer based in the Middle East and I'm interested in sourcing from China.")}">{WA_SVG} WhatsApp</a></div></div>
  </article>
</div></section>
<section class="section section--grey"><div class="container split">
  <div class="reveal">{frame("lobby-overhead", "Overhead view of buyers arriving at Flawless Effect’s Guangzhou meeting space", "4x3", "Guangzhou meeting space")}</div>
  <div class="reveal" data-delay="1"><span class="eyebrow">China, connected</span><h2 class="h2">Local coordination, global confidence</h2><p class="lead mt-2">Wherever your business is based, the work happens here in Guangzhou: at the factory, at the exhibition and in the inspection room. You get a single English-speaking contact and updates in your working hours.</p>
  <ul class="contact-list"><li><span class="ico">{ic("pin")}</span><div><strong>Office</strong><span class="val">{ADDRESS}</span></div></li><li><span class="ico">{ic("clock")}</span><div><strong>Hours</strong><span class="val">{HOURS}</span></div></li><li><span class="ico">{ic("globe")}</span><div><strong>Other markets</strong><span class="val">Buying from elsewhere? Ask us. Much of what we do applies to any destination.</span></div></li></ul></div>
</div></section>
''' + quick_inquiry("Tell us where you sell", "Start a project", "Share your market and product. We will map the certification path and the right factories for that destination.")
    return layout(path="/regional-support/", current="/regional-support/", title="Europe & Middle East Buyer Support | Flawless Effect",
                  description="Source from China for Europe or the Gulf with market-specific documentation guidance, supplier coordination and communication in your working hours.",
                  body=body, schema=breadcrumb_schema(crumbs), wa_message="Hi, I'm an international buyer and I'd like help sourcing from China for my market.")

# ----------------------------------------------------------------------------
# CERTIFICATIONS
# ----------------------------------------------------------------------------
def fee_faq():
    if not FEE_MODEL: return ""
    return f'<details><summary>How do you charge for certification support?{ic("plus")}</summary><div class="acc-body">{E(FEE_MODEL)}</div></details>'

def certifications():
    crumbs = [("Certifications", "/certifications/")]
    cards = [
        ("Automotive", "We provide documentation support for vehicles, used cars and auto parts shipping to Europe and the Middle East. Where relevant to the specific vehicle, product and destination market, we can help coordinate supplier documentation and questions relating to applicable approval processes, such as WVTA for Europe and GCC conformity for the Middle East.", [("WVTA", "Europe"), ("GCC", "Middle East")]),
        ("Beauty & Personal Care", "We help identify beauty and personal-care suppliers whose products carry documentation that may be relevant, such as FDA-related documentation, EU CPNP notification or Middle East GSO compliance, and we review ingredient records and regulatory files for consistency to support import into Europe, the US and Middle East markets.", [("FDA", "US documentation"), ("CPNP", "EU"), ("GSO", "Middle East"), ("GMP", "Manufacturing")]),
        ("Electronics", "We help identify electronics suppliers whose products carry documentation that may be relevant, such as CE and RoHS for European markets, FCC documentation for the United States or GCC compliance for Middle East regions, and we review technical files and compliance records for consistency to support import into each destination.", [("CE", "Europe"), ("RoHS", "Europe"), ("FCC", "US"), ("GCC", "Middle East")]),
        ("Furniture & Building Materials", "We help identify furniture and building-material suppliers with relevant compliance documents. Requirements may include CE and REACH for Europe, CARB-P2 formaldehyde compliance and safety documentation for the US, and GCC or GSO standards for the Middle East. We review test records and material files to support import.", [("CE", "Europe"), ("REACH", "Europe"), ("CARB-P2", "US"), ("GCC / GSO", "Middle East")]),
    ]
    cards_html = "".join(f'''<article class="cert-card reveal" data-delay="{i % 2}"><h3>{t}</h3><p>{d}</p><div class="cert-card__marks">{"".join(f'<span class="mark">{m}<small>{s}</small></span>' for m, s in marks)}</div></article>''' for i, (t, d, marks) in enumerate(cards))
    body = page_hero("Certification and compliance support", "Every destination market has documentation requirements. We help identify them, coordinate supplier documentation and organise it before goods leave China, to reduce the risk of delays at the border.", crumbs, "factory-credentials-wall", "Wall of qualification plaques and certificates photographed at a factory during a visit", "Qualification wall, factory visit") + f'''
<section class="section"><div class="container">
  <div class="notice reveal">{ic("info")}<div><strong>How this works.</strong> {BRAND} is a sourcing agent, not a certification body. Certifications and test reports are held by the manufacturers we source from, or issued by accredited laboratories and notified bodies. Our role is to help identify suppliers with documentation relevant to your market, review that it is consistent and current, and coordinate any additional testing or registration your destination may require. Supplier certificates and registrations are not accreditations held by {BRAND}. Requirements vary by product and destination and should be confirmed with the relevant authority or a qualified adviser before ordering.</div></div>
  <div class="section-head reveal mt-5"><span class="eyebrow">By category</span><h2 class="h2">Compliance support across our core categories</h2><p class="lead">New to this? Start with our <a href="/guides/product-compliance-guide-china-imports/">product compliance guide</a>, then the market guides for the <a href="/guides/importing-from-china-to-the-uk/">UK</a> and the <a href="/guides/importing-from-china-to-uae-saudi-arabia/">UAE and Saudi Arabia</a>.</p></div>
  <div class="grid grid-2">{cards_html}</div>
</div></section>
<section class="section section--grey"><div class="container split">
  <div class="reveal">
    <span class="eyebrow">What we check</span>
    <h2 class="h2">Documentation we review before you buy</h2>
    <ul class="check-list mt-3">
      <li>{ic("check")}<span><strong>Test reports</strong> — issued by a recognised laboratory, matching the exact product and model you are buying, and still within validity.</span></li>
      <li>{ic("check")}<span><strong>Technical files and declarations</strong> — Declaration of Conformity, technical construction files and material data where required.</span></li>
      <li>{ic("check")}<span><strong>Facility registrations</strong> — for example a manufacturer’s FDA cosmetic facility registration or GMP documentation.</span></li>
      <li>{ic("check")}<span><strong>Labelling and marking</strong> — marking, ingredient labelling and language requirements, as specified by you, checked at pre-shipment inspection.</span></li>
    </ul>
    <div class="btn-row mt-4"><a class="btn btn--primary" href="/contact-us/">Ask about your market {ic("arrow")}</a><a class="btn btn--outline" data-wa="Hi, I have a question about certification requirements for importing from China." href="{wa_link('Hi, I have a question about certification requirements for importing from China.')}">{WA_SVG} WhatsApp</a></div>
  </div>
  <div class="reveal" data-delay="1">{frame("inspection-emc", "Flawless Effect inside a vehicle test chamber during a factory inspection", "4x5", "Vehicle test chamber, factory inspection", "(min-width: 960px) 40vw, 100vw")}</div>
</div></section>
<section class="section"><div class="container container--narrow">
  <div class="section-head reveal"><span class="eyebrow">Common questions</span><h2 class="h2">Certification questions buyers ask us</h2></div>
  <div class="accordion reveal">
    <details><summary>Does {BRAND} hold these certifications itself?{ic("plus")}</summary><div class="acc-body">No. Certifications such as CE, FCC, GCC or FDA registration apply to products and manufacturers, not to sourcing agents. We help identify suppliers whose products already carry relevant documentation, review it for consistency, and coordinate additional testing or registration where your market may require it.</div></details>
    <details><summary>Can you arrange new testing if a supplier has no report?{ic("plus")}</summary><div class="acc-body">Usually, yes. We coordinate sample testing with laboratories in China for the standards your destination requires, and build the cost and lead time into the project plan before production.</div></details>
    <details><summary>Which markets do you know best?{ic("plus")}</summary><div class="acc-body">The European Union and GCC states are the markets we support most, along with US documentation for electronics, cosmetics and furniture. See our <a href="/regional-support/">Regional Support</a> page for details.</div></details>
    {fee_faq()}
    <details><summary>Where does compliance fit in the sourcing timeline?{ic("plus")}</summary><div class="acc-body">At the start. We help identify what your market is likely to need during supplier selection so that testing, labelling and registration can happen alongside sampling, not after production when changes are expensive.</div></details>
  </div>
</div></section>
''' + cta_band("Need documentation support for your market?", "Tell us the product and destination. We will help identify the likely documentation requirements and shortlist suppliers with relevant records.", primary=("Ask about your market", "/contact-us/"))
    return layout(path="/certifications/", current="/certifications/", title="Certification & Compliance Support | Flawless Effect",
                  description="Help identifying and coordinating supplier documentation such as CE, RoHS, REACH, FCC, CARB-P2, GCC, GSO or FDA-related records when importing from China.",
                  body=body, schema=breadcrumb_schema(crumbs), wa_message="Hi, I have a question about certification and compliance when importing from China.")

# ----------------------------------------------------------------------------
# CONTACT
# ----------------------------------------------------------------------------
def contact():
    crumbs = [("Contact", "/contact-us/")]
    office = E(ADDRESS)
    linkedin = f'<li><span class="ico">{ic("globe")}</span><div><strong>LinkedIn</strong><a href="{E(LINKEDIN_URL)}" target="_blank" rel="noopener">Company page</a></div></li>' if LINKEDIN_URL else ""
    body = f'''
<section class="page-hero page-hero--compact"><div class="container page-hero__inner">
  <div>{breadcrumb(crumbs)}<h1>Start your sourcing project</h1><p class="lead">Tell us what you want to source and where you sell. Our Guangzhou team reviews every message personally and replies on WhatsApp or by email.</p>
  <div class="btn-row"><a class="btn btn--wa-solid btn--lg" data-wa href="{wa_link()}">{WA_SVG} WhatsApp us</a><button class="btn btn--outline btn--lg" data-wechat type="button">{WC_SVG} WeChat</button></div></div>
  {frame("meeting-skyline", "Flawless Effect meeting and dining space in Guangzhou with the city skyline behind", "3x4", "Our meeting space, Guangzhou", "(min-width: 960px) 40vw, 100vw", lazy=False)}
</div></section>
<section class="section"><div class="container quick quick--contact">
  <div class="contact-aside reveal">
    <span class="eyebrow">Contact our China team</span>
    <h2 class="h2">Two ways to start</h2>
    <p class="lead mt-2"><strong class="ink">Option A.</strong> Complete the form and we prepare a WhatsApp draft for you to review and send. <strong class="ink">Option B.</strong> Email us at <a href="mailto:{E(EMAIL)}">{E(EMAIL)}</a> and your email app opens with a new message.</p>
    <ul class="contact-list">
      <li><span class="ico">{WA_SVG}</span><div><strong>WhatsApp</strong><a data-wa href="{wa_link()}">{PHONE_DISPLAY}</a></div></li>
      <li><span class="ico">{ic("phone")}</span><div><strong>Phone</strong><a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a></div></li>
      <li><span class="ico">{ic("mail")}</span><div><strong>Email</strong><a href="mailto:{E(EMAIL)}">{E(EMAIL)}</a></div></li>
      <li><span class="ico">{WC_SVG}</span><div><strong>WeChat</strong><button class="link-arrow" data-wechat type="button">WeChat ID: {E(WECHAT_ID)} {ic("arrow")}</button><span class="val-note">Watch our factory visits on WeChat Channels: search {E(WECHAT_CHANNEL)}.</span></div></li>
      <li><span class="ico">{ic("pin")}</span><div><strong>Office</strong><span class="val">{office}</span><br><a class="link-arrow link-arrow--sm" href="{E(MAPS_URL)}" target="_blank" rel="noopener">Open in Google Maps {ic("arrow")}</a></div></li>
      <li><span class="ico">{ic("clock")}</span><div><strong>Hours</strong><span class="val">{E(HOURS_LONG)}</span></div></li>
      <li><span class="ico">{IG_SVG}</span><div><strong>Instagram</strong><a href="{E(INSTAGRAM)}" target="_blank" rel="noopener">@flawlesseffect.sourcingagent</a></div></li>{linkedin}
    </ul>
    <div class="mt-4 hide-mobile">{frame("buyer-briefing", "Buyers attending a briefing in the lounge at Flawless Effect’s Guangzhou meeting space", "3x2", "Buyer briefing, Guangzhou", "(min-width: 960px) 40vw, 100vw")}</div>
  </div>
  <div class="form-card reveal" data-delay="1">
    {inquiry_form("inquiry-form")}
  </div>
</div></section>
<section class="section section--sm section--grey"><div class="container">
  <div class="section-head reveal"><span class="eyebrow">What happens next</span><h2 class="h2">After you get in touch</h2></div>
  <ol class="grid grid-3">
    <li class="service-card reveal"><span class="index-row__num">01</span><h3>We review your brief</h3><p>A real person reads it and, if anything is unclear, asks a couple of questions on WhatsApp or email.</p></li>
    <li class="service-card reveal" data-delay="1"><span class="index-row__num">02</span><h3>Feasibility and pricing</h3><p>You get an honest view on whether the product suits China sourcing, indicative pricing and MOQ, and notes on the documentation your market may require.</p></li>
    <li class="service-card reveal" data-delay="2"><span class="index-row__num">03</span><h3>Suppliers and samples</h3><p>If you want to proceed, we shortlist screened factories and arrange samples. You decide every step.</p></li>
  </ol>
</div></section>'''
    schema = [{"@context": "https://schema.org", "@type": "ContactPage", "url": SITE_URL + "/contact-us/", "name": "Contact Flawless Effect", "mainEntity": {"@id": SITE_URL + "/#org"}}, breadcrumb_schema(crumbs)]
    return layout(path="/contact-us/", current="/contact-us/", title="Get a China Sourcing Quote | Flawless Effect",
                  description="Tell our Guangzhou team about your product, quantity and target market on WhatsApp, by email or on WeChat and get a feasibility view, pricing and next steps.",
                  body=body, schema=schema)

# ----------------------------------------------------------------------------
# PRIVACY
# ----------------------------------------------------------------------------
def privacy():
    crumbs = [("Privacy Policy", "/privacy-policy/")]
    ext = 'target="_blank" rel="noopener noreferrer"'
    body = f'''
<section class="page-hero page-hero--text"><div class="container">{breadcrumb(crumbs)}<h1>Privacy Policy</h1><p class="lead">How {E(BRAND)} handles the information you share when you contact us, and where it may be processed.</p></div></section>
<section class="section"><div class="container prose">
  <p><strong>Effective date: {E(PRIVACY_EFFECTIVE_DATE)}.</strong></p>
  <h2>1. Who we are</h2>
  <p>{E(BRAND)} operates through <strong>{E(LEGAL_ENTITY_US)}</strong> in the United States and <strong>{E(LEGAL_ENTITY_CN)}</strong> in China (Unified Social Credit Code {E(REGISTRATION_NO_CN)}; registered address: {E(REGISTERED_ADDRESS_CN)}). Our operational team is based in China and works from our public office at {E(ADDRESS)}. These entities are responsible for the personal information described in this policy.</p>
  <p>Email: <a href="mailto:{E(EMAIL)}">{E(EMAIL)}</a>. Phone and WhatsApp: <a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a>.</p>
  <h2>2. Information you share with us</h2>
  <ul><li><strong>Messages you send</strong> on WhatsApp, by email or on WeChat, including your account name, number or ID and anything you write, such as your name, company, country, product category, service required, approximate budget and requirements.</li><li><strong>Technical information</strong> generated when you visit this site, such as pages requested, browser type and approximate location, recorded in our hosting provider’s access logs for security and performance. This website sets no tracking cookies and uses no analytics service.</li></ul>
  <h2>3. Contacting us through WhatsApp or email</h2>
  <p>This website does not submit or store the information entered in the WhatsApp enquiry form on a {E(BRAND)} web server. When you select ‘Continue on WhatsApp’, the information you entered is used by your browser to create a pre-filled WhatsApp message. WhatsApp will open with that draft. The message is not sent to {E(BRAND)} until you review it and press Send.</p>
  <p>If you click our email address, your device will open its configured email application. The website itself does not send or store the email.</p>
  <h2>4. WhatsApp and email providers</h2>
  <p>If you continue to WhatsApp, WhatsApp and Meta will process information required to open the conversation and deliver any message you choose to send, in accordance with <a href="{E(WHATSAPP_PRIVACY_URL)}" {ext}>WhatsApp’s privacy policy</a>. WhatsApp states that it operates global infrastructure and may transfer, store or process information in the United States and other countries.</p>
  <p>If you contact us by email, your message will be processed by your email provider and by our email provider, {E(EMAIL_PROVIDER)}, under their respective privacy terms.</p>
  <h2>5. Why we use your information and the lawful basis</h2>
  <ul><li>To respond to your enquiry and prepare sourcing proposals — <em>taking steps at your request before entering into a contract</em>.</li><li>To deliver sourcing services once you become a client — <em>performance of a contract</em>.</li><li>To keep accounting and legal records — <em>legal obligation</em>.</li><li>To keep the website secure — <em>legitimate interests</em>.</li></ul>
  <p>We do not sell personal data and we do not use it for unrelated marketing. For project requirements only, we may share product details with prospective manufacturers, testing laboratories and freight forwarders, without your contact details unless you agree otherwise.</p>
  <h2>6. International processing</h2>
  <p>{E(BRAND)} operates through {E(LEGAL_ENTITY_US)} in the United States and {E(LEGAL_ENTITY_CN)} in China. Our operational team is based in China.</p>
  <p>Messages you choose to send through WhatsApp or email may be received, accessed and handled by our operational team in China. Your information may therefore be processed outside the United Kingdom, European Economic Area or the country in which you live. The data-protection laws in those countries may differ from those in your country.</p>
  <p>Third-party communication providers may also process information in countries where they or their service providers operate. Their processing is governed by their own privacy notices and applicable contractual and legal safeguards.</p>
  <p>We use enquiry information to respond to your request and manage a potential or existing business relationship. Our copy of website enquiry correspondence is retained for 24 months from receipt and is then deleted. Communication providers may apply their own retention periods.</p>
  <p>Please do not include payment-card details, identification documents, special-category or sensitive personal information, or confidential product documents in the WhatsApp form. Contact us first if a secure document-transfer method is required.</p>
  <h2>7. Retention</h2>
  <p>Website enquiry correspondence: {E(RETENTION_PERIOD)}, then deleted, as described in section 6. Records relating to a client engagement are kept for the duration of the engagement and any period required by accounting or legal obligations.</p>
  <h2>8. Hosting and technical information</h2>
  <p>This is a static website served through a content delivery network. It has no enquiry database and stores nothing you type into the form. Our hosting provider records technical access logs, described in section 2, for security and performance.</p>
  <h2>9. Your rights</h2>
  <p>Depending on where you live, you may have the right to access, correct or delete the personal information we hold about you, to restrict or object to its processing, or to receive a copy in a portable format. Contact us at <a href="mailto:{E(EMAIL)}">{E(EMAIL)}</a> and we will respond promptly.</p>
  <h2>10. Complaints</h2>
  <p>If you are unhappy with how we handle your information, please contact us first. UK visitors may complain to the <a href="https://ico.org.uk/make-a-complaint/" {ext}>Information Commissioner’s Office</a>. EU visitors may complain to the <a href="https://www.edpb.europa.eu/about-edpb/about-edpb/members_en" {ext}>supervisory authority in their member state</a>. Visitors elsewhere may contact their local data-protection authority.</p>
  <h2>11. Privacy contact</h2>
  <p>For questions about this Privacy Policy or the handling of your information, contact <a href="mailto:{E(EMAIL)}">{E(EMAIL)}</a>.</p>
  <h2>12. Changes to this policy</h2>
  <p>Effective date: {E(PRIVACY_EFFECTIVE_DATE)}. Last updated: {BUILD_DATE}. We will update this page if our contact methods or providers change.</p>
</div></section>'''
    return layout(path="/privacy-policy/", current="/privacy-policy/", title="Privacy Policy | Flawless Effect",
                  description="How Flawless Effect handles the information you share when contacting us on WhatsApp or by email, including international processing and retention.",
                  body=body, schema=breadcrumb_schema(crumbs))

# ----------------------------------------------------------------------------
# Write
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# GUIDES (phase two)
# ----------------------------------------------------------------------------
sys.path.insert(0, os.path.join(ROOT, "_build"))
from guides import GUIDES
GUIDE_BY_SLUG = {g["slug"]: g for g in GUIDES}
GUIDES_PUBLISHED = "2026-09-11"   # first publication date of the guides section (ISO). Per-guide "reviewed" dates are set in guides.py when an article is materially revised.
def _check_dates(published, reviewed):
    today = datetime.date.today().isoformat()
    if reviewed < published: raise SystemExit(f"build error: reviewed date {reviewed} is before published {published}")
    if published > today or reviewed > today: raise SystemExit(f"build error: future date ({published}, {reviewed}) — today is {today}")

def guide_widths(name):
    ws = []
    for f in os.listdir(os.path.join(ROOT, "assets/img/guides")):
        m = re.match(re.escape(name) + r"-(\d+)\.webp$", f)
        if m: ws.append(int(m.group(1)))
    return sorted(ws)

FOCAL_CLASSES = {20, 30, 35, 40, 50, 55, 60}  # vertical focal points with a matching .focal-N rule in style.css

def guide_img(name, alt, sizes, lazy=True, fetchpriority=None, pos=None):
    ws = guide_widths(name)
    if not ws: raise SystemExit(f"missing guide image: {name}")
    w, h = image_size(os.path.join(ROOT, f"assets/img/guides/{name}-{ws[-1]}.webp"))
    srcset = ", ".join(f"{asset(f'assets/img/guides/{name}-{w_}.webp')} {w_}w" for w_ in ws)
    attrs = [f'src="{asset(f"assets/img/guides/{name}-{ws[-1]}.webp")}"', f'srcset="{srcset}"', f'sizes="{sizes}"', f'alt="{E(alt)}"', f'width="{w}"', f'height="{h}"', 'loading="lazy" decoding="async"' if lazy else 'decoding="async"']
    if pos is not None:
        if pos not in FOCAL_CLASSES: raise SystemExit(f"no .focal-{pos} rule for guide image {name}")
        attrs.append(f'class="focal-{pos}"')
    if fetchpriority: attrs.append(f'fetchpriority="{fetchpriority}"')
    return "<img " + " ".join(attrs) + ">"

def reading_time(html_):
    words = len(re.sub(r"<[^>]+>", " ", html_).split())
    return max(3, round(words / 220))

def guide_card(g, i=0):
    return f'''<a class="guide-card reveal" data-delay="{i % 3}" href="/guides/{g["slug"]}/"><div class="img-frame img-frame--16x9">{guide_img(g["hero"], g["hero_alt"], "(min-width: 900px) 33vw, (min-width: 720px) 50vw, 100vw", pos=g.get("hero_pos"))}</div><div class="guide-card__body"><h3>{E(g["title"])}</h3><p>{E(g["summary"])}</p><span class="link-arrow">Read the guide {ic("arrow")}</span></div></a>'''

def guides_index():
    crumbs = [("Guides", "/guides/")]
    cards = "".join(guide_card(g, i) for i, g in enumerate(GUIDES))
    body = f'''
<section class="page-hero page-hero--text"><div class="container">{breadcrumb(crumbs)}<h1>China Sourcing Guides for International Buyers</h1><p class="lead">Practical, plain-English guides to buying from China, written from our work with international buyers in Guangzhou. No sales pitch, no invented numbers: what to check, what to ask, and where to confirm the rules for your market.</p></div></section>
<section class="section section--guides"><div class="container"><div class="section-head reveal"><span class="eyebrow">Eight guides</span><h2 class="h2">Start with the question you have</h2></div><div class="guide-grid">{cards}</div></div></section>
''' + cta_band("Have a product in mind?", "Send us the product and your target market. We will tell you honestly whether it suits sourcing from China and what the next step is.")
    schema = [{"@context": "https://schema.org", "@type": "CollectionPage", "url": SITE_URL + "/guides/", "name": "Sourcing guides", "description": "Practical guides to buying from China.", "isPartOf": {"@id": SITE_URL + "/#website"},
               "hasPart": [{"@type": "Article", "headline": g["title"], "url": SITE_URL + f"/guides/{g['slug']}/"} for g in GUIDES]}, breadcrumb_schema(crumbs)]
    return layout(path="/guides/", current="/guides/", title="China Sourcing Guides | Flawless Effect",
                  description="Practical guides to buying from China: reliable factories, supplier verification, inspection, landed costs, UK and Gulf imports, compliance and the Canton Fair.",
                  body=body, schema=schema, og_image="/assets/img/guides/og/how-to-find-reliable-chinese-factories.jpg")

def _slugify(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")

def guide_page(g):
    crumbs = [("Guides", "/guides/"), (g["short"], f"/guides/{g['slug']}/")]
    mins = reading_time(g["sections"])
    # Anchor ids on H2s + table of contents
    heads = re.findall(r"<h2>(.*?)</h2>", g["sections"])
    body_html = g["sections"]
    toc_items = []
    for h in heads:
        hid = _slugify(re.sub(r"<[^>]+>", "", h))
        body_html = body_html.replace(f"<h2>{h}</h2>", f'<h2 id="{hid}">{h}</h2>', 1)
        label = re.sub(r"^\s*\d+[.)]\s*", "", re.sub(r"<[^>]+>", "", h))
        toc_items.append(f'<li><a href="#{hid}">{label}</a></li>')
    toc = f'<nav class="guide-toc" aria-labelledby="toc-title"><p class="guide-toc__title" id="toc-title">In this guide</p><ol>{"".join(toc_items)}<li><a href="#faq">Frequently asked questions</a></li><li><a href="#sources">Official sources and further reading</a></li></ol></nav>'
    takeaways = f'<aside class="guide-takeaways" aria-labelledby="tk-title"><p class="guide-takeaways__title" id="tk-title">Key takeaways</p><ul>{"".join(f"<li>{t}</li>" for t in g["takeaways"])}</ul></aside>'
    faq_html = "".join(f'<details><summary>{E(q)}{ic("plus")}</summary><div class="acc-body">{E(a)}</div></details>' for q, a in g["faq"])
    sources = "".join(f'<li><a href="{E(u)}" rel="noopener" target="_blank">{E(t)}</a>{(" — " + E(n)) if n else ""}</li>' for t, u, n in g["sources"])
    related = "".join(guide_card(GUIDE_BY_SLUG[s], i) for i, s in enumerate(g["related"]) if s in GUIDE_BY_SLUG)
    hero_sizes = "(min-width: 1280px) 1180px, 100vw"
    caption = f'<figcaption class="guide-hero__cap">{E(g["hero_caption"])}</figcaption>' if g.get("hero_caption") else ""
    reviewed = g.get("reviewed", GUIDES_PUBLISHED)
    _check_dates(GUIDES_PUBLISHED, reviewed)
    byline = f"By {E(AUTHOR['name'])}" + (f", {E(AUTHOR['role'])}" if AUTHOR.get("role") else "") + f", {E(BRAND)}" if AUTHOR.get("name") else f"By {E(BRAND)}, Guangzhou"
    profile_link = ('<p><a href="' + E(AUTHOR["url"]) + '">Profile</a></p>') if AUTHOR.get("url") else ""
    author_box = (f'<aside class="guide-author"><p class="guide-author__title">About the author</p><p><strong>{E(AUTHOR["name"])}</strong>{(" — " + E(AUTHOR["role"])) if AUTHOR.get("role") else ""}</p>{("<p>" + E(AUTHOR["experience"]) + "</p>") if AUTHOR.get("experience") else ""}{("<p>" + E(AUTHOR["bio"]) + "</p>") if AUTHOR.get("bio") else ""}{profile_link}{("<p>Reviewed by <strong>" + E(REVIEWER["name"]) + "</strong>" + ((", " + E(REVIEWER["role"])) if REVIEWER.get("role") else "") + "</p>") if REVIEWER.get("name") else ""}</aside>' if AUTHOR.get("name") else "")
    body = f'''
<article class="guide">
  <header class="guide__head"><div class="container container--narrow">{breadcrumb(crumbs)}<span class="eyebrow">Sourcing guide · {mins} min read</span><h1>{E(g["title"])}</h1><p class="lead">{E(g["description"])}</p><p class="guide__meta">{byline} · Published <time datetime="{GUIDES_PUBLISHED}">{_nice_date(GUIDES_PUBLISHED)}</time> · Last reviewed <time datetime="{reviewed}">{_nice_date(reviewed)}</time></p></div></header>
  <figure class="guide-hero"><div class="container"><div class="img-frame guide-hero__frame">{guide_img(g["hero"], g["hero_alt"], hero_sizes, lazy=False, fetchpriority="high", pos=g.get("hero_pos"))}</div>{caption}</div></figure>
  <div class="container container--narrow guide__body prose">
    {takeaways}
    {toc}
    <p class="guide__note"><strong>About this guide.</strong> This is general information based on our work as a sourcing agent in Guangzhou, not legal, tax or customs advice. Requirements depend on the product and destination and change over time; confirm them with the relevant authority, your customs broker or a qualified adviser before ordering.</p>
    {body_html}
    <h2 id="faq">Frequently asked questions</h2><div class="accordion">{faq_html}</div>
    <h2 id="sources">Official sources and further reading</h2><ul class="guide-sources">{sources}</ul>
    {author_box}
    <div class="guide__cta"><h2 class="h3">Talk to us about your product</h2><p>Tell us what you want to source and where you sell. We reply by email or WhatsApp with an honest view on feasibility and next steps.</p><div class="btn-row"><a class="btn btn--primary" href="/contact-us/">Get a quote</a><a class="btn btn--wa" data-wa="{E('Hi, I read your guide “' + g['title'] + '” and would like some help sourcing from China.')}" href="{wa_link('Hi, I read your guide “' + g['title'] + '” and would like some help sourcing from China.')}">{WA_SVG} WhatsApp us</a></div></div>
  </div>
  <section class="section section--grey"><div class="container"><div class="section-head reveal"><span class="eyebrow">Related guides</span><h2 class="h2">Keep reading</h2></div><div class="guide-grid">{related}</div></div></section>
</article>'''
    article = {"@context": "https://schema.org", "@type": "Article", "@id": SITE_URL + f"/guides/{g['slug']}/#article", "headline": g["title"], "description": g["description"], "url": SITE_URL + f"/guides/{g['slug']}/", "datePublished": GUIDES_PUBLISHED, "dateModified": reviewed, "inLanguage": "en",
               "image": SITE_URL + asset(f"assets/img/guides/og/{g['slug']}.jpg"), "author": ({"@type": "Person", "name": AUTHOR["name"], **({"jobTitle": AUTHOR["role"]} if AUTHOR.get("role") else {}), **({"url": AUTHOR["url"]} if AUTHOR.get("url") else {}), "worksFor": {"@id": SITE_URL + "/#org"}} if AUTHOR.get("name") else {"@type": "Organization", "name": BRAND, "url": SITE_URL + "/"}), **({"reviewedBy": {"@type": "Person", "name": REVIEWER["name"], **({"jobTitle": REVIEWER["role"]} if REVIEWER.get("role") else {}), **({"url": REVIEWER["url"]} if REVIEWER.get("url") else {})}} if REVIEWER.get("name") else {}), "publisher": {"@id": SITE_URL + "/#org"}, "isPartOf": {"@id": SITE_URL + "/#website"}, "mainEntityOfPage": SITE_URL + f"/guides/{g['slug']}/"}
    title = g.get("seo_title") or g["title"]
    gws = guide_widths(g["hero"])
    srcset = ", ".join(asset("assets/img/guides/%s-%d.webp" % (g["hero"], w_)) + " %dw" % w_ for w_ in gws)
    pre = f'<link rel="preload" as="image" imagesrcset="{srcset}" imagesizes="{hero_sizes}" fetchpriority="high">\n'
    return layout(path=f"/guides/{g['slug']}/", current="/guides/", title=title, description=g["description"], body=body, schema=[article, breadcrumb_schema(crumbs)], og_image=f"/assets/img/guides/og/{g['slug']}.jpg", preload_html=pre,
                  wa_message="Hi, I've been reading your sourcing guides and would like some help sourcing from China.")

def _nice_date(iso):
    y, m, d = iso.split("-"); months = ["January","February","March","April","May","June","July","August","September","October","November","December"]
    return f"{int(d)} {months[int(m)-1]} {y}"

def not_found():
    body = f'''
<section class="section"><div class="container container--narrow text-center"><span class="eyebrow">404</span><h1 class="h1">Page not found</h1><p class="lead mt-3">That page has moved or never existed. The main sections are below, or message us on WhatsApp and we will point you the right way.</p><h2 class="h3 mt-4">Where to next?</h2><div class="btn-row btn-row--center mt-3"><a class="btn btn--primary" href="/">Home</a><a class="btn btn--outline" href="/sourcing-services/">Services</a><a class="btn btn--outline" href="/product-categories/">Product categories</a><a class="btn btn--outline" href="/contact-us/">Get a quote</a><a class="btn btn--wa" data-wa href="{wa_link()}">{WA_SVG} WhatsApp us</a></div></div></section>'''
    return layout(path="/404.html", current="", title="Page Not Found | Flawless Effect", description="The page you requested could not be found. Browse our China sourcing services, product categories and contact options, or message us on WhatsApp.", body=body, noindex=True)

PAGES = {"index.html": home, "404.html": not_found, "about-us/index.html": about, "sourcing-services/index.html": services, "product-categories/index.html": categories,
         "regional-support/index.html": regional, "certifications/index.html": certifications, "contact-us/index.html": contact, "privacy-policy/index.html": privacy, "guides/index.html": guides_index}
for _g in GUIDES: PAGES[f"guides/{_g['slug']}/index.html"] = (lambda g: (lambda: guide_page(g)))(_g)
SITEMAP_URLS = ["/", "/about-us/", "/sourcing-services/", "/product-categories/", "/regional-support/", "/certifications/", "/contact-us/", "/privacy-policy/", "/guides/"] + [f"/guides/{g['slug']}/" for g in GUIDES]

def write(rel, content, binary=False):
    p = os.path.join(DIST, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb" if binary else "w", **({} if binary else {"encoding": "utf-8"})) as f: f.write(content)

def csp():
    # Static site only. WhatsApp is opened by navigation (wa.me links / window.open), which CSP does not restrict, so no
    # external host is needed. connect-src stays 'self' because nothing is fetched; form-action 'self' because no form posts anywhere.
    return ("default-src 'self'; script-src 'self' '" + NOJS_HASH + "'; style-src 'self'; img-src 'self' data:; font-src 'self'; media-src 'self'; "
            "connect-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests")

def headers_file():
    return f"""/*
  Content-Security-Policy: {csp()}
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Cross-Origin-Opener-Policy: same-origin

/assets/*
  Cache-Control: public, max-age=31536000, immutable

/assets/fonts/*
  Cache-Control: public, max-age=31536000, immutable

/assets/css/*
  Cache-Control: public, max-age=86400, stale-while-revalidate=604800

/assets/js/*
  Cache-Control: public, max-age=86400, stale-while-revalidate=604800

/favicon.ico
  Cache-Control: public, max-age=604800
/favicon.svg
  Cache-Control: public, max-age=604800
/apple-touch-icon.png
  Cache-Control: public, max-age=604800
/site.webmanifest
  Cache-Control: public, max-age=86400
"""

REDIRECTS = """/about/            /about-us/            301
/contact/          /contact-us/          301
/services/         /sourcing-services/   301
/home/             /                     301
/feed/             /                     301
/comments/feed/    /                     301
/wp-content/*      /                     301
/wp-json/*         /                     301
/xmlrpc.php        /                     301
/index.html        /                     301
"""

def check_launch_gate():
    missing = [k for k, v in LAUNCH_REQUIRED.items() if not str(v).strip()]
    if SITE_MODE == "production" and missing and not AUDIT_ONLY:
        sys.exit("PRODUCTION BUILD BLOCKED — these values are empty in _build/build.py: " + ", ".join(missing) + ". See CLIENT_REQUIRED.md. Build as preview instead (no --production).")
    return missing

def build():
    check_launch_gate()
    if os.path.isdir(DIST): shutil.rmtree(DIST)
    os.makedirs(DIST)
    pages = {rel: fn() for rel, fn in PAGES.items()}   # render first so ASSET_MAP is complete
    for rel, html_ in pages.items(): write(rel, html_)
    # hashed assets referenced by pages
    for src, pub in ASSET_MAP.items():
        os.makedirs(os.path.dirname(os.path.join(DIST, pub.lstrip("/"))), exist_ok=True)
        shutil.copyfile(os.path.join(ROOT, src), os.path.join(DIST, pub.lstrip("/")))
    # unhashed, stable assets referenced by CSS/JS
    for rel in ["assets/css/style.css", "assets/js/main.js"]:
        write(rel, open(os.path.join(ROOT, rel), encoding="utf-8").read())
    for f in os.listdir(os.path.join(ROOT, "assets/fonts")):
        if f.endswith(".woff2"): write(f"assets/fonts/{f}", open(os.path.join(ROOT, "assets/fonts", f), "rb").read(), binary=True)
    # root icons (approved brand package)
    for f, dest in [("favicon.ico", "favicon.ico"), ("favicon.svg", "favicon.svg"), ("favicon-16.png", "favicon-16.png"), ("favicon-32.png", "favicon-32.png"), ("apple-touch-icon.png", "apple-touch-icon.png"), ("icon-192.png", "icon-192.png"), ("icon-512.png", "icon-512.png")]:
        write(dest, open(os.path.join(ROOT, "assets/img/brand", f), "rb").read(), binary=True)
    write("site.webmanifest", json.dumps({"name": BRAND, "short_name": "Flawless Effect", "description": "China sourcing agent in Guangzhou.", "start_url": "/", "display": "browser", "background_color": "#ffffff", "theme_color": "#12161f",
                                          "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}]}, indent=2))
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{SITE_URL}{u}</loc></url>\n" for u in SITEMAP_URLS) + "</urlset>\n")
    write("robots.txt", "User-agent: *\nDisallow: /\n" if PREVIEW else f"User-agent: *\nAllow: /\nDisallow: /404.html\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    write("_redirects", REDIRECTS)
    write("_headers", headers_file())
    print(f"built {len(pages)} pages -> dist/ ({SITE_MODE}); {len(ASSET_MAP)} hashed assets")
    missing = [k for k, v in LAUNCH_REQUIRED.items() if not str(v).strip()]
    if missing: print("preview only — production blocked until set:", ", ".join(missing))

if __name__ == "__main__":
    build()
