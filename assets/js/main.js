/* Flawless Effect — site behaviour (no dependencies). Progressive enhancement: every link works without this file;
   the enquiry form is a WhatsApp composer that needs it, so without JavaScript a plain WhatsApp link and the email address are shown instead. */
(function () {
  'use strict';

  // Configurable values arrive from _build/build.py as escaped data attributes on <body>.
  var B = document.body.dataset;
  var CONFIG = {
    whatsappNumber: B.whatsapp || '8619042799025',
    defaultMessage: "Hi, I'm interested in sourcing a product from China and would like some help.",
    email: B.email || '',
    wechatId: B.wechatId || '',
    wechatQr: B.wechatQr || ''
  };
  var MAX_WA_URL = 1800;       // generic links fall back to the default message above this length
  var MAX_DRAFT_URL = 2000;    // composer: the finished wa.me URL must fit; otherwise the visitor is asked to shorten the text

  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var isTouch = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent) || window.matchMedia('(pointer: coarse)').matches;

  /* ---------- WhatsApp links (static hrefs exist in HTML; this only refines the message) ---------- */
  function waUrl(message) {
    var url = 'https://wa.me/' + CONFIG.whatsappNumber + '?text=' + encodeURIComponent(message || CONFIG.defaultMessage);
    return url.length <= MAX_WA_URL ? url : 'https://wa.me/' + CONFIG.whatsappNumber + '?text=' + encodeURIComponent(CONFIG.defaultMessage);
  }
  function initWhatsApp() {
    var pageCtx = document.body.getAttribute('data-wa-message');
    $$('[data-wa]').forEach(function (a) {
      var msg = a.getAttribute('data-wa') || pageCtx || CONFIG.defaultMessage;
      a.setAttribute('href', waUrl(msg));
      a.setAttribute('target', '_blank');
      a.setAttribute('rel', 'noopener');
    });
  }

  /* ---------- Header ---------- */
  function initHeader() {
    var header = $('.header'); if (!header) return;
    var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 8); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---------- Shared: make the rest of the page inert while an overlay is open ---------- */
  function setInert(on, except) {
    $$('#main, .footer, .header, .mobile-bar, .fab, #drawer, #wechat-modal').forEach(function (el) {
      if (el === except) return;
      if (on) el.setAttribute('inert', ''); else el.removeAttribute('inert');
    });
  }
  function trapFocus(e, root) {
    var f = $$('a[href], button:not([disabled]), input:not([hidden]), select, textarea, [tabindex]:not([tabindex="-1"])', root)
      .filter(function (el) { return el.offsetParent !== null; });
    if (!f.length) return;
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  /* ---------- Mobile drawer ---------- */
  function initDrawer() {
    var drawer = $('#drawer'), open = $('#nav-open'), close = $('#nav-close');
    if (!drawer || !open) return;
    var isOpen = false;
    function show() {
      isOpen = true;
      drawer.classList.add('is-open'); drawer.setAttribute('aria-hidden', 'false');
      open.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
      setInert(true, drawer);
      (close || drawer).focus();
    }
    function hide(restoreFocus) {
      if (!isOpen) return;
      isOpen = false;
      drawer.classList.remove('is-open'); drawer.setAttribute('aria-hidden', 'true');
      open.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
      setInert(false);
      if (restoreFocus !== false) open.focus();
    }
    open.addEventListener('click', show);
    if (close) close.addEventListener('click', hide);
    $('.drawer__backdrop', drawer).addEventListener('click', hide);
    drawer.addEventListener('keydown', function (e) { if (e.key === 'Escape') hide(); if (e.key === 'Tab') trapFocus(e, drawer); });
    $$('a', drawer).forEach(function (a) { a.addEventListener('click', function () { hide(false); }); });
    // Breakpoint cleanup: the desktop nav appears at 1280px, so close the drawer if the viewport grows past it.
    var mq = window.matchMedia('(min-width: 1280px)');
    var onChange = function (ev) { if (ev.matches) hide(false); };
    if (mq.addEventListener) mq.addEventListener('change', onChange); else mq.addListener(onChange);
  }

  /* ---------- Floating chat (desktop) ---------- */
  function initFab() {
    var fab = $('.fab'); if (!fab) return;
    var t = $('.fab__toggle', fab), menu = $('.fab__menu', fab);
    function set(openNow) {
      fab.classList.toggle('is-open', openNow);
      t.setAttribute('aria-expanded', openNow ? 'true' : 'false');
      if (openNow) { menu.hidden = false; menu.removeAttribute('inert'); requestAnimationFrame(function () { fab.classList.add('is-shown'); }); }
      else { fab.classList.remove('is-shown'); menu.setAttribute('inert', ''); menu.hidden = true; }
    }
    set(false);
    t.addEventListener('click', function () { set(!fab.classList.contains('is-open')); });
    document.addEventListener('click', function (e) { if (!fab.contains(e.target)) set(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && fab.classList.contains('is-open')) { set(false); t.focus(); } });
  }

  /* ---------- Mobile bar: hide (and make inert) while a form is on screen ---------- */
  function initMobileBar() {
    var bar = $('.mobile-bar'); if (!bar) return;
    document.body.classList.add('has-mobile-bar');
    var mq = window.matchMedia('(min-width: 900px)');
    function apply() {
      var offscreen = bar.classList.contains('is-hidden') || mq.matches;
      if (offscreen) { bar.setAttribute('inert', ''); bar.setAttribute('aria-hidden', 'true'); }
      else { bar.removeAttribute('inert'); bar.removeAttribute('aria-hidden'); }
    }
    var form = $('#inquiry-form') || $('#quick-form');
    if (form && 'IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) { bar.classList.toggle('is-hidden', entries[0].isIntersecting); apply(); }, { threshold: 0.15 }).observe(form);
    }
    if (mq.addEventListener) mq.addEventListener('change', apply); else mq.addListener(apply);
    apply();
  }

  /* ---------- Clipboard with truthful feedback ---------- */
  function copyText(text, statusEl, fallbackField) {
    var ok = function () { statusEl.textContent = 'Copied to clipboard.'; statusEl.classList.remove('is-error'); if (fallbackField) fallbackField.hidden = true; };
    var fail = function () {
      statusEl.textContent = 'Copy failed. Select the text and copy it manually.'; statusEl.classList.add('is-error');
      if (fallbackField) { fallbackField.hidden = false; fallbackField.focus(); fallbackField.select(); }
    };
    if (navigator.clipboard && navigator.clipboard.writeText && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(ok, fail);
    } else { fail(); }
  }

  /* ---------- WeChat modal ---------- */
  function initWeChat() {
    var modal = $('#wechat-modal'); if (!modal) return;
    if (!CONFIG.wechatId && !CONFIG.wechatQr) { document.body.classList.add('no-wechat'); return; }
    var qrBox = $('.modal__qr', modal), idEl = $('.modal__id', modal), intro = $('.modal__intro', modal), title = $('#wechat-title', modal), help = $('.modal__help', modal), copyBtn = $('[data-copy-wechat]', modal), copied = $('.modal__copied', modal), idField = $('.modal__id-field', modal);
    if (CONFIG.wechatQr) {
      title.textContent = 'Scan to chat on WeChat';
      qrBox.hidden = false; while (qrBox.firstChild) qrBox.removeChild(qrBox.firstChild);
      var img = document.createElement('img'); img.src = CONFIG.wechatQr; img.alt = 'Flawless Effect WeChat QR code'; img.width = 220; img.height = 220; qrBox.appendChild(img);
      intro.textContent = 'Open WeChat, tap “+” then “Scan”, and point your camera at the code.';
    } else {
      title.textContent = 'Copy WeChat ID';
      qrBox.hidden = true;
      intro.textContent = 'We are on WeChat for buyers who prefer it.';
    }
    if (CONFIG.wechatId) {
      while (idEl.firstChild) idEl.removeChild(idEl.firstChild);
      idEl.appendChild(document.createTextNode('WeChat ID: '));
      var strong = document.createElement('strong'); strong.textContent = CONFIG.wechatId; idEl.appendChild(strong);
      help.textContent = 'How to add us: open WeChat, tap + then Add Contacts, search ' + CONFIG.wechatId + ', and look for the FLAWLESS effect logo.';
      copyBtn.addEventListener('click', function () { copyText(CONFIG.wechatId, copied, idField); });
    } else { idEl.hidden = true; help.hidden = true; copyBtn.parentNode.hidden = true; }

    var lastFocus = null;
    function show() {
      lastFocus = document.activeElement;
      modal.classList.add('is-open'); modal.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
      setInert(true, modal);
      $('.modal__close', modal).focus();
    }
    function hide() {
      modal.classList.remove('is-open'); modal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
      setInert(false);
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }
    $$('[data-wechat]').forEach(function (b) { b.addEventListener('click', function (e) { e.preventDefault(); show(); }); });
    $('.modal__close', modal).addEventListener('click', hide);
    $('.modal__backdrop', modal).addEventListener('click', hide);
    modal.addEventListener('keydown', function (e) { if (e.key === 'Escape') hide(); if (e.key === 'Tab') trapFocus(e, modal); });
  }

  /* ---------- Scroll reveal (content is visible without JS; html.js enables the animation) ---------- */
  function initReveal() {
    var els = $$('.reveal'); if (!els.length) return;
    if (reduceMotion || !('IntersectionObserver' in window)) { els.forEach(function (el) { el.classList.add('is-in'); }); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ---------- Hero video: sources only on wide screens, never on data-saver ---------- */
  function initVideo() {
    var v = $('.hero__video video'); if (!v) return;
    var wide = window.matchMedia('(min-width: 720px)').matches;
    var saveData = navigator.connection && navigator.connection.saveData;
    if (!wide || reduceMotion || saveData) return;
    var start = function () {
      if (v.querySelector('source')) return;
      [['data-webm', 'video/webm'], ['data-mp4', 'video/mp4']].forEach(function (pair) {
        var src = v.getAttribute(pair[0]); if (!src) return;
        var el = document.createElement('source'); el.src = src; el.type = pair[1]; v.appendChild(el);
      });
      v.preload = 'auto'; v.load();
      var p = v.play(); if (p && p.catch) p.catch(function () {});
    };
    if ('requestIdleCallback' in window) requestIdleCallback(start, { timeout: 2500 }); else setTimeout(start, 1200);
  }

  /* ---------- Enquiry form: WhatsApp composer (client-side only) ----------
     Builds a readable draft from the completed fields, encodes it with encodeURIComponent and opens
     https://wa.me/<number>?text=<draft>. No fetch/XHR, no storage, no logging. The visitor presses Send in WhatsApp. */
  function initForms() { $$('form[data-inquiry]').forEach(setupForm); }

  function setupForm(form) {
    var status = $('.form__status', form), submitBtn = $('button[type="submit"]', form);
    var msgEl = $('textarea[name="message"]', form), countEl = $('[data-count]', form);
    var nextBox = $('.form-next', form.parentNode);
    var opened = false;

    function setStatus(msg, isErr) { if (!status) return; status.textContent = msg || ''; status.classList.toggle('is-error', !!isErr); }
    function fieldWrap(el) { return el.closest('.field') || el.closest('.consent-wrap'); }
    function markInvalid(el, msg) {
      var wrap = fieldWrap(el); if (wrap) wrap.classList.add('is-invalid');
      el.setAttribute('aria-invalid', 'true');
      if (msg) { var err = wrap && $('.err', wrap); if (err) err.textContent = msg; }
    }
    function clearInvalid(el) { var wrap = fieldWrap(el); if (wrap) wrap.classList.remove('is-invalid'); el.setAttribute('aria-invalid', 'false'); }

    function validate() {
      var firstBad = null;
      $$('[required]', form).forEach(function (el) {
        var valid = el.type === 'checkbox' ? el.checked : !!el.value.trim();
        if (valid) clearInvalid(el); else { markInvalid(el); if (!firstBad) firstBad = el; }
      });
      if (firstBad) firstBad.focus();
      return !firstBad;
    }
    $$('[required]', form).forEach(function (el) {
      el.addEventListener(el.type === 'checkbox' || el.tagName === 'SELECT' ? 'change' : 'input', function () { clearInvalid(el); });
    });
    // any edit after WhatsApp was opened re-enables the button for a fresh draft
    form.addEventListener('input', function () { if (opened) { opened = false; submitBtn.disabled = false; if (nextBox) nextBox.hidden = true; setStatus(''); } });
    if (msgEl && countEl) {
      var max = msgEl.maxLength > 0 ? msgEl.maxLength : 1200;
      var update = function () { countEl.textContent = msgEl.value.length + ' / ' + max + ' characters'; };
      msgEl.addEventListener('input', update); update();
    }
    prefill(form);

    // Plain-text draft: labelled lines for completed fields only; blank optional fields are omitted.
    function draft() {
      var lines = ['New enquiry from the Flawless Effect website', ''];
      var message = '';
      $$('input[data-label], select[data-label], textarea[data-label]', form).forEach(function (el) {
        var val = (el.value || '').replace(/\s+$/, '').replace(/^\s+/, '');
        if (!val) return;
        if (el.tagName === 'TEXTAREA') { message = val; return; }
        lines.push(el.getAttribute('data-label') + ': ' + val.replace(/\s*\n+\s*/g, ' '));
      });
      if (message) lines.push('', 'Requirements:', message);
      return lines.join('\n');
    }
    function draftUrl(text) { return 'https://wa.me/' + CONFIG.whatsappNumber + '?text=' + encodeURIComponent(text); }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (submitBtn.disabled) return;                       // double submission guard
      if (!validate()) { setStatus('Please complete the highlighted fields.', true); return; }
      var url = draftUrl(draft());
      if (url.length > MAX_DRAFT_URL) {
        var over = url.length - MAX_DRAFT_URL;
        var msg = 'Your text is too long for a WhatsApp link by about ' + Math.ceil(over / 3) + ' characters. Please shorten your requirements; you can add more detail in WhatsApp after the first message.';
        markInvalid(msgEl, msg); msgEl.focus(); setStatus('Please shorten your requirements.', true);
        return;                                             // never truncated silently
      }
      submitBtn.disabled = true; opened = true;
      setStatus('Opening WhatsApp with your draft…');
      if (nextBox) {
        var link = $('[data-wa-draft]', nextBox); if (link) link.href = url;
        nextBox.hidden = false;
      }
      window.open(url, '_blank', 'noopener,noreferrer');
      if (nextBox) { nextBox.focus(); nextBox.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'center' }); }
    });
  }

  /* Prefill selects from URL parameters, e.g. /contact-us/?category=Electronics&service=Quality%20inspection */
  function prefill(form) {
    var params = new URLSearchParams(location.search);
    [['category', 'select[name="category"]'], ['service', 'select[name="service"]']].forEach(function (pair) {
      var val = params.get(pair[0]); var sel = $(pair[1], form);
      if (!val || !sel) return;
      var want = val.trim().toLowerCase().slice(0, 80);
      var match = Array.prototype.find.call(sel.options, function (o) { return o.value.toLowerCase() === want || o.textContent.trim().toLowerCase() === want; });
      if (!match) match = Array.prototype.find.call(sel.options, function (o) { return o.value && (want.indexOf(o.value.toLowerCase()) === 0 || o.value.toLowerCase().indexOf(want) === 0); });
      if (match) sel.value = match.value;
    });
  }

  function initYear() { $$('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); }); }

  document.addEventListener('DOMContentLoaded', function () {
    initWhatsApp(); initHeader(); initDrawer(); initFab(); initMobileBar(); initWeChat(); initReveal(); initVideo(); initForms(); initYear();
  });
})();
