#!/usr/bin/env python3
"""Extract equipment items from the EA Dressage Equipment Annex .docx.

Usage (from repo root):
    python tools/extract_annex.py source-docs/equipment-annex-v23.docx

Outputs tools/raw_extract.json (items + special rows) and prints a summary.
The tick/cross status icons are identified by MD5 hash so a new version of
the document keeps working even if media file numbering changes.
"""
import sys, re, json, zipfile, hashlib, io
from lxml import etree

NS = {
 'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
 'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
 'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
 'v': 'urn:schemas-microsoft-com:vml',
}
# MD5 of the green tick / red cross PNGs used in Annex v23
TICK_MD5 = None   # resolved at runtime: the two most-reused small images
SECTIONS = {1: "Bit Rings & Cheeks", 2: "Bits & Mouthpieces", 3: "Bridles & Nosebands",
            4: "Competition Wear", 5: "Saddles & Stirrups",
            6: "Additional Equipment & Accessories", 7: "Horse Boots & Shoes", 8: "Spurs"}


def cell_text(tc):
    parts = []
    for p in tc.findall('.//w:p', NS):
        t = ''.join(n.text or '' for n in p.findall('.//w:t', NS))
        if t.strip():
            parts.append(t.strip())
    return '\n'.join(parts)


def cell_images(tc, rid2file):
    imgs = []
    for blip in tc.findall('.//a:blip', NS):
        rid = blip.get('{%s}embed' % NS['r'])
        if rid in rid2file:
            imgs.append(rid2file[rid])
    for im in tc.findall('.//v:imagedata', NS):
        rid = im.get('{%s}id' % NS['r'])
        if rid in rid2file:
            imgs.append(rid2file[rid])
    return imgs


def main(path):
    z = zipfile.ZipFile(path)
    doc = etree.parse(io.BytesIO(z.read('word/document.xml')))
    rels = z.read('word/_rels/document.xml.rels').decode()
    rid2file = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="media/([^"]+)"', rels))

    # Identify tick & cross: the two most frequently embedded images
    blips = re.findall(r'r:embed="(rId\d+)"',
                       z.read('word/document.xml').decode(errors='ignore'))
    from collections import Counter
    top = [rid2file[r] for r, _ in Counter(blips).most_common(2) if r in rid2file]
    # cross is used slightly more than tick in v23; disambiguate by pixel colour
    from PIL import Image
    def is_green(fname):
        im = Image.open(io.BytesIO(z.read('word/media/' + fname))).convert('RGB').resize((8, 8))
        px = list(im.getdata())
        g = sum(1 for r, gr, b in px if gr > r and gr > b)
        return g > len(px) / 4
    TICK = next(f for f in top if is_green(f))
    CROSS = next(f for f in top if f != TICK)
    print(f'tick={TICK} cross={CROSS}')

    items, specials, counter = [], [], {}
    current_section = None
    for tbl in doc.findall('.//w:tbl', NS):
        for tr in tbl.findall('./w:tr', NS):
            cells = tr.findall('./w:tc', NS)
            texts = [cell_text(tc) for tc in cells]
            imgs = [cell_images(tc, rid2file) for tc in cells]
            m = re.match(r'^Section\s+(\d)$', texts[0].strip()) if texts else None
            if m:
                current_section = int(m.group(1)); continue
            if not any(texts) and not any(i for i in imgs):
                continue
            if len(cells) < 3:
                specials.append({'section': current_section, 'text': ' '.join(texts),
                                 'images': [i for c in imgs for i in c]})
                continue
            status_imgs = imgs[2]
            equip = [i for c in imgs[:2] for i in c if i not in (TICK, CROSS)]
            status = ('prohibited' if CROSS in status_imgs else
                      'permitted' if TICK in status_imgs else 'review')
            counter[current_section] = counter.get(current_section, 0) + 1
            items.append({'id': f's{current_section}-{counter[current_section]:03d}',
                          'section': current_section,
                          'sectionName': SECTIONS.get(current_section),
                          'name': texts[0], 'notes': texts[1],
                          'statusText': texts[2], 'status': status, 'images': equip})

    json.dump({'items': items, 'specials': specials},
              open('tools/raw_extract.json', 'w'), indent=1)
    print(f'{len(items)} items, {len(specials)} special rows -> tools/raw_extract.json')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'source-docs/equipment-annex-v23.docx')
