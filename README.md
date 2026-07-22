# EA Dressage Equipment Reference

A searchable, mobile-friendly reference of permitted and prohibited dressage
equipment for Equestrian Australia competition, built from two source
documents:

- **Equipment Annex v23** (7 Nov 2025, effective 1 Jan 2026) — the item-by-item
  photo catalogue with tick/cross rulings
- **EA National Dressage Rules, Section 5** (2026) — the governing rulebook
  chapter (dress, saddlery & equipment)

The app is a single static page: no backend, no build step, no logins.

> **Taking this project over?** Read [HANDOVER.md](HANDOVER.md) — a complete
> developer handover covering rehosting at a new URL, release discipline,
> content maintenance and the hard-won service-worker gotchas.

## Repo layout

```
site/               The deployable app — host this directory as-is
  index.html        All markup, CSS and JS
  data.js           Generated content (items, rules topics, galleries)
  images/           Processed equipment photos & illustrations
  manifest.json     PWA manifest (installable on iOS/Android home screens)
  sw.js             Service worker: offline caching after first load
tools/              Content pipeline (only needed when source docs change)
  extract_annex.py       docx -> tools/raw_extract.json
  process_images.py      docx media -> site/images/ + filename mappings
  build_merged_data.py   everything -> site/data.js (incl. hand-curated
                         rules topics, galleries, enrichments, new items)
  policy_block.py        EADC noseband policy text + app meta
source-docs/        The two source .docx files
```

## Editing content

For everyday edits, **edit `site/data.js` directly** — each equipment item is
a small JSON record:

```json
{ "id": "s2-014", "section": 2, "title": "Dr Bristol",
  "status": "prohibited", "penalty": "Elimination",
  "scope": "competition", "images": ["image47.jpg"], ... }
```

`status` is one of `permitted` / `prohibited` / `conditional`. `scope` is
`competition` or `warm-up`. Rules topics and the illustration galleries live
in the same file under `rules` and `galleries`.

If a **new version of a source document** arrives, rerun the pipeline from
the repo root (requires `python3 -m pip install lxml pillow`, plus
LibreOffice on PATH for EMF image conversion):

```bash
python tools/extract_annex.py source-docs/equipment-annex-v23.docx
python tools/process_images.py
python tools/build_merged_data.py
```

Note that item-level enrichments, the 24 rulebook items and the rules topics
are curated inside `build_merged_data.py` — review that file when sources
change materially.

## Deploying

Any static host works: GitHub Pages, Cloudflare Pages, or a Synology Web
Station share. Serve the `site/` directory. Over HTTPS the service worker
enables offline use and the app can be installed to a phone home screen
(Share → Add to Home Screen on iOS; install prompt on Android).

For App Store / Play Store distribution later, wrap `site/` with
[Capacitor](https://capacitorjs.com/) — no rework needed.

## Known editorial issues

- **Throat lash conflict**: the Annex banner says all bridles must have a
  throat lash; National Rules 5.11 exempts combined nosebands and Micklem
  bridles. Both wordings shown in the app (Rules tab, flagged card) pending
  an editorial decision.
- `s1-007` "Variant of Eggbutt cheeks" had a placeholder ("INSERT VARIAT OF
  EGGBUTT CHEEKS") in the source Annex — no image or description yet.
- Rules 5.13/5.15 example image captions ("lungeing gear", "nose net") were
  inferred from document position and are marked "please verify caption".
