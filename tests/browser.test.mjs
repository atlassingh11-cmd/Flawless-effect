// Browser QA for the built site. Run after `npm run build`:  node tests/browser.test.mjs
// Serves dist/ in-process with the generated _headers applied (no backend exists), then checks
// accessibility (axe-core), responsive layout, navigation behaviour, the WhatsApp composer, no-JS fallbacks, console and CSP cleanliness.
// Set PUPPETEER_EXECUTABLE_PATH to use an installed Chrome instead of puppeteer's download.
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DIST = path.join(ROOT, "dist");
const PORT = 8790, BASE = `http://localhost:${PORT}`;
const GUIDES = ["how-to-find-reliable-chinese-factories", "supplier-verification-checklist", "quality-inspection-guide", "china-sourcing-costs", "importing-from-china-to-the-uk", "importing-from-china-to-uae-saudi-arabia", "product-compliance-guide-china-imports", "canton-fair-buyers-guide"].map((s) => `/guides/${s}/`);
const PAGES = ["/", "/about-us/", "/sourcing-services/", "/product-categories/", "/regional-support/", "/certifications/", "/contact-us/", "/privacy-policy/", "/guides/", ...GUIDES];
const WIDTHS = [375, 390, 430, 768, 1024, 1180, 1200, 1240, 1280, 1366, 1440];
const NAV_BREAKPOINT = 1280, LOGO_RATIO = 468 / 100;
const problems = [];
const note = (m) => problems.push(m);

// ---- tiny static server applying _headers
const MIME = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "application/javascript", ".webp": "image/webp", ".jpg": "image/jpeg", ".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon", ".woff2": "font/woff2", ".mp4": "video/mp4", ".webm": "video/webm", ".xml": "application/xml", ".txt": "text/plain", ".webmanifest": "application/manifest+json" };
const rules = fs.readFileSync(path.join(DIST, "_headers"), "utf8").split(/\n(?=\S)/).map((b) => b.trim().split("\n")).filter((l) => l[0]).map((l) => ({ pattern: l[0].trim(), headers: l.slice(1).map((x) => x.trim().split(/:\s(.+)/)).filter((x) => x[0]) }));
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split("?")[0]);
  let file = path.join(DIST, url); if (url.endsWith("/")) file = path.join(file, "index.html");
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404, { "Content-Type": "text/html" }); res.end(fs.readFileSync(path.join(DIST, "404.html"))); return; }
  const headers = { "Content-Type": MIME[path.extname(file)] || "application/octet-stream" };
  for (const r of rules) if (r.pattern === url || (r.pattern.endsWith("*") && url.startsWith(r.pattern.slice(0, -1)))) for (const [k, v] of r.headers) headers[k] = v;
  res.writeHead(200, headers); fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(PORT, r));

const browser = await puppeteer.launch({ headless: true, executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || undefined, args: ["--no-sandbox", "--hide-scrollbars"] });
const vp = (w) => (w < 900 ? { width: w, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true } : { width: w, height: 900, deviceScaleFactor: 1 });
async function open(url, w) {
  const page = await browser.newPage(); await page.setViewport(vp(w));
  await page.emulateMediaFeatures([{ name: "prefers-reduced-motion", value: "reduce" }]);
  page.on("console", (m) => { const txt = m.text(); if (/Content Security Policy/i.test(txt)) note(`${url}@${w}: CSP violation: ${txt.slice(0, 120)}`); else if ((m.type() === "error" || m.type() === "warning") && !/\b(502|422)\b/.test(txt)) note(`${url}@${w}: console ${m.type()}: ${txt.slice(0, 120)}`); });
  page.on("pageerror", (e) => note(`${url}@${w}: pageerror ${String(e).slice(0, 120)}`));
  await page.goto(BASE + url, { waitUntil: "networkidle0" });
  await page.evaluate(() => document.fonts.ready);
  return page;
}
const axeSource = fs.readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");

// ---- 1. responsive + accessibility across every page and width
let axeRuns = 0;
for (const p of PAGES) {
  for (const w of WIDTHS) {
    const page = await open(p, w);
    const info = await page.evaluate((bp, ratio) => {
      const cw = document.documentElement.clientWidth;
      const logo = document.querySelector(".brand img").getBoundingClientRect();
      const navVisible = getComputedStyle(document.querySelector(".nav")).display !== "none";
      const footerGuides = [...document.querySelectorAll('footer a[href="/guides/"]')].length;
      const footerGuideArticles = [...document.querySelectorAll('footer a[href^="/guides/"]')].filter((a) => a.getAttribute("href") !== "/guides/").length;
      return { overflow: document.documentElement.scrollWidth > cw, logoOk: Math.abs(logo.width / logo.height - ratio) < 0.1 && logo.height >= 30, navVisible, expectNav: innerWidth >= bp, footerGuides, footerGuideArticles, h1: document.querySelectorAll("h1").length };
    }, NAV_BREAKPOINT, LOGO_RATIO);
    if (info.overflow) note(`${p}@${w}: horizontal overflow`);
    if (!info.logoOk) note(`${p}@${w}: logo aspect ratio or size wrong`);
    if (info.navVisible !== info.expectNav) note(`${p}@${w}: navigation mode wrong (visible=${info.navVisible})`);
    if (info.footerGuides !== 1 || info.footerGuideArticles) note(`${p}@${w}: footer guides links ${info.footerGuides}/${info.footerGuideArticles}`);
    if (info.h1 !== 1) note(`${p}@${w}: ${info.h1} H1`);
    if (w === 390 || w === 1440) {
      await page.evaluate(axeSource);
      const v = await page.evaluate(async () => (await axe.run(document, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"] } })).violations.map((x) => `${x.id} (${x.nodes.length})`));
      axeRuns++; if (v.length) note(`${p}@${w}: axe ${v.join(", ")}`);
    }
    await page.close();
  }
}

// ---- 2. guide TOC anchors land below the sticky header
for (const g of GUIDES) for (const w of [390, 1440]) {
  const page = await open(g, w);
  const res = await page.evaluate(async () => {
    const headerH = document.querySelector(".header").getBoundingClientRect().height; const out = [];
    for (const a of document.querySelectorAll(".guide-toc a")) {
      const id = a.getAttribute("href").slice(1); const el = document.getElementById(id);
      if (!el) { out.push(`missing #${id}`); continue; }
      el.scrollIntoView(); await new Promise((r) => setTimeout(r, 30));
      const top = el.getBoundingClientRect().top; if (top < headerH - 1) out.push(`#${id} under header (${Math.round(top)}px)`);
      if (/^\s*\d+[.)]/.test(a.textContent)) out.push(`label numbered: ${a.textContent.trim()}`);
    }
    return out;
  });
  res.forEach((r) => note(`${g}@${w}: TOC ${r}`)); await page.close();
}

// ---- 3. drawer behaviour (mobile) and resize cleanup; hidden chat controls; keyboard
{
  const page = await open("/", 390);
  await page.evaluate(() => document.getElementById("nav-open").click()); await new Promise((r) => setTimeout(r, 300));
  const o = await page.evaluate(() => ({ focus: document.activeElement.id, inert: document.getElementById("main").hasAttribute("inert"), locked: document.body.style.overflow === "hidden" }));
  if (o.focus !== "nav-close" || !o.inert || !o.locked) note(`drawer open state wrong ${JSON.stringify(o)}`);
  await page.keyboard.press("Escape");
  const c = await page.evaluate(() => ({ open: document.getElementById("drawer").classList.contains("is-open"), focus: document.activeElement.id, inert: document.getElementById("main").hasAttribute("inert"), locked: document.body.style.overflow === "hidden" }));
  if (c.open || c.focus !== "nav-open" || c.inert || c.locked) note(`drawer close/restore wrong ${JSON.stringify(c)}`);
  await page.evaluate(() => document.getElementById("nav-open").click()); await new Promise((r) => setTimeout(r, 200));
  await page.setViewport(vp(1440)); await new Promise((r) => setTimeout(r, 400));
  const r = await page.evaluate(() => ({ open: document.getElementById("drawer").classList.contains("is-open"), locked: document.body.style.overflow === "hidden", inert: document.getElementById("main").hasAttribute("inert") }));
  if (r.open || r.locked || r.inert) note(`drawer resize cleanup failed ${JSON.stringify(r)}`);
  await page.close();
}
{
  const page = await open("/", 1440);
  await page.keyboard.press("Tab");
  const first = await page.evaluate(() => document.activeElement.className);
  if (!/skip-link/.test(first)) note(`first tab stop is ${first}, expected skip link`);
  let fabFocused = false;
  for (let i = 0; i < 300; i++) { await page.keyboard.press("Tab"); if (await page.evaluate(() => !!document.activeElement.closest(".fab__menu"))) { fabFocused = true; break; } if (await page.evaluate(() => document.activeElement === document.body) && i > 5) break; }
  if (fabFocused) note("hidden chat controls received keyboard focus");
  await page.close();
}

// ---- 4. WhatsApp composer: validation, draft correctness, encoding, no network, no storage, overlong text, double submit
{
  const NUMBER = "8619042799025";
  const page = await browser.newPage(); await page.setViewport(vp(390));
  await page.emulateMediaFeatures([{ name: "prefers-reduced-motion", value: "reduce" }]);
  await page.evaluateOnNewDocument(() => { window.__opened = []; window.open = function (u) { window.__opened.push(String(u)); return null; }; });
  const requests = []; page.on("request", (r) => requests.push(r.url()));
  page.on("console", (m) => { if (m.type() === "error") note(`composer: console error ${m.text().slice(0, 120)}`); });
  page.on("pageerror", (e) => note(`composer: pageerror ${String(e).slice(0, 120)}`));
  await page.goto(BASE + "/contact-us/", { waitUntil: "networkidle0" });
  const F = "#inquiry-form";
  const click = () => page.evaluate((F) => document.querySelector(F + ' button[type="submit"]').click(), F);
  const set = (n, v) => page.evaluate((F, n, v) => { const el = document.querySelector(F + ' [name="' + n + '"]'); el.value = v; el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true })); }, F, n, v);
  // form markup: no submission target, no removed fields, truthful copy
  const markup = await page.evaluate((F) => { const f = document.querySelector(F); const card = f.parentNode; return { action: f.hasAttribute("action"), method: f.hasAttribute("method"), email: !!f.querySelector('[name="email"]'), phone: !!f.querySelector('[name="phone"]'), file: !!f.querySelector('input[type="file"]'), button: f.querySelector('button[type="submit"]').textContent.trim(), heading: (card.querySelector("h2, h3") || {}).textContent, text: card.textContent }; }, F);
  if (markup.action || markup.method || markup.email || markup.phone || markup.file) note(`composer markup wrong ${JSON.stringify(markup)}`);
  if (markup.button !== "Continue on WhatsApp") note(`composer button copy is ${JSON.stringify(markup.button)}`);
  if (!/Tell us what you need/.test(markup.heading || "")) note(`composer heading is ${JSON.stringify(markup.heading)}`);
  if (/Send enquiry|Message sent|Successfully submitted|has been sent/i.test(markup.text)) note("composer copy claims a message was sent");
  // validation focuses the first invalid field and announces the error
  await click(); await new Promise((r) => setTimeout(r, 150));
  const v = await page.evaluate((F) => ({ focus: document.activeElement.id, invalid: document.querySelectorAll(F + " .is-invalid").length, ackErr: getComputedStyle(document.getElementById("inquiry-form-ack-err")).display, status: document.querySelector(F + " .form__status").textContent, opened: window.__opened.length }), F);
  if (v.focus !== "inquiry-form-name" || v.invalid < 5 || v.ackErr !== "block" || !v.status || v.opened) note(`composer validation wrong ${JSON.stringify(v)}`);
  // a complete draft with awkward characters; company left blank so it must be omitted
  const before = requests.length;
  await set("name", "Zoë O'Brien"); await set("country", "United Kingdom"); await set("category", "Electronics"); await set("service", "Quality inspection");
  await set("budget", "£8,000 & 500 units"); await set("message", "Wir brauchen Kabel für „Auto & Home“ — 100% Kupfer; Lieferung nach Köln?\nZweite Zeile: 你好.");
  await page.evaluate(() => { document.getElementById("inquiry-form-ack").checked = true; });
  await click(); await new Promise((r) => setTimeout(r, 300));
  const after = await page.evaluate((F) => ({ opened: window.__opened.slice(), disabled: document.querySelector(F + ' button[type="submit"]').disabled, next: (() => { const n = document.querySelector(".form-next"); return n && !n.hidden ? { text: n.textContent, link: n.querySelector("[data-wa-draft]").getAttribute("href"), focused: document.activeElement === n } : null; })(), status: document.querySelector(F + " .form__status").textContent, storage: Object.keys(localStorage).length + Object.keys(sessionStorage).length, cookies: document.cookie }), F);
  if (requests.length !== before) note(`composer made ${requests.length - before} network request(s) on submit: ${requests.slice(before).join(", ")}`);
  if (after.opened.length !== 1) note(`composer opened ${after.opened.length} windows`);
  else {
    const u = new URL(after.opened[0]);
    if (u.hostname !== "wa.me" || u.pathname.replace(/\//g, "") !== NUMBER) note(`composer opened wrong target ${after.opened[0]}`);
    const text = u.searchParams.get("text") || "";
    const expect = "New enquiry from the Flawless Effect website\n\nName: Zoë O'Brien\nCountry: United Kingdom\nProduct category: Electronics\nService required: Quality inspection\nApproximate budget or quantity: £8,000 & 500 units\n\nRequirements:\nWir brauchen Kabel für „Auto & Home“ — 100% Kupfer; Lieferung nach Köln?\nZweite Zeile: 你好.";
    if (text !== expect) note(`composer draft differs:\n${JSON.stringify(text)}\nexpected\n${JSON.stringify(expect)}`);
    if (/Company:|undefined|null|\bname=|\[object/.test(text)) note("composer draft exposes blank fields or internal names");
    if (after.next && after.next.link !== after.opened[0]) note("fallback draft link differs from the opened URL");
  }
  if (!after.disabled || !after.next || !after.next.focused) note(`composer post-open state wrong ${JSON.stringify({ disabled: after.disabled, next: !!after.next, focused: after.next && after.next.focused })}`);
  if (after.next && /sent\b(?! to Flawless Effect)|submitted|delivered/i.test(after.next.text.replace(/is not sent to Flawless Effect|Nothing has been sent to Flawless Effect/g, ""))) note("post-open panel claims the message was sent");
  if (after.storage || after.cookies) note(`composer stored data (storage keys ${after.storage}, cookies ${JSON.stringify(after.cookies)})`);
  // double submission: a second click while disabled must not open again
  await click(); await new Promise((r) => setTimeout(r, 100));
  const dbl = await page.evaluate(() => window.__opened.length);
  if (dbl !== 1) note(`double submission opened WhatsApp ${dbl} times`);
  // editing re-enables the button; an overlong non-ASCII draft must produce a visible error and never open WhatsApp
  await set("message", "é".repeat(1200));
  const re = await page.evaluate((F) => document.querySelector(F + ' button[type="submit"]').disabled, F);
  if (re) note("editing after opening did not re-enable the button");
  await click(); await new Promise((r) => setTimeout(r, 150));
  const long = await page.evaluate((F) => ({ opened: window.__opened.length, err: document.getElementById("inquiry-form-message-err").textContent, shown: getComputedStyle(document.getElementById("inquiry-form-message-err")).display, focus: document.activeElement.id, value: document.querySelector(F + ' [name="message"]').value.length }), F);
  if (long.opened !== 1 || long.shown !== "block" || !/too long/i.test(long.err) || long.focus !== "inquiry-form-message" || long.value !== 1200) note(`overlong draft handling wrong ${JSON.stringify(long)}`);
  await page.close();
  // homepage compact composer opens the same number with the same structure
  const home = await browser.newPage(); await home.setViewport(vp(1440));
  await home.evaluateOnNewDocument(() => { window.__opened = []; window.open = function (u) { window.__opened.push(String(u)); return null; }; });
  await home.goto(BASE + "/", { waitUntil: "networkidle0" });
  await home.evaluate(() => { const set = (n, v) => { const el = document.querySelector('#quick-form [name="' + n + '"]'); el.value = v; el.dispatchEvent(new Event("input", { bubbles: true })); }; set("name", "QA"); set("country", "Germany"); set("category", "Electronics"); set("message", "Quick test."); document.getElementById("quick-form-ack").checked = true; document.querySelector('#quick-form button[type="submit"]').click(); });
  const q = await home.evaluate(() => window.__opened[0] || "");
  if (!q.startsWith("https://wa.me/" + NUMBER + "?text=") || !decodeURIComponent(q).includes("Name: QA\nCountry: Germany\nProduct category: Electronics\n\nRequirements:\nQuick test.")) note(`homepage composer wrong: ${q}`);
  await home.close();
  console.log("composer: draft, encoding, omission of blank fields, no network, no storage, double-submit guard, overlong text, homepage form");
}

// ---- 5. progressive enhancement: WhatsApp links and the enquiry form must be correct with JavaScript disabled,
//         and JavaScript enhancement must leave the same message in place
{
  const CASES = [
    ["/sourcing-services/", "#product-sourcing a[data-wa]", /product sourcing service/i, "service-specific WhatsApp button"],
    ["/product-categories/", "#electronics a[data-wa]", /sourcing electronics from china/i, "category-specific WhatsApp button"],
    ["/guides/quality-inspection-guide/", ".guide__cta a[data-wa]", /Quality Inspection in China/i, "guide-specific WhatsApp button"],
    ["/", ".hero__ctas a[data-wa]", /sourcing a product from China/i, "primary homepage WhatsApp button"],
  ];
  const NUMBER = "8619042799025";
  const read = async (page, sel) => page.evaluate((sel) => { const a = document.querySelector(sel); return a ? { href: a.getAttribute("href"), msg: a.getAttribute("data-wa") || document.body.getAttribute("data-wa-message") || "" } : null; }, sel);
  for (const [url, sel, expect, label] of CASES) {
    const page = await browser.newPage(); await page.setJavaScriptEnabled(false); await page.setViewport(vp(1440));
    await page.goto(BASE + url, { waitUntil: "networkidle0" });
    const nojs = await read(page, sel);
    const jsRan = await page.evaluate(() => document.documentElement.classList.contains("js"));
    if (jsRan) note(`${label}: JavaScript was not disabled`);
    if (!nojs) note(`${label}: element ${sel} not found on ${url}`);
    else {
      let u; try { u = new URL(nojs.href); } catch { u = null; }
      const text = u ? (u.searchParams.get("text") || "") : "";
      if (!u || u.hostname !== "wa.me" || u.pathname.replace(/\//g, "") !== NUMBER) note(`${label}: no-JS href has wrong host/number: ${nojs.href}`);
      if (/[{}]|%7B|%7D|\.lower\(\)/i.test(nojs.href)) note(`${label}: no-JS href contains template syntax: ${nojs.href}`);
      if (!expect.test(text)) note(`${label}: no-JS message ${JSON.stringify(text)} does not name the selected item`);
      if (nojs.msg && text !== nojs.msg) note(`${label}: no-JS message differs from data-wa message`);
    }
    await page.close();
    const page2 = await open(url, 1440);
    const js = await read(page2, sel);
    // compare decoded number + message: Python percent-encodes the apostrophe (%27), encodeURIComponent leaves it bare
    const dec = (h) => { try { const u = new URL(h); return u.hostname + u.pathname.replace(/\//g, "") + "|" + (u.searchParams.get("text") || ""); } catch { return "invalid:" + h; } };
    if (!js || !nojs || dec(js.href) !== dec(nojs.href)) note(`${label}: JavaScript changed the message (${nojs && dec(nojs.href)} -> ${js && dec(js.href)})`);
    await page2.close();
  }
  // Without JavaScript the composer cannot work, so the form must be hidden and a usable WhatsApp link + mailto shown instead
  for (const url of ["/contact-us/", "/"]) {
    const page = await browser.newPage(); await page.setJavaScriptEnabled(false); await page.setViewport(vp(1440));
    await page.goto(BASE + url, { waitUntil: "networkidle0" });
    const st = await page.evaluate((NUMBER) => { const f = document.querySelector("form[data-inquiry]"); const nojs = f && f.parentNode.querySelector(".form-nojs"); const wa = nojs && nojs.querySelector('a[href^="https://wa.me/"]'); const mail = nojs && nojs.querySelector('a[href^="mailto:"]'); return { formHidden: !!f && getComputedStyle(f).display === "none", nojsShown: !!nojs && getComputedStyle(nojs).display !== "none", wa: wa ? wa.getAttribute("href") : null, mail: mail ? mail.getAttribute("href") : null, action: f && f.hasAttribute("action") }; }, NUMBER);
    if (!st.formHidden || !st.nojsShown || !st.wa || !st.wa.includes("wa.me/" + NUMBER) || st.mail !== "mailto:info@flawlesseffect.com" || st.action) note(`no-JS fallback wrong on ${url}: ${JSON.stringify(st)}`);
    await page.close();
  }
  // every visible email address is a mailto link on every page (JavaScript disabled)
  for (const p of PAGES) {
    const page = await browser.newPage(); await page.setJavaScriptEnabled(false); await page.setViewport(vp(1440));
    await page.goto(BASE + p, { waitUntil: "networkidle0" });
    const m = await page.evaluate(() => { const EMAIL = "info@flawlesseffect.com"; const all = (document.body.innerText.match(/info@flawlesseffect\.com/g) || []).length; const linked = [...document.querySelectorAll('a[href="mailto:' + EMAIL + '"]')].filter((a) => a.textContent.includes(EMAIL) && a.getClientRects().length > 0).length; const other = [...document.querySelectorAll('a[href^="mailto:"]')].filter((a) => a.getAttribute("href") !== "mailto:" + EMAIL).length; return { all, linked, other }; });
    if (m.all !== m.linked || m.other) note(`${p}: ${m.all} visible email(s), ${m.linked} linked, ${m.other} other mailto`);
    await page.close();
  }
  console.log(`progressive enhancement: ${CASES.length} WhatsApp links checked with JavaScript disabled and enabled; no-JS form fallback on 2 pages; mailto coverage on ${PAGES.length} pages`);
}

await browser.close(); server.close();
console.log(`browser QA: ${PAGES.length} pages × ${WIDTHS.length} widths, ${axeRuns} axe runs, ${GUIDES.length * 2} TOC checks`);
if (problems.length) { console.log(problems.map((p) => "- " + p).join("\n")); process.exit(1); }
console.log("all browser checks passed");
