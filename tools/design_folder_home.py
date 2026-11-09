#!/usr/bin/env python3
"""Generate a C64-native folder Home bitmap, compressed assets and pixel preview.

Uses the project's EF3 proportional font and exact 320x200 hi-res bitmap layout.
Preview is a layout render, not a VICE screenshot. Pillow only exports the PNG.
"""
from pathlib import Path
from itertools import groupby
import json
import re
from PIL import Image
from make_font import read_font, glyph

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'experiments/folder-home'
SPEC = json.loads((OUT / 'design.json').read_text())
FONT, OFFSETS = read_font(ROOT / 'launcher/ui/charset.sed')
BITMAP = bytearray(8000)
PALETTE = ['000000','ffffff','813338','75cec8','8e3c97','56ac4d','2e2c9b','edf171',
           '8e5029','553800','c46c71','4a4a4a','7b7b7b','a9ff9f','706deb','b2b2b2']


def pixel(x, y):
    assert 0 <= x < 320 and 0 <= y < 200, (x,y)
    BITMAP[(y//8)*320 + (x//8)*8 + y%8] |= 128 >> (x%8)


def text(x, row, value):
    x *= 8
    for char in value:
        code = ord(char)-32 if 'a' <= char <= 'z' else ord(char)
        cols = glyph(FONT, OFFSETS[code])
        for col in cols:
            for y in range(8):
                if col & (1 << y): pixel(x,row*8+y)
            x += 1
        x += 1
    assert x <= 304, (value,x)


def rect(x,y,w,h):
    for px in range(x,x+w): pixel(px,y);pixel(px,y+h-1)
    for py in range(y,y+h): pixel(x,py);pixel(x+w-1,py)


def line(x0,y0,x1,y1):
    dx=abs(x1-x0);sx=1 if x0<x1 else -1
    dy=-abs(y1-y0);sy=1 if y0<y1 else -1
    err=dx+dy
    while True:
        if 0<=x0<320 and 0<=y0<200:pixel(x0,y0)
        if x0==x1 and y0==y1:break
        e=2*err
        if e>=dy:err+=dy;x0+=sx
        if e<=dx:err+=dx;y0+=sy


def clear(x,y,w,h):
    assert x%8==y%8==w%8==h%8==0
    for row in range(y//8,(y+h)//8):
        BITMAP[row*320+x:row*320+x+w]=bytes(w)


ICONS = [
    ["      ######      ","   ############   ","  ##############  "," ################ ",
     " #### ###### #### "," ###   ####   ### "," #### ########### "," ################ ",
     " ######    ###### "," #####      ##### "," ####        #### "," ###          ### "],
    ["          ##  ##  ","         ###  ### ","         ###  ### ","         ######## ",
     "          ######  ","         ######   ","        ####      ","       ####       ",
     "      ####        ","     ####         ","    ####          ","   ####           ",
     "  ####            ","  ###             "],
    [" ################ "," ################ "," ###         #### "," ###      ## #### ",
     " ###      ## #### "," ###         #### "," ################ "," ################ ",
     " ####        #### "," ####        #### "," ####        #### "," ####        #### ",
     " ####        #### "," ################ "],
    ["        ##        ","       ####       ","       ####       ","      ######      ",
     " ################ ","  ##############  ","   ############   ","    ##########    ",
     "    ##########    ","   ############   ","   #####  #####   ","  ####      ####  ",
     "  ##          ##  "]
]


def icon(x,y,rows):
    for dy,row in enumerate(rows):
        for dx,value in enumerate(row):
            if value=='#':pixel(x+dx,y+dy)


def rle(raw):
    packed=[]
    for value, group in groupby(raw):
        count=len(list(group))
        while count:
            n=min(count,255);packed.extend([n,value]);count-=n
    packed.append(0)
    restored=[]
    for i in range(0,len(packed)-1,2):restored.extend([packed[i+1]]*packed[i])
    assert bytes(restored)==bytes(raw)
    return packed


def c_array(name,values):
    lines=[f'static const uint8_t {name}[{len(values)}] = {{']
    lines += ['    '+','.join(f'0x{n:02x}' for n in values[i:i+16])+',' for i in range(0,len(values),16)]
    return '\n'.join(lines+['};'])


def matrix(selected):
    colors=bytearray([0xe4]*1000)
    def fill(x,y,w,h,value):
        for row in range(y,y+h): colors[row*40+x:row*40+x+w]=bytes([value])*w
    fill(1,1,38,23,0xc0)
    fill(2,1,36,4,0x30)
    fill(29,1,9,4,0xe0)
    fill(2,4,26,1,0xc0)
    fill(2,5,36,1,0xe0)
    for i,color in enumerate((6,14,4,10,7,13,3)):
        fill(27+i,5,1,1,color<<4)
    fill(2,19,36,1,0xf0)
    for y in (20,21,23):fill(2,y,36,1,0xc0)
    fill(2,22,36,1,0xe0)
    for i,c in enumerate(SPEC['cards']):
        x,y=c['x'],c['y'];w,h=SPEC['width'],SPEC['height']
        fill(x,y,w,h,0xf0 if i==selected else 0xc0)
        fill(x,y,w,1,0x30 if i==selected else 0xf0)
        fill(x,y,1,h,0x30 if i==selected else 0xf0)
        fill(x,y+h-1,w,1,0x30 if i==selected else 0xb0)
        fill(x+w-1,y,1,h,0x30 if i==selected else 0xb0)
        fill(x+1,y+1,3,2,((7,3,14,7)[i]<<4))
        fill(x+5,y+1,w-6,1,0x30 if i==selected else 0x10)
        fill(x+1,y+3,1,1,0x03 if i==selected else 0xf6)
        fill(x+3,y+3,w-4,1,0xc0)
    return colors


def main():
    global BITMAP
    BITMAP=bytearray(8000)
    # Original geometric surround: VIC-II blue and light-blue at cell level.
    for offset in range(-200,350,24):
        line(offset,0,offset+200,199)
        line(offset+1,0,offset+201,199)
        line(offset+7,0,offset+207,199)
    clear(8,8,304,184)
    # Reuse the approved title exactly, without including the silhouette.
    header=(ROOT/'launcher/ui/kicker.h').read_text().split('title_rle',1)[1]
    packed=[int(n,16) for n in re.findall(r'0x([0-9a-f]{2})',header)]
    title=[]
    for i in range(0,len(packed)-1,2):title.extend([packed[i+1]]*packed[i])
    assert len(title)==576
    for row in range(2):BITMAP[(1+row)*320+16:(1+row)*320+304]=bytes(title[row*288:(row+1)*288])
    text(2,4,'SD CARD LAUNCHER')
    # Compact angular emblem in the masthead, rather than a large mascot.
    for shift in (0,12,24):
        line(242+shift,12,254+shift,24)
        line(254+shift,24,242+shift,36)
        line(243+shift,12,255+shift,24)
        line(255+shift,24,243+shift,36)
    for y in (5*8+4,22*8+3):
        for x in range(16,304):pixel(x,y)
    descriptions=['Load and play','Make and explore','Manage your C64','Your best picks']
    for i,c in enumerate(SPEC['cards']):
        x,y=c['x'],c['y']
        rect(x*8+1,y*8+1,SPEC['width']*8-2,SPEC['height']*8-2)
        line(x*8+2,y*8+2,x*8+SPEC['width']*8-3,y*8+2)
        line(x*8+2,y*8+2,x*8+2,y*8+SPEC['height']*8-3)
        icon((x+1)*8+2,(y+1)*8,ICONS[i])
        text(x+5,y+1,c['label'])
        # Key caps are small, not entire highlighted panels.
        text(x+1,y+3,c['key'])
        text(x+3,y+3,descriptions[i])
    text(2,20,'B  Browse SD      S  Settings')
    text(2,21,'F3  Cart utilities      Q  BASIC')
    text(2,23,'CURSOR / JOY 2: MOVE    RETURN / FIRE: OPEN')
    base=bytes(BITMAP)
    hints=[]
    for c in SPEC['cards']:
        BITMAP=bytearray(base)
        clear(16,19*8,288,8)
        text(2,19,c['path']+'  '+c['hint'])
        hints.append(bytes(BITMAP[19*320:20*320]))
    assets=[c_array('folder_bitmap',rle(base))]
    assets.extend(c_array('folder_hint_'+str(i),rle(h)) for i,h in enumerate(hints))
    assets.append('static const uint8_t* const folder_hints[4] = {folder_hint_0,folder_hint_1,folder_hint_2,folder_hint_3};')
    assets.append('static const char* const folder_paths[4] = {'+','.join(json.dumps(c['path']) for c in SPEC['cards'])+'};')
    assets.extend(c_array('folder_colors_'+str(i),rle(matrix(i))) for i in range(4))
    assets.append('static const uint8_t* const folder_palettes[4] = {folder_colors_0,folder_colors_1,folder_colors_2,folder_colors_3};')
    (OUT/'assets.h').write_text('/* Generated by tools/design_folder_home.py. EF3 font: Thomas Giesel. */\n'+'\n'.join(assets)+'\n')
    for selected,c in enumerate(SPEC['cards']):
        bitmap=bytearray(base);bitmap[19*320:20*320]=hints[selected]
        colors=matrix(selected);image=Image.new('RGB',(320,200))
        for y in range(200):
            for x in range(320):
                cell=colors[y//8*40+x//8]
                bit=bitmap[y//8*320+x//8*8+y%8] & (128>>(x%8))
                color=PALETTE[cell>>4 if bit else cell&15]
                image.putpixel((x,y),tuple(int(color[i:i+2],16) for i in (0,2,4)))
        image.resize((960,600),Image.Resampling.NEAREST).save(ROOT/'preview'/('folder-home-'+c['label'].lower()+'.png'))
    sizes={'bitmap_raw':8000,'bitmap_rle':len(rle(base)),'hints_rle':sum(len(rle(h)) for h in hints),'matrix_rle':sum(len(rle(matrix(i))) for i in range(4)),'firmware_integrated':False,'vice_tested':False}
    (OUT/'measurements.json').write_text(json.dumps(sizes,indent=2)+'\n')
    print(json.dumps(sizes))


if __name__=='__main__':main()
