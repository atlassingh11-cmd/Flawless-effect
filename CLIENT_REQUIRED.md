# Project status and optional items

**Status: code and content ready for owner-managed deployment.** The owner has confirmed image publication permission, the public email address (`info@flawlesseffect.com`, active and externally tested), domain ownership, and the legal names and business details used in the footer and privacy policy. The owner will handle the GitHub repository and the Cloudflare Pages upload. The site is not yet deployed by this project.

Nothing blocks a production build: every `LAUNCH_REQUIRED` value in `_build/build.py` is filled, and `SITE_MODE=production python3 _build/build.py` runs. The gate remains in place so that a blanked value stops a production build.

## Contact model (final)

- The enquiry form is a WhatsApp composer: it prepares a pre-filled draft and opens WhatsApp. The visitor presses Send in WhatsApp. No email-delivery service, serverless function, database or attachment upload exists.
- Every visible `info@flawlesseffect.com` is a `mailto:` link.
- The privacy policy describes this model, the WhatsApp/Meta and Zoho Mail processing, the international processing by the team in China, the 24-month retention of enquiry correspondence, and the complaint routes (ICO, EU supervisory authorities, local authorities). It is a transparency disclosure; it has not been reviewed by a lawyer, and the owner may wish to arrange that.

## Optional content (modules stay hidden until supplied)

- **WeChat QR image** → `WECHAT_QR`. The modal currently shows “Copy WeChat ID” with the verified ID `flawlesseffect`.
- **Fee model** → `FEE_MODEL` (one paragraph). Enables “How we charge” on the Services page and the related FAQ entry.
- **Team names, roles, languages** → `EVIDENCE["team"]`. Enables “Meet the team” on About.
- **Genuine client quotes** (name, company, country) → `EVIDENCE["reviews"]`. Enables the testimonials section on the homepage.
- **LinkedIn company URL** → `LINKEDIN_URL`.
- **Exact Google Maps place link** → `MAPS_URL` (currently a search for the Pazhou Digital Science and Technology Industrial Park).
- **A genuine packing, warehouse or shipment photograph** for the “Importing to the UK” guide, which currently uses a branded graphic because no logistics photograph exists in the source folder.
- **Genuine product photography** for the six category tiles (replace `assets/img/cat-*.webp`, same names and widths).
- **Author or reviewer** for the guides → `AUTHOR` / `REVIEWER` in `_build/build.py`. Do not supply a name unless the person really wrote or reviewed the guides.

## Claims removed pending evidence

“Serving buyers since 2018” / founding date, “no hidden commission”, “no trading-company markup”, “every photograph taken by our team”, “nothing is held at the border”, guaranteed certification or customs outcomes, “repeat container shipments”, and “English & Chinese” as a stated capability. Supply supporting material if you want any of these reinstated.

## Image permissions (confirmed, 11 September 2026)

Publication permission is confirmed for every photograph containing identifiable third parties, for every placement. Every placement is listed in `IMAGE_USAGE.md`. If permission is ever withdrawn, set `USE_SAFE_IMAGE_FALLBACKS = True` in `_build/build.py` (site pages) and restore the `branded-…` hero names in `_build/guides.py` (guides), then rebuild.
