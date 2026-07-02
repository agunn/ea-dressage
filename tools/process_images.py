#!/usr/bin/env python3
"""Export, trim, resize and compress images from the two source .docx files
into site/images/, and write the filename mappings the data build depends on.

Usage (from repo root):
    python tools/process_images.py

Annex images keep their original basename (image10.png -> image10.jpg).
National Rules images get an 'r5-' prefix to avoid collisions.
EMF images (Windows metafiles) require LibreOffice for conversion:
    soffice --headless --convert-to png --outdir <tmp> <file>.emf
"""
import os, io, json, zipfile, subprocess, tempfile
from PIL import Image, ImageChops

Image.MAX_IMAGE_PIXELS = None
OUT = 'site/images'


def trim(im):
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
        bg.paste(im, mask=im.split()[3])
        im = bg.convert('RGB')
    else:
        im = im.convert('RGB')
    diff = ImageChops.difference(im, Image.new('RGB', im.size, (255, 255, 255)))
    b = diff.getbbox()
    if b:
        l, t, r, btm = b
        p = 6
        im = im.crop((max(0, l - p), max(0, t - p),
                      min(im.width, r + p), min(im.height, btm + p)))
    return im


def convert_emf(data, name):
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, name)
        open(src, 'wb').write(data)
        subprocess.run(['soffice', '--headless', '--convert-to', 'png',
                        '--outdir', td, src], check=True, capture_output=True)
        return Image.open(src.rsplit('.', 1)[0] + '.png')


def process(docx_path, prefix, only=None):
    z = zipfile.ZipFile(docx_path)
    mapping = {}
    for info in z.infolist():
        if not info.filename.startswith('word/media/'):
            continue
        fname = os.path.basename(info.filename)
        if only and fname not in only:
            continue
        data = z.read(info)
        if fname.lower().endswith('.emf'):
            im = convert_emf(data, fname)
        else:
            im = Image.open(io.BytesIO(data))
        im = trim(im)
        if max(im.size) > 700:
            im.thumbnail((700, 700), Image.LANCZOS)
        outname = prefix + os.path.splitext(fname)[0] + '.jpg'
        im.save(os.path.join(OUT, outname), 'JPEG', quality=83, optimize=True)
        mapping[fname] = outname
    return mapping


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    # Only images actually referenced by items need exporting for the annex;
    # tools/raw_extract.json (from extract_annex.py) defines which.
    raw = json.load(open('tools/raw_extract.json'))
    used = set()
    for it in raw['items']:
        used.update(it['images'])
    for s in raw['specials']:
        used.update(s['images'])
    m1 = process('source-docs/equipment-annex-v23.docx', '', only=used)
    json.dump(m1, open('tools/img_mapping.json', 'w'))
    m2 = process('source-docs/national-rules-section-5.docx', 'r5-')
    json.dump(m2, open('tools/r5_img_mapping.json', 'w'))
    print(f'annex: {len(m1)} images, rules: {len(m2)} images -> {OUT}/')
