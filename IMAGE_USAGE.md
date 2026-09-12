# Guide image usage record

Source photographs live in `/Users/atlassingh/Documents/Myu Website/` and are unchanged. Published derivatives are in `assets/img/guides/` (responsive WebP at 640, 960 and 1440 px wide where the source allows) and `assets/img/guides/og/` (1200×630 Open Graph cards). All derivatives were produced with ffmpeg (EXIF orientation applied on decode) and `cwebp -metadata none`, which strips EXIF including GPS; checked with exiftool. Aspect ratios are preserved in the responsive files; hero framing on the page is done with CSS `object-fit`, not by cropping the file. OG cards are necessarily 1200×630 crops of the photo with the approved white logo and the guide title overlaid.

| Original file | Published files | Guide | What the image shows | Alt text | Caption | Processing | Suitability notes |
|---|---|---|---|---|---|---|---|
| `1071.JPG` (4493×3209) | `factory-floor-visit-{640,960,1440}.webp`, `og/how-to-find-reliable-chinese-factories.jpg` | How to Find Reliable Chinese Factories | A group of visitors in hi-vis vests and caps walking a factory floor; a Flawless Effect team member in the foreground | “A group of visiting buyers in hi-vis vests walking a factory floor in China with Flawless Effect” | “Walking a factory floor with visiting buyers” | Resize only; OG crop | Lanyard text is not legible at published sizes. A small vehicle-maker logo on the visitors’ caps is visible at 1440 px; the factory is not named and no relationship is claimed. Third parties present as part of a group visit; also the homepage hero. Focal point 20% (heads stay in frame at 16:9 and 4:3). |
| `IMG_1769.JPG` (3213×5712, portrait) | `supplier-showroom-meeting-{640,960,1440}.webp`, `og/supplier-verification-checklist.jpg` | Supplier Verification Checklist | Two men in conversation at a showroom counter in a retail-style interior | “Two people in discussion at a supplier showroom counter in Guangzhou” | “A supplier meeting at a showroom in Guangzhou” | Resize; portrait kept, CSS-framed 16:9 on page; OG crop | Location given as Guangzhou per the client’s own site (“Our meeting spaces”). Not captioned as an audit. Focal point 50% (portrait source; both people in frame at 16:9 and 4:3). |
| `IMG_5840.JPG` (5712×4284, EXIF rotate 90) | `product-sample-review-{640,960,1440}.webp`, `og/quality-inspection-guide.jpg` | Quality Inspection Guide | A visiting buyer seated at a round table with product samples, papers and drinks in the Guangzhou lounge | “A visiting buyer seated at a table reviewing product samples and papers in Flawless Effect’s Guangzhou meeting space” | “Reviewing samples with a visiting buyer in Guangzhou” | Orientation applied; resize; OG crop | Papers on the table are not legible. Phone in hand, no screen content visible. A lounge membership standee with two small QR codes stands on the table; at the largest published size each code is roughly 40 px wide and not expected to scan. Not captioned as an inspection. Focal point 40% (hero) / 30% (OG card). |
| `IMG_6541.HEIC` (5712×4284, EXIF rotate 90) | `buyer-briefing-guangzhou-{640,960,1440}.webp`, `og/china-sourcing-costs.jpg` | China Sourcing Costs | Several people seated on lounge sofas facing a screen during a briefing in the Guangzhou lounge | “International buyers seated in a lounge in Guangzhou listening to a briefing” | “A buyer briefing at our Guangzhou meeting space” | HEIC decoded by ffmpeg, orientation applied; resize; OG crop | A wall screen at the far right shows an event slide; its title (“Digital-Intelligence Integration”) is readable at the 1440 px hero size, the smaller lines are not. No personal data is shown. Individuals are not identified. Focal point 55% (hero) / 60% (OG card). |
| `IMG_1839.JPG` (1080×1920) | `gulf-buyers-trade-exhibition-{640,960}.webp`, `og/importing-from-china-to-uae-saudi-arabia.jpg` | Importing from China to the UAE and Saudi Arabia | A Flawless Effect team member in conversation with two men in traditional Gulf dress at an exhibition stand | “Flawless Effect in conversation with buyers wearing traditional Gulf dress at a trade exhibition” | “Meeting Gulf buyers at a trade exhibition” | Resize only (source too small for 1440); OG crop | Exhibition and city are not named because they are not verified. No location in the Gulf is implied. Source is 1080 px wide, so the OG card was rendered from a metadata-stripped full-resolution decode of the original rather than the 960 px derivative. Focal point 30% (hero, keeps the raised hand and all three faces) / 40% (OG card). |
| `54712a30c021a881ac9a870c6e177d3f.JPG` (2130×3200) | `vehicle-test-chamber-visit-{640,960,1440}.webp`, `og/product-compliance-guide-china-imports.jpg` | Product Compliance Guide | A Flawless Effect team member in a hi-vis vest inside a vehicle anechoic test chamber with a pickup truck | “Flawless Effect inside a vehicle testing chamber with a pickup truck during a factory visit” | “Inside a vehicle test chamber during a factory visit” | Resize; OG crop | A manufacturer logo is partly visible on the chamber wall; the manufacturer is not named and no certification claim is made about the image. |
| `IMG_1257.JPG` (3213×5712, portrait) | `guangzhou-skyline-meeting-space-{640,960,1440}.webp`, `og/canton-fair-buyers-guide.jpg` | Canton Fair Buyer’s Guide | Round dining table by floor-to-ceiling windows with the Guangzhou skyline and Canton Tower outside | “The Guangzhou skyline with the Canton Tower seen through the windows of Flawless Effect’s meeting space” | “Guangzhou, seen from our meeting space” | Resize; CSS-framed; OG crop | Canton Tower is identifiable and verifies the Guangzhou location. Not a photograph of the fair itself, and not captioned as one. |
| `Facetune_15-07-2026-17-41-15.HEIC` (1206×2117) | `trade-exhibition-meeting-{640,960}.webp` | Not placed | A Flawless Effect team member in conversation with a man in a suit at an exhibition | — | — | HEIC decoded; resize | Permission confirmed, but not placed in the guides to avoid repeating the exhibition theme (the same photograph is used on the homepage, Services and Regional Support pages as `exhibition-meeting`). Exhibition not named. |
| — (no suitable logistics or packaging photograph exists in the source folder) | `branded-importing-uk-{640,960,1440}.webp`, `og/importing-from-china-to-the-uk.jpg` | Importing from China to the UK | Restrained branded graphic: ink background, approved white logo, guide title | “Flawless Effect logo on a dark panel with the title Importing from China to the UK” | — | Rendered from the approved logo system | Used instead of a misleading photograph. Replace with a genuine packing or shipment photograph when one is available. |

## Status: permission confirmed for every placement (11 September 2026)

The client confirmed that the photographs containing third-party visitors may be published in every placement. The five guides that had used branded graphics while permission was outstanding now show their intended photographs again, with regenerated OG cards. The UK guide keeps its branded hero because no genuine logistics, packing or shipment photograph exists in the source folder.

| Guide | Hero now published | OG card |
|---|---|---|
| How to Find Reliable Chinese Factories | `factory-floor-visit-*` (from `1071.JPG`) | photo |
| Supplier Verification Checklist | `supplier-showroom-meeting-*` (from `IMG_1769.JPG`) | photo |
| Quality Inspection Guide | `product-sample-review-*` (from `IMG_5840.JPG`) | photo |
| China Sourcing Costs | `buyer-briefing-guangzhou-*` (from `IMG_6541.HEIC`) | photo |
| Importing from China to the UK | `branded-importing-uk-*` | branded (unchanged) |
| Importing to the UAE and Saudi Arabia | `gulf-buyers-trade-exhibition-*` (from `IMG_1839.JPG`) | photo |
| Product Compliance Guide | `vehicle-test-chamber-visit-*` (from `54712a30…JPG`) | photo (unchanged) |
| Canton Fair Buyer’s Guide | `guangzhou-skyline-meeting-space-*` (from `IMG_1257.JPG`) | photo (unchanged) |

Photo OG cards carry a light shade at the top so the white logo stays legible over bright backgrounds. The `branded-*` hero derivatives for the five restored guides remain in `assets/img/guides/` (unreferenced, so not copied to `dist/`) in case permission is ever withdrawn; the site-wide fallback flag `USE_SAFE_IMAGE_FALLBACKS` in `_build/build.py` stays `False`.

### Every placement of the approved third-party photographs

| Source | Site image name | Pages |
|---|---|---|
| `1071.JPG` | `factory-tour` / `factory-floor-visit` | Home (hero), About (hero), Services (Product Sourcing), Find Reliable Factories guide |
| `IMG_1769.JPG` | `showroom-meeting` / `supplier-showroom-meeting` | Home, Services (hero), Supplier Verification guide |
| `IMG_5840.JPG` | `sample-review` / `product-sample-review` | Home, Services (Samples), Quality Inspection guide |
| `IMG_6541.HEIC` | `buyer-briefing` / `buyer-briefing-guangzhou` | About, Regional Support (hero), Contact, China Sourcing Costs guide |
| `IMG_1839.JPG` | `exhibition-middle-east` / `gulf-buyers-trade-exhibition` | Home, Regional Support, UAE and Saudi Arabia guide |
| `Facetune_15-07-2026-17-41-15.HEIC` | `exhibition-meeting` / `trade-exhibition-meeting` | Home, Services (Negotiation), Regional Support |
| `6ce136c2…JPG` | `client-dinner` | About |

Crops were checked in Chrome at 390 px (4:3 frame) and 1440 px (16:9 frame) for each guide hero and for the guide cards on `/guides/`; faces are complete in every frame. EXIF and GPS metadata are absent from every published derivative and OG card (exiftool).

## Excluded from the guides, and why

- `IMG_2700.JPG`, `IMG_2037.JPG`, `IMG_2120.JPG`, `IMG_2956.JPG`: laptop or display screens with visible content.
- `微信图片_2026-09-07_235314_056.jpg`: wall of certificates and award plaques; publishing it could be read as a compliance claim and shows third-party documents.
- `43E61CA9-…TIF`, `截屏*.png`, `wechat.PNG`-style captures, `/flawless-effect-screenshots/`, `/new logos/` (except the approved logo assets): screenshots, documents or brand files, not editorial photography.
- `f71b2ca7…JPG` and `fdd56913…JPG`: a manufacturer’s name is prominent (test chamber wall, event backdrop); using them in editorial guides would imply a relationship that is not verified.
- `6ce136c2…JPG`: a private dinner with identifiable third parties.
- `IMG_1255`, `IMG_1268`, `IMG_2290`, `IMG_3263`, `IMG_3264`, `IMG_3266`, `IMG_3267`, `IMG_3725`: interior views of the meeting space with no guide-relevant subject.
- `Facetune_10-07…`, `Facetune_14-07…`: technology exhibition and Hong Kong event images; relevant only to trade fairs in general and already used on the About page.
- `cat-*.webp` in `assets/img/`: product renders inherited from the previous website, not genuine photographs.

## Notes for the client

None of the selected images shows a verified factory name or private document. Two points are recorded for transparency rather than as blockers: the briefing photograph’s wall screen shows a readable event slide title at the largest size, and the sample-review photograph includes a lounge standee with small QR codes. Tell us if you would prefer either photograph swapped; the `IMG_FALLBACKS` mapping in `_build/build.py` already names non-identifying alternatives.
