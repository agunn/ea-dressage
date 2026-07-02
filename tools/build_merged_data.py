import json, re

annex = json.load(open('tools/raw_extract.json'))
imap = json.load(open('tools/img_mapping.json'))
r5 = json.load(open('tools/r5_img_mapping.json'))
R = lambda f: r5[f]

# ---------------- annex items (same enrichment as v1) ----------------
def clean(t):
    t = t.replace('Top hatsare', 'Top hats are')
    return re.sub(r'\s+', ' ', t.replace('\n', ' ')).strip()

items = []
counter = {}
for it in annex['items']:
    st = clean(it['statusText'])
    penalty = 'Elimination' if re.search(r'elimination', st, re.I) else ('Minus 0.5%' if re.search(r'minus\s*0\.5', st, re.I) else None)
    mu = re.search(r'Updated\s+([A-Za-z]+\s+\d{4})', st)
    cond = re.sub(r'Updated\s+[A-Za-z]+\s+\d{4}', '', re.sub(r'Minus\s*0\.5%?( for [^.]*)?', '', re.sub(r'Elimination', '', st, flags=re.I), flags=re.I)).strip(' .;,-')
    lines = [l.strip() for l in it['name'].split('\n') if l.strip()]
    title = clean(lines[0]) if lines else '(untitled)'
    notes = clean(it['notes'])
    if 'INSERT' in notes.upper(): notes = ''
    status = it['status']
    scope = 'warm-up' if re.search(r'warm[\s-]?up', st + ' ' + title + ' ' + notes, re.I) else 'competition'
    if status == 'review' or re.search(r'exemption', st, re.I): status = 'conditional'
    items.append({'id': it['id'], 'section': it['section'], 'sectionName': it['sectionName'],
        'title': title, 'description': clean(' '.join(lines[1:])), 'notes': notes,
        'status': status, 'penalty': penalty, 'condition': cond or None, 'scope': scope,
        'updated': mu.group(1) if mu else None,
        'images': [imap[i] for i in it['images'] if i in imap],
        'source': 'annex', 'ruleRef': None})

# ---------------- enrich annex items with rulebook references ----------------
ENRICH = {  # title-substring (case-insens) -> (ruleRef, extra note or None)
 'bit guards': ('5.12', None),
 'blinkers of any type': ('5.12', None),
 'electronic devices / headsets': ('5.12', None),
 'electronic communication devices': ('5.12', None),
 'hoof boots': ('5.12 / 5.16', 'Removable over-boots (e.g. Easy Boot, Scoot Boot) are permitted in the warm-up area but not past the gear check or into the competition surrounds or arena.'),
 'running martingales': ('5.12', None),
 'nose net': ('5.15', 'Written EADC approval required (application with veterinary letter). Approval letter must be produced at gear check on request. Net must be transparent and must not cover the mouth or bit.'),
 'ear bonnet/hoods': ('5.14', 'Must be correct size and not cover the eyes; sound-reducing material is allowed but no additional insulation or ear plugs. Officials may request removal after the test for checking.'),
 'magnetic stirrups': ('5.10.1 / 5.12', 'Lock-in stirrups and stirrup tie-downs are likewise not permitted.'),
 'riding boots must have heels': ('5.3', 'All boots must have heels and smooth soles (or only lightly indented tread). Unsafe boots will entail elimination.'),
 'boots or bandages that cover the hoof': ('5.16 / 5.17', None),
 'body bandage': ('5.17', 'Any protective skin covering (plaster/tape/belly band/towel), broken skin or not, is strictly forbidden when the horse is under saddle at an event.'),
 'exercise sheets': ('5.12', None),
 'coloured piping is permitted': ('5.10', None),
}
for it in items:
    tl = it['title'].lower()
    for key, (ref, note) in ENRICH.items():
        if key in tl:
            it['ruleRef'] = ref
            if note:
                it['notes'] = (it['notes'] + ' ' if it['notes'] else '') + note
            break

# ---------------- new items from National Rules 5.12 & gear check ----------------
def NI(section, title, status, cond=None, penalty=None, scope='competition', ref='5.12', notes='', images=None):
    counter[section] = counter.get(section, 0) + 1
    names = {1:'Bit Rings & Cheeks',2:'Bits & Mouthpieces',3:'Bridles & Nosebands',4:'Competition Wear',
             5:'Saddles & Stirrups',6:'Additional Equipment & Accessories',7:'Horse Boots & Shoes',8:'Spurs'}
    return {'id': f'r{section}-{counter[section]:03d}', 'section': section, 'sectionName': names[section],
            'title': title, 'description': '', 'notes': notes, 'status': status, 'penalty': penalty,
            'condition': cond, 'scope': scope, 'updated': None, 'images': images or [],
            'source': 'rules', 'ruleRef': ref}

new_items = [
 NI(3,'Bearing reins (e.g. chambon, deGogue)','prohibited',penalty='Elimination',notes='Not permitted anywhere at an event or venue.'),
 NI(3,'Running reins (e.g. chambon, deGogue)','prohibited',penalty='Elimination',notes='Not permitted anywhere at an event or venue.'),
 NI(3,'Bitless bridles (e.g. hackamores)','prohibited',penalty='Elimination',ref='5.11 / 5.12',notes='Bitless bridles are not permitted; not permitted anywhere at an event or venue.'),
 NI(3,'Grass reins','prohibited',penalty='Elimination'),
 NI(3,'Snaffle bridle','permitted',cond='Permitted at all levels. Compulsory in all tests up to and including Elementary; optional at Medium and above.',ref='5.11.3 / 5.12'),
 NI(3,'Double bridle','conditional',cond='Medium level & above, and 7yo Young Horse competitions. Cavesson noseband compulsory (lower flash strap not permitted). A double bridle with a pelham bit is not permitted in any test.',ref='5.11.4 / 5.12'),
 NI(6,'Crystal mane bands','prohibited',penalty='Elimination'),
 NI(6,'Decoration of the horse (ribbons, flowers, glitter, etc.)','prohibited',penalty='Elimination',cond='Exception: a red ribbon in the tail to indicate a horse that kicks.'),
 NI(6,'Ear plugs','conditional',cond='Permitted in presentations/prize-giving only.'),
 NI(6,'False tail / tail extensions','permitted',cond='No metal parts (except hooks and eyelets) and no added weight — otherwise elimination. For FEI-sanctioned events refer to FEI Art 428.4.'),
 NI(6,'Foregirths','permitted',cond='All levels.'),
 NI(6,'Breastplates','permitted',cond='Up to and including Medium level, with a snaffle bridle only.'),
 NI(6,'Monkey grip','permitted',cond='All levels.'),
 NI(6,'Neck straps','permitted',cond='All levels, for safety purposes only.'),
 NI(6,'Nasal strips','prohibited',penalty='Elimination'),
 NI(6,'Tongue ties','prohibited',penalty='Elimination'),
 NI(6,'Whips','conditional',scope='warm-up',ref='5.6 / 5.12',cond='One whip only: horses max 1.20 m, ponies max 1.00 m (tassel included). Permitted in warm-up and in tests up to and including Advanced. Not to be carried at FEI-level tests at State and Australian Championships: 0.5% per judge if carried circling or entering the arena; elimination if carried in the test for more than 3 movements. Lungeing whip permitted when lungeing.'),
 NI(6,'Side reins & lungeing cavesson','conditional',cond='Lungeing only. Only one lunge rein; lunge line/side reins must not attach to a curb bit. Lungeing a mounted rider is not permitted anywhere at the event.',ref='5.13'),
 NI(6,'Crupper','permitted',cond='Ponies only (not in Young Horse competitions).',ref='5.10 / 5.19'),
 NI(6,'Horse identification numbers','permitted',cond='Compulsory: one on each side of the bridle or saddlecloth, clearly visible, whenever the horse is out of the stable.',ref='5.19'),
 NI(6,'Equipment against the intent and general principles of dressage','prohibited',penalty='Elimination',cond='As determined by the Ground Jury, Technical Delegate or Chief Steward.'),
 NI(7,'Boots, bell boots and bandages (leg protection)','conditional',scope='warm-up',ref='5.12 / 5.17',cond='Permitted in warm-up only. 0.5% from each judge if worn in the space around the arena; 0.5% from each judge if worn in the arena.'),
 NI(5,'Saddle covers (sheepskin, rain covers, etc.)','conditional',scope='warm-up',cond='Warm-up area only.'),
 NI(5,'Lock-in stirrups & stirrup tie-downs','prohibited',penalty='Elimination',ref='5.10.1 / 5.12'),
]
items += new_items

# ---------------- rules topics ----------------
P = lambda *xs: list(xs)
rules = [
 {'id':'r5-1','ref':'5.1','title':'Compulsory dress by level','body':P(
   'Up to Medium level: safety helmet; short coat (riders may ride without jackets if overheated); long, short-sleeved or sleeveless shirt with a stock, tie or ratcatcher securely pinned; stock/tie in white, off-white, pale colour or coat colour (coloured trim permitted); white or light-coloured breeches/jodhpurs (seat may be dark); long boots or jodhpur boots in black, brown or coat colour, with or without gaiters; gloves white/off-white preferred or same colour as jacket.',
   'Advanced level: as above, but a short coat or tailcoat may be worn.',
   'FEI levels (Prix St Georges – Grand Prix): short coat or tailcoat, colour per FEI rules; long boots in black or coat colour; white or off-white breeches. For non-CDI competitions riders may ride without jackets if overheated; see FEI rules for CDIs.',
   'Optional at all levels: military/police personnel may wear service dress with a safety helmet; spurs, whip, monkey grip and back protector are optional.',
   'Incorrect dress for the level incurs a technical fault of 0.5% from each judge; "not permitted" items entail elimination (Annex E).'),'images':[]},
 {'id':'r5-2','ref':'5.2','title':'Headgear & helmets','body':P(
   'Any person mounted must wear an approved safety helmet with the retaining harness secured and fastened — an unfastened harness entails elimination.',
   'Approved standards (must also have passed quality testing): AS/NZS 3838 (2006+) SAI Global marked; ARB HS 2012 SAI Global marked; ASTM F1163 (2004a+) SEI marked or SNELL E2001; PAS 015 (1998 or 2011) BSI Kitemarked; CE mark referencing EN1384:2023 or VG1 with InspecIC or BSI Kitemark. VG1 without a kitemark allowed until 1 January 2027.',
   'Helmets must be black or coat colour; a reflective strip (not the entire helmet) is permitted.',
   'All helmets must carry a current visible EA Helmet Tag — failure may entail a recorded warning.',
   'No camera of any type may be attached to the helmet, rider, saddlery or horse.'),
  'images':[{'src':R('image1.png'),'cap':'BSI Kitemark'},{'src':R('image2.jpeg'),'cap':'SAI Global mark'},{'src':R('image3.jpeg'),'cap':'SEI mark'}]},
 {'id':'r5-3','ref':'5.3','title':'Footwear','body':P(
   'All riders must wear riding boots when mounted. All boots must have heels and smooth soles (or only lightly indented tread); unsafe boots entail elimination.',
   'The exposed side of long boots must be smooth; a discrete outside zipper and front lace closers are permitted.',
   'Boots may be black, brown or jacket colour, except top boots/gaiters with a decorative or hunting top.',
   'Decorative features on the top section of top boots, gaiters or hunting tops are permitted in the same colour scheme as the boot or matching the jacket.'),'images':[]},
 {'id':'r5-4','ref':'5.4','title':'Gaiters','body':P(
   'Gaiters may be worn up to and including Advanced (including Young Horse events), with a short coat only, and only with approved short boots.',
   'The exposed side must be full grain leather. Black, brown or boot colour; decorative or hunting tops permitted.'),'images':[]},
 {'id':'r5-5','ref':'5.5','title':'Spurs — specifications','body':P(
   'Spurs are optional for all competitors and must be an identical pair, made of metal or hard plastic.',
   'A curved or straight shank must point directly back from the centre of the spur; the tip must not point up or inwards. Swan neck spurs are permitted. The arms must be smooth.',
   'Disc rowels must be blunt, smooth and free to rotate, in a vertical or horizontal plane. Daisy rowels, tines, notched or serrated edges are not permitted.',
   'Soft touch spurs (rolling ball, either plane), metal spurs with hard plastic knobs, dummy spurs (no shank) and Impulse spurs are permitted.',
   'Pony riders (any age): spurs max 4.0 cm measured from boot to tip (FEI CDIP: max 3.5 cm, no rowels). No maximum length for horse riders.',
   'Non-compliant or incorrect spurs entail elimination.'),'images':[]},
 {'id':'r5-6','ref':'5.6','title':'Whips','body':P(
   'Riders of horses may carry one whip up to 1.20 m; ponies up to 1.00 m (tassel included in the length).',
   'Permitted in exercise and warm-up areas, in all tests up to and including Advanced at all events, and anywhere on the ground when riding or leading.',
   'Only the nominated rider (or groom) may use a whip in connection with training when riding, walking in hand, leading or lunging (lunge whip allowed).',
   'Whips are not to be carried at FEI-level tests at State and Australian Championships (incl. AOR, Youth and Pony Championships); for Young Horse competitions see rule 9.1.',
   'At those championships: circling the arena with a whip = 0.5% per judge; entering the arena = 0.5% per judge; carrying it for more than 3 movements = elimination.',
   'Incorrect length or use entails elimination (Annex E).'),'images':[]},
 {'id':'r5-7','ref':'5.7','title':'Shirts & neck wear','body':P(
   'The shirt should be tucked in; visible parts should be white, pale or coordinating. Patterns on body/sleeves are permitted even without a coat.',
   'Collar: ratcatcher or business-style (a tie must be worn with the latter). Long, short, capped sleeve or sleeveless permitted. A waistcoat may be worn.',
   'Stocks: white, off-white, pale or coat colour; piping trim permitted.'),'images':[]},
 {'id':'r5-8','ref':'5.8','title':'Jackets & coats','body':P(
   'Preliminary to Advanced: a short jacket or coat (may be double breasted); cutaway coats/mini tails permitted if cut straight across the back; colour solid or very faint/tweed pattern.',
   'Advanced and FEI levels: tailcoat optional, jackets permitted; tailcoats may be worn with a snaffle.',
   'FEI and National levels: any solid colour; wide contrast stripes and multi-coloured jackets not permitted. Piping accents and matching colour sections on collars/pocket flaps permitted.',
   'For all EA levels and non-CDI FEI levels, a coat is optional if the rider feels overheated; waistcoats/fitted vests permitted with or without the coat.',
   'Back protectors may be worn under or over the coat. A non-flapping rain jacket (clear or coat-coloured) may be worn over the coat in wet weather.'),'images':[]},
 {'id':'r5-9','ref':'5.9','title':'Pocket badges & advertising','body':P(
   'Pocket badges are issued for specific occasions; normally one badge is worn, with a second permitted when riding as a representative. Riders who have represented Australia at a World Championships or Olympic Games may wear the Australian flag pocket badge at all times.',
   'Badge dimensions and advertising/sponsor logo rules: EA General Regulations, Article 135 (sponsor pocket badges max 80 cm² at breast height; saddlecloth badges max 200 cm² each side).'),'images':[]},
 {'id':'r5-10','ref':'5.10','title':'Saddles, saddlecloths & stirrups','body':P(
   'A fully mounted dressage-type saddle (including all-purpose), traditional or treeless, is compulsory, with or without a saddlecloth. In Participation events only, jumping saddles and English side saddles are permitted.',
   'All parts of the saddle black and/or brown only; coloured piping around the edges permitted; the back of the cantle may reflect shades of the saddle. A non-compliant saddle entails elimination.',
   'Saddlecloths may be square or shaped — white preferred, pale colours permitted, coloured piping permitted. A sheepskin/fleece girth cover is permitted. A crupper may be worn by ponies.',
   'Stirrups must be black, silver, gold or boot colour. All safety stirrups, toe stoppers and open branches are permitted. The stirrup iron and leather must hang freely from the bar on the outside of the flap; the rider must not tie any part of their body to the saddle or stirrup.',
   'Lock-in stirrups, stirrup tie-downs and magnetised stirrups are not permitted.'),
  'images':[{'src':R('image4.png'),'cap':'Example of a permitted dressage saddle'}]},
 {'id':'r5-11','ref':'5.11','title':'Bridles, nosebands & bits — construction rules','body':P(
   'Bridles must be black or brown (coloured accent/piping permitted). Except for buckles and padding, the headstall and noseband must be entirely leather or leather-like; nylon reinforcement must not contact the horse. Elastic inserts only in crown piece and cheek pieces, not contacting horse or bit.',
   'Padding under bridles must be discreet, underside only. A browband is required. The crown piece must lie immediately behind the poll (may extend forward, never behind the skull).',
   'A throat latch is required except when a combined noseband or Micklem bridle is used.',
   'Reins: black or brown; a continuous uninterrupted strap from bit to hand; each bit on a separate rein; leather, cotton or synthetic (not rope); no additions, attachments, elastic inserts or loops — martingale stoppers and continental reins with billets are permitted.',
   'A noseband is compulsory and only one may be worn (two nosebands = elimination; non-approved noseband = elimination). Nosebands must never be so tight as to harm the horse. Padding (incl. sheepskin) under the noseband is permitted if it does not affect tightness.',
   'Bits must be smooth with a solid surface, rounded (not ridged, sharp or corrugated); metal, rigid plastic or durable synthetic, optionally covered in rubber/latex; no mechanical restraint on the tongue; twisted and wire bits not permitted. Bit measurement tolerance ±1 mm.',
   'Snaffle: min mouthpiece diameter 10 mm ponies / 12 mm horses (14 mm Young Horse). Up to two joints; bushing/coupling centre link must be solid (roller allowed) and must not act as a tongue plate. Tongue-relief deviation: max height 30 mm, min width 30 mm. Forward-curved bits permitted (not with hanging cheeks; must have a joint).',
   'Double bridle: bridoon + curb with curb chain (metal, leather or combination); pelham not permitted. Compulsory cavesson noseband. Bridoon min 10 mm, one or two joints, no multiple rollers, no flexible rubber bits. Curb: min 12 mm, lever arm max 10 cm (measured at uppermost position for sliding mouthpieces), upper cheek not longer than lower, straight or S-shaped cheeks, rotating lever arms allowed; curb chain must lie flat and never harm the horse. Optional: lip strap, leather or rubber curb chain cover.',
   'Bitless bridles and one-eared bridles are not permitted (elimination).'),'images':[]},
 {'id':'r5-13','ref':'5.13','title':'Lungeing equipment','body':P(
   'Lungeing cavessons are permitted. Only one lunge rein (no long reining). Snaffle with cavesson, dropped, Mexican or flash noseband; running martingale (snaffle only); boots and bandages permitted.',
   'Double bridles permitted, but the lunge line or side reins must not attach to the curb bit. The horse must be attached to a lunge line and wear a bit or lungeing cavesson.',
   'Lungeing a mounted rider is not permitted anywhere at the event. Ear hoods and a lungeing whip are permitted.'),
  'images':[{'src':R('image48.png'),'cap':'Lungeing gear example (please verify caption)'}]},
 {'id':'r5-14','ref':'5.14','title':'Ear hoods','body':P(
   'Permitted if correctly sized and not covering the eyes. Sound-reducing material is allowed, but no additional insulation beyond manufactured state and no ear plugs.',
   'May not be attached to the noseband. Officials may request removal after the test for checking.'),'images':[]},
 {'id':'r5-15','ref':'5.15','title':'Nose nets','body':P(
   'Only permitted with written EADC approval, case by case. Application requires a supporting veterinary letter with the horse\u2019s registration details.',
   'If approved: a copy of the approval letter must accompany entries, be available on request to gear checkers/stewards/judges, and is copied to the relevant SDA.',
   'The net must be transparent and must not cover the mouth or bit.'),
  'images':[{'src':R('image49.png'),'cap':'Nose net example (please verify caption)'}]},
 {'id':'r5-16','ref':'5.16','title':'Over-boots, hoof boots & shoes','body':P(
   'Shoeing is not mandatory. Removable over-boots/hoof boots are permitted in the warm-up area but not past the gear check or into competition surrounds or arena.',
   'Glued-on shoes are permitted if made of clear material with the hoof visible — bulbs of the heel and full circumference of the coronary band must be clearly visible.'),'images':[]},
 {'id':'r5-17','ref':'5.17','title':'Protective coverings, boots & bandages','body':P(
   'Boots and/or bandages are permitted in warm-up but not in the competition arena (technical faults per rule 5.12).',
   'Any protective skin covering (plaster, tape, belly band, towel), whether the skin is broken or not, is strictly forbidden when the horse is under saddle at an event — elimination.'),'images':[]},
 {'id':'r5-18','ref':'5.18','title':'Exemption cards & riders with a disability','body':P(
   'EA members with a diagnosed, medically documented disability who are not eligible (or do not wish to be classified) for Para-Equestrian may apply for exemptions allowing special equipment or allowances that are reasonable, necessary, safe and provide no competitive advantage.',
   'Applications are assessed by the EA Exemption Committee (PE classifiers, experienced judges and coaches). Approved riders receive an EA Exemption Card (valid up to 4 years) listing the permitted exemptions — a copy goes to the OC at entry and should be carried throughout the competition.',
   'Test calling in Young Horse competitions is permitted with the appropriate exemption card; if caller exemptions are granted, no headset is permitted. Forms: equestrian.org.au/content/exemption-cards-dressage.'),'images':[]},
]

# ---------------- illustration galleries (5.20 / 5.21) ----------------
def G(cap, *files): return {'cap': cap, 'srcs': [R(f) for f in files]}
gal_bits = {
 'id':'g5-20','ref':'5.20','title':'Permitted bits — official illustrations','groups':[
  {'name':'Snaffles','entries':[
    G('1. Loose ring snaffle','image5.png'),
    G('2–4. Snaffle with jointed mouthpiece — middle piece must be rounded (egg butt sides also permitted)','image6.png','image7.png','image8.png'),
    G('5. Egg butt snaffle','image9.png'),
    G('6. Racing snaffle (D-ring)','image10.png'),
    G('7. Loose-ring snaffle with cheeks (Fulmer) — keepers permitted','image11.png'),
    G('8. Egg-butt snaffle with cheeks — keepers permitted','image12.png'),
    G('9. Snaffle with upper cheeks only','image13.png'),
    G('10. Hanging cheek snaffle (single or double joint only)','image14.png'),
    G('11. Straight bar snaffle — also permitted with mullen mouth and egg butt rings','image15.png'),
    G('12. Snaffle with rotating mouthpiece','image16.png'),
    G('13. Snaffle with rotating middle piece','image17.jpeg'),
    G('14. Rotary bit, single jointed','image18.jpeg'),
    G('15. Rotary bit, double jointed','image19.png'),
    G('16. Rotary bit with rotating middle piece and looped rings','image20.png'),
    G('Measurement for tongue-relief deviation (rotating mouthpiece): max height 30 mm, min width 30 mm','image21.png'),
  ]},
  {'name':'Bridoons (double bridle)','entries':[
    G('17. Loose-ring bridoon','image5.png'),
    G('18–19. Loose-ring bridoon with jointed mouthpiece — middle piece rounded','image6.png','image7.png','image8.png'),
    G('20. Bridoon with rotating middle piece','image17.jpeg'),
    G('21. Bridoon with hanging cheeks (Baucher) — single or double joint only','image22.png'),
    G('22. Egg-butt bridoon','image9.png'),
  ]},
  {'name':'Curbs (curb chain hooks may be fixed)','entries':[
    G('23. Half-moon curb; half-moon curb with straight cheeks and port; Weymouth (port and sliding mouthpiece); rotating lever arm also permitted','image23.png','image24.png','image25.png','image26.png','image27.png','image28.png'),
    G('24. Variation of the above','image29.png'),
    G('25. Curb bit with S-curved cheeks','image30.png','image31.png','image32.png','image33.png'),
    G('26. Length of lever arm limited to 10 cm','image34.png'),
    G('27. Lip strap','image35.png'),
    G('28. Leather cover for curb chain','image36.png'),
    G('29. Rubber or sheepskin cover for curb chain','image37.png'),
    G('30. Curb chain — metal, leather or combination (rule 5.11.2)','image38.png'),
    G('31. Curb chain (rule 5.11.4.2)','image39.png','image40.jpeg'),
  ]},
 ]}
gal_nose = {
 'id':'g5-21','ref':'5.21','title':'Permitted nosebands — official illustrations','groups':[
  {'name':'Snaffle bridle — one (only) of the following is compulsory','entries':[
    G('1. Dropped noseband','image41.png'),
    G('2. Cavesson noseband','image42.png'),
    G('3. Flash noseband (Hanoverian)','image43.png'),
    G('4. Crossed noseband (Grackle or Mexican) — not permitted in Young Horse competitions','image44.png'),
    G('5. Combined noseband — no throat lash. With a double bridle the lower strap is not permitted','image45.png'),
    G('6. Micklem bridle','image46.png'),
  ]},
  {'name':'Double bridle','entries':[
    G('Double bridle with cavesson noseband, bridoon and curb with curb chain. Nosebands 1, 3, 4 or 6 are not permitted with a double bridle','image47.png'),
  ]},
 ]}

# ---------------- assemble ----------------
policy_src = None
# rebuild policy + meta identical to v1
exec(open('tools/policy_block.py').read())  # defines policy, meta

sections = [{'id':s,'name':n} for s,n in sorted({(i['section'], i['sectionName']) for i in items})]
data = {'meta': meta, 'sections': sections, 'items': items, 'policy': policy,
        'rules': rules, 'galleries': [gal_bits, gal_nose],
        'conflicts': [
          {'topic':'Throat lash','annex':'Annex banner: “ALL BRIDLES MUST HAVE A THROAT LASH”; Micklem bridles assessed on whether the upper strap is fitted as a throat lash.',
           'rules':'National Rules 5.11: a throat latch is required EXCEPT when the combined noseband or Micklem bridle is used.'}
        ]}
with open('site/data.js','w') as f:
    f.write('const EA_DATA = ' + json.dumps(data, indent=1) + ';\n')
print('items:', len(items), '| rules topics:', len(rules), '| galleries:', 2)
from collections import Counter
print(Counter(i['status'] for i in items))
print(Counter(i['source'] for i in items))
