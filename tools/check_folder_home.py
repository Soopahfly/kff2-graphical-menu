#!/usr/bin/env python3
"""Check folder Home PRG entry, memory ranges and compressed asset lengths."""
import hashlib
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
build=root/'launcher/build/folder-home'
prg=(build/'kff2-folder-home-preview.prg').read_bytes()
load=int.from_bytes(prg[:2],'little')
assert load==0x0801 and prg[6]==0x9e
entry=int(prg[7:prg.index(b'\0',7)])
end=load+len(prg)-2
assert load<=entry<end<0x4000
segments=(build/'preview.map').read_text().split('Segment list:',1)[1].split('Exports list',1)[0]
for name,start,last,size in re.findall(r'^(\w+)\s+([0-9A-F]{6})\s+([0-9A-F]{6})\s+([0-9A-F]{6})',segments,re.M):
    if name!='ZEROPAGE':assert int(last,16)<0x4000,(name,last)
assets=(root/'experiments/folder-home/assets.h').read_text()
checked=0
for name,body in re.findall(r'static const uint8_t (folder_\w+)\[\d+\] = \{([^}]+)\};',assets):
    raw=[int(n,16) for n in re.findall(r'0x([0-9a-f]{2})',body)]
    assert raw[-1]==0 and 0 not in raw[:-1:2]
    size=sum(raw[:-1:2])
    assert size==(8000 if name=='folder_bitmap' else 1000 if name=='folder_colors' else 320),(name,size)
    checked+=1
assert checked==6
path=root/'experiments/folder-home/measurements.json'
report=json.loads(path.read_text())
report.update(prg_bytes=len(prg),prg_load=hex(load),prg_end_exclusive=hex(end),basic_sys=entry,
              prg_sha256=hashlib.sha256(prg).hexdigest(),stream_lengths_checked=True)
path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
