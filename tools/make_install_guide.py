# Generates the install-guide handout PDF (site/install-guide.pdf + Downloads copy).
# Usage: python3 make_install_guide.py   (needs: pip install reportlab pillow qrcode)
import qrcode, os, tempfile
QR_PATH = os.path.join(tempfile.gettempdir(), "ea-qr.png")
qrcode.make("https://ea-dressage.eq-au.workers.dev/", box_size=10, border=2).save(QR_PATH)
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from PIL import Image

NAVY = HexColor("#002942")
PAPER = HexColor("#F1EFE7")
INK = HexColor("#22271F")
MUTED = HexColor("#5E6558")

S = None  # QR path handled above
IMG = "/Volumes/web/ea-dressage/site/images/"
OUT = "/Users/ag/Downloads/EA-Dressage-App-Install.pdf"
URL = "ea-dressage.eq-au.workers.dev"

W, H = A4
c = canvas.Canvas(OUT, pagesize=A4)

# ---------- header band ----------
BAND_H = 104
c.setFillColor(NAVY)
c.rect(0, H - BAND_H, W, BAND_H, stroke=0, fill=1)

def logo(path, x_centre, height, y_centre):
    im = Image.open(path)
    w = im.width * height / im.height
    c.drawImage(path, x_centre - w/2, y_centre - height/2, width=w, height=height, mask='auto')

mid = H - BAND_H/2
logo(IMG + "ea-logo-white.png", 74, 76, mid)
logo(IMG + "ea-dressage-logo-white.png", W - 74, 76, mid)

c.setFillColor(white)
c.setFont("Helvetica", 11.5)
c.drawCentredString(W/2, H - 34, "Equestrian Australia")
c.setFont("Helvetica-Bold", 18)
c.drawCentredString(W/2, H - 55, "Dressage Rules, Equipment and Tests")
c.setFont("Helvetica", 11)
c.drawCentredString(W/2, H - 74, "Install the free reference app on your phone or tablet")
c.setFont("Helvetica-Bold", 11.5)
c.drawCentredString(W/2, H - 92, URL)

# ---------- QR + intro row ----------
MARGIN = 36
qr_size = 92
qy = H - BAND_H - 18 - qr_size
c.setFillColor(PAPER)
c.roundRect(MARGIN, qy - 12, W - MARGIN*2, qr_size + 24, 10, stroke=0, fill=1)
c.drawImage(QR_PATH, MARGIN + 14, qy, width=qr_size, height=qr_size)
tx = MARGIN + 14 + qr_size + 18
c.setFillColor(NAVY)
c.setFont("Helvetica-Bold", 13)
c.drawString(tx, qy + qr_size - 20, "Scan to open — then install below")
c.setFillColor(INK)
c.setFont("Helvetica", 10.5)
for i, ln in enumerate([
    "This is not an App Store or Play Store download — it is a web page you",
    "add to your home screen. It then opens full-screen like an app and works",
    "offline once loaded: every rule and photo stored on your device."]):
    c.drawString(tx, qy + qr_size - 40 - i*14, ln)
c.setFont("Helvetica-Bold", 10.5)
c.setFillColor(NAVY)
c.drawString(tx, qy + 4, "https://" + URL + "/")

# ---------- device panels ----------
PANEL_TOP = qy - 30
PANEL_H = 268
GAP = 16
panel_w = (W - MARGIN*2 - GAP) / 2

def panel(x, title, sub, steps, foot=None):
    c.setFillColor(PAPER)
    c.roundRect(x, PANEL_TOP - PANEL_H, panel_w, PANEL_H, 10, stroke=0, fill=1)
    tx = x + 14
    ty = PANEL_TOP - 26
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(tx, ty, title)
    c.setFillColor(MUTED)
    c.setFont("Helvetica-BoldOblique", 9.5)
    c.drawString(tx, ty - 14, sub)
    yy = ty - 38
    for n, lines in enumerate(steps, 1):
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(tx, yy, f"{n}.")
        c.setFillColor(INK)
        c.setFont("Helvetica", 10)
        for i, ln in enumerate(lines):
            c.drawString(tx + 15, yy - i*12.5, ln)
        yy -= 12.5*len(lines) + 7.5
    if foot:
        c.setFillColor(MUTED)
        c.setFont("Helvetica-Oblique", 9)
        for i, ln in enumerate(foot):
            c.drawString(tx, PANEL_TOP - PANEL_H + 24 - i*11.5, ln)

panel(MARGIN, "iPhone / iPad", "must use the Safari browser",
      [["Open Safari and go to the address", "above (or scan the QR code)."],
       ["Tap Share (square with an up arrow) —", "bottom toolbar on iPhone; top-right", "next to the address bar on iPad."],
       ["Find “Add to Home Screen”.", "Don't see it? Scroll down, or tap", "“View More” to reveal it."],
       ["Leave “Open as Web App” switched on", "(the default), then tap Add (top-right)."]],
      ["The option only exists in Safari, and often sits", "further down the Share sheet — keep scrolling."])

panel(MARGIN + panel_w + GAP, "Android phone / tablet", "use the Chrome browser",
      [["Open Chrome and go to the address", "above (or scan the QR code)."],
       ["If an “Install app” banner appears,", "tap it — done. Otherwise continue."],
       ["Tap the three-dot menu (top right)."],
       ["Tap “Add to Home screen” or", "“Install app”, then confirm."]],
      ["Samsung Internet works too — look for", "Add page to > Home screen."])

# ---------- notes ----------
ny = PANEL_TOP - PANEL_H - 30
def note(title, lines):
    global ny
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11.5)
    c.drawString(MARGIN, ny, title)
    c.setFillColor(INK)
    c.setFont("Helvetica", 10)
    for i, ln in enumerate(lines):
        c.drawString(MARGIN, ny - 15 - i*13, ln)
    ny -= 15 + 13*len(lines) + 14

note("First launch — let it pack its bags",
     ["Stay on Wi-Fi for a minute while every rule image downloads. The line under the filter buttons reads",
      "“offline images ready” when finished. From then on it works fully offline — even with no signal at the arena."])

note("Updates take care of themselves",
     ["When anything changes, the app shows “New version available — tap to update”. One tap and you're current."])

note("What's inside",
     ["Equipment — searchable permitted / prohibited / conditional gear with photos.  Equipment Rules — the rule text.",
      "Dressage Tests — every EA and Para test sheet.  Dressage Rulebook — the official National Dressage Rules.",
      "(Tests and Rulebook open on the EA website, so those two need an internet connection.)"])

# ---------- footer ----------
c.setFillColor(NAVY)
c.rect(0, 0, W, 30, stroke=0, fill=1)
c.setFillColor(white)
c.setFont("Helvetica-Bold", 10.5)
c.drawCentredString(W/2, 10.5, URL)

c.save()
print("wrote", OUT)

import shutil
shutil.copyfile(OUT, "/Volumes/web/ea-dressage/site/install-guide.pdf")
print("copied to site/install-guide.pdf")
