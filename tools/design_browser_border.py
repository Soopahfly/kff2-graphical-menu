#!/usr/bin/env python3
"""Build a native 320x200 browser layout using Home's exact patterned surround.

Design experiment only. The static PRG does not read SD or replace the launcher.
All glyphs use the project's licensed EF3 font. No C64 ROM bytes are embedded.
"""
from pathlib import Path
import json,re,hashlib,subprocess,os
from PIL import Image
from make_font import read_font,glyph

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'launcher/build/browser-border'
DEST=ROOT/'preview'
FONT,OFFSETS=read_font(ROOT/'launcher/ui/charset.sed')
PALETTE=['000000','ffffff','813338','75cec8','8e3c97','56ac4d','2e2c9b','edf171',
         '8e5029','553800','c46c71','4a4a4a','7b7b7b','a9ff9f','706deb','b2b2b2']

def assets():
    out={}
    for name,body in re.findall(r'static const uint8_t (folder_\w+)\[\d+\] = \{([^}]+)\};',
                               (ROOT/'experiments/folder-home/assets.h').read_text()):
        data=[int(n,16) for n in re.findall(r'0x([0-9a-f]{2})',body)]
        out[name]=bytes(v for i in range(0,len(data)-1,2) for v in [data[i+1]]*data[i])
    return out

def index(x,y):return y//8*320+x//8*8+y%8

def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    a=assets();bitmap=bytearray(a['folder_bitmap']);colors=bytearray(a['folder_colors_0'])
    original_bitmap=bytes(bitmap);original_colors=bytes(colors)
    # Keep Home's masthead, surround, subtitle band and colour-strip separator.
    for row in range(6,24):
        bitmap[row*320+8:row*320+312]=bytes(304)
        colors[row*40+1:row*40+39]=bytes([0x10])*38
    bitmap[4*320+16:4*320+304]=bytes(288)
    colors[4*40+2:4*40+38]=bytes([0xf0])*36
    def pixel(x,y):
        assert 8<=x<312 and 8<=y<192
        bitmap[index(x,y)] |= 128>>(x%8)
    def text(x,row,value):
        for ch in value:
            code=ord(ch)-32 if 'a'<=ch<='z' else ord(ch)
            for column in glyph(FONT,OFFSETS[code]):
                for dy in range(8):
                    if column&(1<<dy):pixel(x,row*8+dy)
                x+=1
            x+=1
        assert x<=304,(value,x)
        return x
    def fill(x,row,w,color):colors[row*40+x:row*40+x+w]=bytes([color])*w
    def icon(x,row,kind):
        shapes={
            'DIR':[0,0x70,0xfe,0x82,0x82,0x82,0xfe,0],
            'CRT':[0,0x7e,0x42,0x5a,0x42,0x7e,0x24,0],
            'D64':[0,0x7e,0x52,0x5e,0x42,0x5a,0x7e,0],
            'PRG':[0,0x78,0x4c,0x44,0x54,0x54,0x7c,0]}
        for dy,bits in enumerate(shapes[kind]):
            for dx in range(8):
                if bits&(128>>dx):pixel(x+dx,row*8+dy)
    text(16,4,'GAMES   /Games/Arcade')
    files=[('.. Parent folder','DIR'),('Shooters','DIR'),('Platformers','DIR'),
           ('Boulder Dash','PRG'),('Bruce Lee','CRT'),('Bubble Bobble','D64'),
           ('Impossible Mission','CRT'),('International Karate','PRG'),
           ('Mayhem in Monsterland','D64'),('Paradroid','PRG'),
           ('The Last Ninja','D64'),('Turrican','CRT')]
    selected=4
    for i,(name,kind) in enumerate(files):
        row=7+i
        if i==selected:fill(2,row,36,0x03)
        else:
            fill(2,row,1,0x30 if kind=='DIR' else 0xf0)
            fill(3,row,30,0x30 if kind=='DIR' else 0x10)
            fill(34,row,4,0xf0)
        icon(16,row,kind);text(32,row,name);text(272,row,kind)
    # Details and controls use the same bands and line positions as Home.
    for x in range(16,304):pixel(x,19*8+3);pixel(x,22*8+3)
    for row in (19,22):fill(2,row,36,0xe0)
    text(16,20,'Bruce Lee.crt');text(264,20,'5 / 148');fill(2,20,36,0x30)
    text(16,21,'Played 6 times   Random 2');fill(2,21,36,0xf0)
    text(16,23,'RETURN Open  DEL Back  F2 Home  F4 Random');fill(2,23,36,0xf0)
    # Byte-for-byte preservation of EVERY border cell, including its palette.
    for row in range(25):
        for col in range(40):
            if row in (0,24) or col in (0,39):
                cell=row*40+col
                assert colors[cell]==original_colors[cell]
                assert bitmap[cell*8:cell*8+8]==original_bitmap[cell*8:cell*8+8]
    # Preserve Home's original title and chevron artwork, too.
    assert bitmap[1*320:4*320]==original_bitmap[1*320:4*320]
    (BUILD/'bitmap.bin').write_bytes(bitmap);(BUILD/'matrix.bin').write_bytes(colors)
    image=Image.new('RGB',(320,200))
    for y in range(200):
        for x in range(320):
            cell=colors[y//8*40+x//8]
            bit=bitmap[index(x,y)]&(128>>(x%8))
            c=PALETTE[cell>>4 if bit else cell&15]
            image.putpixel((x,y),tuple(int(c[i:i+2],16) for i in (0,2,4)))
    image.save(DEST/'browser-home-border-native.png')
    image.resize((960,600),Image.Resampling.NEAREST).save(DEST/'browser-home-border.png')
    env=os.environ.copy()
    subprocess.run(['ca65','-g','--bin-include-dir',str(BUILD),'-o',str(BUILD/'preview.o'),
                    str(ROOT/'experiments/browser-border/preview.s')],check=True,env=env)
    subprocess.run(['ld65','-C',str(ROOT/'experiments/browser-border/preview.cfg'),
                    '-o',str(DEST/'kff2-browser-border-preview.prg'),
                    '-Ln',str(BUILD/'preview.lbl'),'-m',str(BUILD/'preview.map'),
                    str(BUILD/'preview.o')],check=True,env=env)
    prg=(DEST/'kff2-browser-border-preview.prg').read_bytes()
    assert prg[:2]==b'\x01\x08' and prg[7:11]==b'2061'
    assert prg[2+0x5c00-0x0801:2+0x5c00-0x0801+1000]==colors
    assert prg[2+0x6000-0x0801:]==bitmap
    result={'native_resolution':[320,200],'preview_only':True,'integrated_firmware':False,
            'border_bitmap_and_palette_identical_to_home':True,'masthead_art_identical':True,
            'visible_rows':len(files),'font':'Existing EF3 / Home font, Thomas Giesel',
            'details_and_counts':'Sample design data, not an implemented firmware stats feature',
            'prg_bytes':len(prg),'prg_sha256':hashlib.sha256(prg).hexdigest(),
            'vice_verified':False,'hardware_tested':False}
    (ROOT/'experiments/browser-border/measurements.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
