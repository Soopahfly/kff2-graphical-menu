#!/usr/bin/env python3
"""Rasterize the upright high-kick reference as a C64 one-bit icon.

Hand-traced polygons keep the pose and selected negative-space details readable
at 64x88 pixels. No photo pixels, antialiasing or external packages are used.
The silhouette is centred in an 8-column by 11-row VIC-II tile canvas.
"""
from pathlib import Path
from itertools import groupby
from make_font import read_font, glyph

WIDTH, HEIGHT = 64, 88
# Outline coordinates follow the reference supplied for this menu.
OUTLINE = [
 (370,66),(361,61),(359,53),(367,41),(380,38),(408,44),
 (413,51),(424,57),(426,66),(432,72),(434,82),(448,86),
 (449,91),(438,98),(422,100),(421,109),(423,142),(430,151),
 (447,158),(463,147),(475,146),(485,151),(492,174),(506,209),
 (514,247),(528,291),(549,346),(551,340),(567,326),(577,306),
 (580,319),(584,302),(591,308),(595,318),(599,310),(608,318),
 (617,329),(625,344),(631,372),(626,405),(614,429),(596,443),
 (592,467),(604,484),(615,494),(614,510),(604,525),(590,550),
 (580,580),(563,594),(552,609),(520,630),(492,637),(478,635),
 (477,678),(476,721),(479,763),(482,823),(468,845),(478,897),
 (505,912),(535,924),(539,932),(505,940),(451,943),(435,936),
 (438,920),(430,884),(419,845),(405,821),(398,791),(390,752),
 (395,706),(391,671),(380,628),(364,581),(355,552),(350,530),
 (350,517),(361,487),(363,429),(376,389),(378,319),(365,273),
 (371,225),(363,186),(363,172),(373,156)
]
# A few deliberate gaps distinguish limbs, face and gi at native resolution.
CUTOUTS = [
 [(444,187),(450,172),(461,180),(454,200),(454,225),(464,248),
  (473,271),(475,302),(461,277),(446,250),(439,225),(439,202)],
 [(378,164),(398,177),(416,181),(438,175),(426,185),(406,185),(389,179)],
 [(582,338),(598,342),(613,354),(618,373),(623,361),(619,342),
  (609,330),(603,337),(594,333),(590,340)],
 [(551,350),(570,370),(583,396),(592,421),(582,441),(573,456),
  (566,458),(573,447),(582,430),(584,418),(577,396),(568,377)],
 [(505,422),(519,426),(530,443),(535,463),(540,481),(553,490),
  (562,500),(566,517),(571,544),(578,551),(574,568),(566,578),
  (560,592),(553,588),(558,574),(559,558),(551,533),(543,515),
  (535,505),(526,503),(518,513),(508,533),(493,547),(482,554),
  (475,563),(471,575),(465,571),(466,555),(480,541),(492,523),
  (504,503),(513,488),(519,472),(515,449),(507,434)],
 [(482,384),(502,388),(521,383),(540,375),(543,362),(549,373),
  (546,385),(525,390),(500,392)],
 [(391,443),(402,456),(425,464),(407,464),(402,475),
  (397,469),(386,468),(394,459)],
 [(382,536),(389,564),(407,576),(415,601),(420,626),
  (454,620),(433,632),(416,633),(408,605),(402,583),(383,575)],
 [(429,807),(454,800),(470,793),(468,806),(453,814),(427,815),
  (450,809),(463,803),(445,805)],
 [(458,910),(466,919),(489,928),(515,931),(481,931),
  (470,927),(458,925),(447,932),(442,929),(448,922)],
 [(383,72),(393,78),(401,89),(413,93),(415,84),(408,74),
  (418,83),(420,94),(411,97),(397,92),(391,82)],
]

def inside(x, y, poly):
    result = False
    j = len(poly)-1
    for i,(xi,yi) in enumerate(poly):
        xj,yj=poly[j]
        if (yi>y)!=(yj>y) and x < (xj-xi)*(y-yi)/(yj-yi)+xi:
            result = not result
        j=i
    return result

# Slight horizontal emphasis keeps the limbs readable on a C64 display.
scale=86/905
scale_x=0.13
# Keep the defining limb/face gaps; omit small fabric details at this size.
CUTOUTS=[CUTOUTS[i] for i in (0,2,3,4,5)]
pixels=[]
for y in range(HEIGHT):
    row=[]
    for x in range(WIDTH):
        rx=(x+0.5-32)/scale_x+490
        ry=(y+0.5-1)/scale+38
        row.append(inside(rx,ry,OUTLINE) and not any(inside(rx,ry,p) for p in CUTOUTS))
    pixels.append(row)
values=[]
for cy in range(HEIGHT//8):
    for cx in range(WIDTH//8):
        for dy in range(8):
            value=0
            for dx in range(8):
                value=value*2+pixels[cy*8+dy][cx*8+dx]
            values.append(value)
assert len(values)==704

def pack(values):
    out=[]
    for value,group in groupby(values):
        length=len(list(group))
        while length:
            n=min(length,255)
            out.extend([n,value])
            length-=n
    out.append(0)
    # Verify a lossless round trip, including all blank pixels.
    restored=[]
    for i in range(0,len(out)-1,2): restored.extend([out[i+1]]*out[i])
    assert restored==list(values)
    return out

root=Path(__file__).resolve().parents[1]
font,offsets=read_font(root/'launcher/ui/charset.sed')
# cc65's default C64 character map stores a-z as PETSCII $41-$5a.
title_pixels=[[False]*288 for _ in range(16)]
xpos=0
for char in "kung fu flash 2":
    code=ord(char)-32 if 'a'<=char<='z' else ord(char)
    columns=glyph(font,offsets[code])
    for col in columns:
        for y in range(8):
            if col & (1<<y):
                for dx in (0,1):
                    for dy in (0,1): title_pixels[y*2+dy][xpos*2+dx]=True
        xpos+=1
    xpos+=1
assert xpos<=144
header=[]
for cy in range(2):
    for cx in range(36):
        for dy in range(8):
            value=0
            for dx in range(8): value=value*2+title_pixels[cy*8+dy][cx*8+dx]
            header.append(value)

path=root/'launcher/ui/kicker.h'
lines=['/* Lossless artwork streams. Generated by tools/make_kicker.py. */',
       '#ifndef KFF_KICKER_H','#define KFF_KICKER_H',
       '#define KICKER_TILE_ROWS 11', '#define KICKER_TILE_COLS 8',
       '#define TITLE_TILE_COLS 36']
for name,raw in [('kicker_rle',values),('title_rle',header)]:
    packed=pack(raw)
    lines.append(f'static const uint8_t {name}[{len(packed)}] = {{')
    lines += ['    '+', '.join(f'0x{n:02x}' for n in packed[i:i+16])+',' for i in range(0,len(packed),16)]
    lines.append('};')
    print(f'{name}: {len(raw)} -> {len(packed)} bytes')
lines += ['#endif','']
path.write_text('\n'.join(lines))
