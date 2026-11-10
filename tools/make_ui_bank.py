#!/usr/bin/env python3
"""Prepare Home graphics plus the licensed font in unused VIC-bank RAM."""
from pathlib import Path
import ctypes,ctypes.util,re,hashlib,json
from pack_folder_home import decode
from make_font import read_font,glyph
ROOT=Path(__file__).resolve().parents[1]
def make_bank():
    packed=bytes(int(x,16) for x in re.findall(r'0x([0-9a-f]{2})',(ROOT/'launcher/ui/folder_packed.h').read_text()))
    bank=bytearray(decode(packed));assert len(bank)==16384
    font,offsets=read_font(ROOT/'launcher/ui/charset.sed');assert len(font)<=1024
    assert not any(bank[0x1500:0x1c00])
    bank[0x1500:0x1500+len(font)]=font
    bank[0x1900:0x1a00]=bytes(x&255 for x in offsets)
    bank[0x1a00:0x1a40]=bytes(sum((offsets[i+j]>>8)<<(2*j) for j in range(4)) for i in range(0,256,4))
    bank[0x1a40:0x1b40]=bytes(len(glyph(font,p))+1 for p in offsets)
    return bytes(bank)
def c_array(name,data):
    return 'const unsigned char '+name+'['+str(len(data))+'] = {\n'+'\n'.join(','.join('0x%02x'%x for x in data[i:i+32])+',' for i in range(0,len(data),32))+'\n};\n'
def generate(out):
    out.mkdir(parents=True,exist_ok=True);bank=make_bank();(out/'bank.bin').write_bytes(bank)
    (out/'ui_assets.h').write_text('/* Generated. EF3 font: Thomas Giesel; see launcher/ui/EF3-LICENSE.md. */\n'+c_array('ui_bank',bank))
    lib=ctypes.CDLL(ctypes.util.find_library('lz4'));lib.LZ4_compress_HC.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int]
    dest=ctypes.create_string_buffer(32768);size=lib.LZ4_compress_HC(bank,dest,16384,32768,12);packed=dest.raw[:size];assert decode(packed)==bank
    (out/'mock_assets.c').write_text('/* VICE fixture only. */\n#pragma rodata-name ("MOCK_ASSET")\n'+c_array('home_packed',packed))
    return {'ui_bank_sha256':hashlib.sha256(bank).hexdigest(),'ui_bank_bytes':len(bank),'mock_packed_bytes':size}
if __name__=='__main__':print(json.dumps(generate(ROOT/'launcher/build/ui-assets'),indent=2))
