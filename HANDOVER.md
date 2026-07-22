# Developer Handover — EA Dressage Equipment, Rules and Tests

This document lets a developer with **no prior contact with the original
maintainer** take over, rehost and maintain this app. Read it alongside
`README.md` (repo layout and content pipeline).

The app is live (July 2026) at:

- **Production / share URL:** https://ea-dressage.eq-au.workers.dev (Cloudflare
  Workers, original maintainer's account)
- **Mirror:** https://agunn.github.io/ea-dressage (GitHub Pages, deploys from
  this repo's `main`)

If you are reading this as a handover, you will likely be **rehosting at a new
URL on your own accounts** — the checklist in section 4 covers everything that
must change. Nothing else about the app needs rebuilding: `site/` is the
complete, deployable product.

---

## 1. What this is (and the one rule that matters)

A static, installable web app (PWA): a searchable reference of permitted and
prohibited dressage equipment under Equestrian Australia (EA) rules, plus the
equipment rule text, test-sheet links and rulebook PDFs. Vanilla HTML/CSS/JS,
one page, no framework, no build step, no backend. Content lives in
`site/data.js` as a plain JS file so the app also works opened straight from
the filesystem.

**The one rule:** this is a *rules reference* — content accuracy beats
everything. Never invent, reword or "improve" rule wording. Wording comes from
the EA source documents; deviations only ever happened with explicit approval
from the EA Dressage Committee (EADC) or the app owner, and each one is logged
in section 10 below. Keep that log going.

## 2. What you need

- This repo. It contains everything required to host and maintain the app.
- Any static web host (two ready-made options below).
- Python 3 only if you regenerate the install-guide PDF or process new images
  (`pip install reportlab pillow qrcode pypdfium2`).
- Node (any recent version) for the sanity-check one-liners.

**Not in the repo, and not required:** the original EA source `.docx` files
(`source-docs/` is gitignored — `site/data.js` is the authoritative content and
was hand-verified against them; get fresh source documents from the EADC if EA
publishes new editions), the original maintainer's Cloudflare/GitHub accounts,
and the Cloudflare Web Analytics account (see section 4, step 5).

## 3. Hosting: two known-good recipes

`site/` deploys as-is on any static host. These two are proven with this app:

**GitHub Pages** — push this project to a GitHub repository of your own and
enable Pages. The included workflow `.github/workflows/deploy-pages.yml`
publishes `site/` on every push to `main`. Zero config beyond enabling Pages
in repo settings.

**Cloudflare Workers (static assets)** — `wrangler.jsonc` at the repo root is
the whole config (assets-only worker serving `./site`). One-off deploy from a
checkout:

    CLOUDFLARE_API_TOKEN=<your token> CLOUDFLARE_ACCOUNT_ID=<your account id> \
      npx wrangler deploy

Rename the worker in `wrangler.jsonc` to suit your account. Cloudflare's
Git-connected "Workers Builds" can automate this on push, same as the original
setup.

**⚠ Host redirect gotcha (learned the hard way):** Cloudflare's asset serving
307-redirects `/index.html` → `/`. A service worker that caches a redirected
response for the start page **breaks offline app launches** (browsers reject
redirect-tainted cached responses for navigations, and only after a version
update — fresh installs mask it). `site/sw.js` defends against this
(`cleanPut` / `unpoison`); do not remove those helpers, and if you host
somewhere new, check how it responds to `/index.html` before assuming offline
works. Test offline launch **after an update, not just after a fresh install**
(see section 7).

## 4. Rehosting checklist — everything tied to the old URL

The production URL appears in the app in a handful of places. With the app at
your new URL, work through:

1. **`site/index.html`** — search for `ea-dressage.eq-au.workers.dev` and
   replace: two install-popup mentions (Safari/Chrome steps), the share-popup
   displayed URL and QR `alt`, and two JS share/copy handlers (app URL and
   install-guide PDF URL).
2. **`tools/make_install_guide.py`** — `URL` constant *and* the QR payload at
   the top; also the two absolute output paths (they point at the original
   maintainer's folders). Then run it to regenerate `site/install-guide.pdf`
   and `site/images/install-guide.jpg`.
3. **`site/images/app-qr.png`** — the in-app share QR. Regenerate:

       python3 -c "import qrcode; qrcode.make('https://YOUR-URL/', box_size=10, border=2).save('site/images/app-qr.png')"

4. **`site/manifest.json`** — no URL inside, nothing to change (icons and
   `start_url` are relative). Same for `manifest-staging.json`.
5. **Analytics** — the `<script ... cloudflareinsights ...>` tag at the bottom
   of `index.html` reports to the original maintainer's free Cloudflare Web
   Analytics account. Either delete the line, or create your own Web Analytics
   site (Cloudflare dashboard → Analytics & Logs → Web Analytics → Add site →
   JS-snippet route) and swap in your token. The token is public by design;
   the app works identically with the line removed.
6. **Staging (recommended)** — deploy the same `site/` to a second worker whose
   name contains `-staging` (e.g. `yourapp-staging`). The app detects the
   hostname and automatically: uses `manifest-staging.json` (installs as
   "EA Staging", amber theme) and shows a fixed amber STAGING badge on screen.
   Deploy manually with `npx wrangler deploy --name yourapp-staging` — never
   wire staging to git pushes, that is what production is for.
   *Do not judge PWA installability from a staging origin's first minutes* —
   Chrome caches a per-origin "not installable" verdict with no user-facing
   reset; if that happens, mint a fresh worker name.
7. **Existing installed users** cannot be migrated: a PWA is keyed to its URL.
   A new URL means users install afresh (the old URL's installs keep working
   only while the old hosting stays up). Coordinate the cut-over accordingly.

## 5. Release discipline (every change, no exceptions)

1. Make your edits.
2. **Bump the cache version** in `site/sw.js` (`ea-equipment-vNN` → vNN+1) —
   without this, returning users keep the old version indefinitely. Also bump
   the matching `cacheV: vNN` string in the `?debug` overlay in `index.html`.
3. Update the footer line "Site last updated D Month YYYY" in `index.html`.
4. Sanity checks (from repo root):

       node --check site/sw.js
       node -e "const fs=require('fs');(0,eval)(fs.readFileSync('site/data.js','utf8').replace('const EA_DATA','globalThis.EA_DATA'));console.log(EA_DATA.items.length,'items');const m=EA_DATA.items.flatMap(i=>i.images||[]).filter(f=>!fs.existsSync('site/images/'+f));console.log(m.length,'missing images')"

5. Stage it, test on real phones (see section 7), then deploy production.

Users then see a "New version available — tap to update" pill on their next
online open; one tap completes the update.

## 6. Content maintenance

**Editing items** — hand-edit `site/data.js`. Each item: `id`, `section` (1–8),
`title`, `status` (`permitted|prohibited|conditional`), `penalty`, `condition`,
`scope` (`competition|warm-up`), `images[]`, `ruleRef`, etc. Rule topics live in
`rules[]`, official illustration plates in `galleries[]`, the EADC noseband
policy in `policy`. Cross-document contradictions go in `conflicts[]` (renders
as flagged cards) — surface conflicts, never silently pick a side.

**Do not rerun the `tools/` pipeline for small edits.** It exists only for a
new edition of the source documents, and `build_merged_data.py` embeds
hand-curated content that must be reviewed line-by-line, not blindly rerun.

**Adding images** — conventions used throughout: flatten transparency to
white, trim to content (background threshold >245), pad 16px white, cap width
640px, save JPEG quality 85, sequential names `imageNNN.jpg` (check the
highest existing number in `site/images/`). Keep the whole site around ~3 MB
excluding the rulebook PDFs — it is all precached to phones.

**Hosted rulebook PDFs** — drop the PDF in `site/docs/`, add a button in the
"Rulebook sections and annexes" card in `index.html`. Offline precache and the
greyed-out-when-unavailable state pick it up automatically (the code derives
the list from the page's own links).

**Committee round-trips** — content corrections historically travelled as a
Word table (item id in a Ref column) sent to the EADC and merged row-by-row on
return. `tools/title-proposals.json` / `title-originals.json` document the
big 2026 title-standardisation pass and allow selective rollback.

## 7. Testing (no test suite — field-test on devices)

The failure modes that actually occurred were all *update-transition* and
*offline* bugs invisible on desktop. Minimum device pass before a production
deploy, on one iPhone and one Android, using the **staging** URL with the app
installed:

1. With the previous version installed and fully downloaded (see below), open
   online → let it update → wait for the plain **ⓘ** icon.
2. Aeroplane mode → relaunch → browse items → open a rulebook PDF.
3. Both must work **first time**. If launch fails offline after an update, you
   have reintroduced the redirect-taint bug (section 3).

The **ⓘ icon** on the Equipment tab doubles as the offline-download indicator:
it shows a progress ring until every image and PDF is stored *and* the service
worker fully controls the app, and only then turns into a plain ⓘ. "Wait for
the plain ⓘ before going offline" is the user-facing contract — keep it
truthful if you extend precaching.

iOS quirks to preserve: opening an in-app PDF strands iOS standalone users
(no back UI) — the app shows a "swipe from the left edge" tip card first
(iOS-installed only). The iOS aero-mode system dialog about mobile data is
cosmetic and expected.

## 8. Where knowledge lives

- This document — working rules, rehosting, release discipline, the
  wording-amendment log (section 10), open items (section 9).
- `README.md` — repo layout and content pipeline description.
- `?debug` appended to the app URL — on-device diagnostics overlay (viewport,
  service-worker state, cache version).

## 9. Open items inherited with the app

- EA Para Dressage Tests sub-tab is built but hidden: `SHOW_PARA = false` in
  `index.html`. Flip to `true` to reinstate; also restore Para in the install
  guide's "What's inside" line (`tools/make_install_guide.py`) and regenerate.
- s1-007 "Variant of Eggbutt cheeks": source document had a placeholder image;
  none exists in the app.
- Two rule-image captions (lungeing gear / nose net, rules 5.13/5.15) are
  marked "please verify caption" pending EADC confirmation.
- Custom domain: the owner considered `eadert.au` / `eadressage.au` (available
  as of July 2026, never purchased). A custom domain would decouple the app
  from any host's URL — worth doing before building a large installed base at
  a new URL.

## 10. Owner-approved wording amendments (differ from source documents)

Every place the app's wording deliberately departs from the EA source
documents, with its authority. Append to this list whenever a new deviation is
approved — it is the audit trail that keeps the app defensible as a reference.

- 2026-07-09 — r6-014 Horse identification numbers: appended "Minimum height
  of numbers is 3.5-4 cm" to the condition, per EADC instruction via owner.
- 2026-07-10 — r6-015 "Equipment against the intent and general principles of
  dressage" removed as an item card, per owner: a catch-all covering the
  Section 6 prohibited items already displayed individually.
- 2026-07-10 — Title standardisation: 93 corrections applied per EADC approval
  plus owner rulings on three held rows (s5-001 "Stock saddles", s1-011
  "Shaped sleeve", s1-014 "Various gags"). Pre-change titles are preserved in
  `tools/title-originals.json` for selective rollback.
- 2026-07-20 — s2-021 renamed "Beris Mullen straight bar" → "Ridged Mullen
  mouths" per owner (committee instruction); second image added (image256).
