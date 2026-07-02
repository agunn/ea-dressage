# CLAUDE.md — project context for Claude Code

## What this is
A static, searchable reference app for Equestrian Australia dressage
equipment rules. Single-page vanilla HTML/CSS/JS in `site/`, content
generated into `site/data.js` by Python scripts in `tools/` from two Word
source documents in `source-docs/`. No framework, no bundler, no backend —
keep it that way unless the owner asks otherwise.

## Golden rules
- `site/` must remain deployable as-is on any static host (Synology,
  GitHub Pages, Cloudflare Pages) and continue to work when opened directly
  from `file://` (data is a JS file, not fetched JSON — do not change that).
- This is a **rules reference**: content accuracy beats style. Never invent,
  reword or "improve" rule wording; when sources conflict, surface the
  conflict to the owner (see the `conflicts` array in data.js) rather than
  picking a side.
- Do not regenerate `site/data.js` via the tools pipeline for small content
  edits — hand-edit data.js. The pipeline is only for new source-document
  versions, and `tools/build_merged_data.py` contains hand-curated content
  (rules topics, 24 rulebook items, enrichments) that must be reviewed, not
  blindly rerun.
- Bump the cache name in `site/sw.js` (`ea-equipment-vNN`) whenever content
  or code changes, or returning users will see stale cached versions.

## Data model (site/data.js -> EA_DATA)
- `items[]`: id, section (1–8), sectionName, title, description, notes,
  status (`permitted|prohibited|conditional`), penalty (`Elimination`,
  `Minus 0.5%`, or null), condition, scope (`competition|warm-up`),
  updated, images[], source (`annex|rules`), ruleRef.
- `rules[]`: prose rule topics {id, ref, title, body[], images[{src,cap}]}.
- `galleries[]`: numbered official illustrations (bits 5.20, nosebands 5.21).
- `policy`: EADC noseband policy page. `conflicts[]`: cross-document
  discrepancies shown as flagged cards. `meta`: version strings shown in
  the header — update when content changes.

## UI structure (site/index.html)
Two tabs: Equipment (card grid, status segmented control, section chips,
search) and Rules (topic list + galleries + conflict cards). One shared
modal (`<dialog>`) renders item details, rule topics, galleries and the
policy. Styling via CSS custom properties at the top of the file; verdict
colours: green permitted, red prohibited, amber conditional.

## Testing
No test suite. Sanity-check with Node after data edits:
    node -e "const fs=require('fs');(0,eval)(fs.readFileSync('site/data.js','utf8').replace('const EA_DATA','globalThis.EA_DATA'));console.log(EA_DATA.items.length)"
Verify every `images[]` entry exists in `site/images/`. Keep total site
size small (~3 MB) — images are pre-compressed to ≤700px JPEG q≈83.

## Known open editorial items (owner to resolve)
1. Throat lash: Annex ("all bridles") vs Rules 5.11 (Micklem/combined
   noseband exempt).
2. s1-007 "Variant of Eggbutt cheeks": source had a placeholder, no image.
3. Captions for r5-image48/49 (lungeing gear / nose net) inferred from
   position — marked "please verify caption" in rules 5.13 / 5.15.
