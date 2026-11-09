#!/usr/bin/env python3
"""Pack the exact folder Home VIC bank with a small, bounded LZ format."""
from pathlib import Path
import re,json,ctypes,ctypes.util
ROOT=Path(__file__).resolve().parents[1]

def decode(data):
 out=bytearray();p=0
 def length(n):
  nonlocal p
  if n==15:
   while True:
    value=data[p];p+=1;n+=value
    if value<255:break
  return n
 while p<len(data):
  token=data[p];p+=1;n=length(token>>4)
  out.extend(data[p:p+n]);p+=n
  if p==len(data):break
  offset=data[p]|data[p+1]<<8;p+=2
  assert 0<offset<=len(out)
  n=length(token&15)+4
  for _ in range(n):out.append(out[-offset])
 return bytes(out)

def main():
 text=(ROOT/'experiments/folder-home/assets.h').read_text();raw={}
 for name,body in re.findall(r'static const uint8_t (folder_\w+)\[\d+\] = \{([^}]+)\};',text):
  a=[int(n,16) for n in re.findall(r'0x([0-9a-f]{2})',body)]
  raw[name]=bytes(v for i in range(0,len(a)-1,2) for v in [a[i+1]]*a[i])
 bank=bytearray(16384)
 for i in range(4):
  bank[i*320:(i+1)*320]=raw['folder_hint_'+str(i)]
  bank[1280+i*1000:1280+(i+1)*1000]=raw['folder_colors_'+str(i)]
 bank[0x1c00:0x1fe8]=raw['folder_colors_0']
 bank[0x2000:0x3f40]=raw['folder_bitmap']
 # liblz4's high-compression encoder produces a standard raw LZ4 block.
 library=ctypes.util.find_library('lz4')
 if not library:raise RuntimeError('Install liblz4 to reproduce the ROM-fit build')
 lib=ctypes.CDLL(library)
 lib.LZ4_compress_HC.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int]
 dest=ctypes.create_string_buffer(len(bank)*2)
 size=lib.LZ4_compress_HC(bytes(bank),dest,len(bank),len(dest),12)
 assert size>0
 packed=dest.raw[:size]
 assert decode(packed)==bytes(bank)
 header=['/* Generated lossless VIC bank. EF3 font: Thomas Giesel. */',f'const uint8_t home_packed[{len(packed)}] = {{']
 header+=['    '+','.join(f'0x{n:02x}' for n in packed[i:i+16])+',' for i in range(0,len(packed),16)]
 header+=['};','']
 (ROOT/'launcher/ui/folder_packed.h').write_text('\n'.join(header))
 dest=ROOT/'launcher/build/folder-home';dest.mkdir(parents=True,exist_ok=True)
 (dest/'vic-bank.bin').write_bytes(bank)
 (dest/'vic-bank.lz').write_bytes(packed)
 print(json.dumps({'unpacked':len(bank),'packed':len(packed),'roundtrip':True}))
if __name__=='__main__':main()
