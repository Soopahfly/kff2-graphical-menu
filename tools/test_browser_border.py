#!/usr/bin/env python3
"""Verify the static browser preview's exact VIC data and Space-to-BASIC exit."""
import argparse,json,re,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--vice',type=Path,required=True);p.add_argument('--rom-dir',type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[1];work=root/'launcher/build/browser-border'
syms={name:int(value,16) for value,name in re.findall(r'^al ([0-9A-F]+) \.(\w+)',(work/'preview.lbl').read_text(),re.M)}
mon=work/'preview.mon'
regs=[0xd011,0xd016,0xd018,0xdd00,0xdd02,0xd020,0xd015,0x0291]
commands=[f'break exec ${syms["start"]:04x}','g']
for i,reg in enumerate(regs):commands.append(f'bsave "{work / ("before-"+str(i)+".bin")}" 0 ${reg:04x} ${reg:04x}')
commands+=['delete 1',f'break exec ${syms["preview_poll"]:04x}','ignore 1 1000','g',
           f'bsave "{work / "vic-bank.bin"}" 0 $4000 $7fff',
           f'screenshot "{root / "preview/browser-home-border-vice.png"}" 2',
           'keybuf " "','delete 1',f'break exec ${syms["preview_done"]:04x}','g']
for i,reg in enumerate(regs):commands.append(f'bsave "{work / ("after-"+str(i)+".bin")}" 0 ${reg:04x} ${reg:04x}')
commands+=['delete 1','g']
mon.write_text('\n'.join(commands)+'\n')
for f in [*work.glob('before-*.bin'),*work.glob('after-*.bin'),work/'vic-bank.bin']:f.unlink(missing_ok=True)
cmd=[str(a.vice.resolve()),'-console','-default','+sound','-warp','-limitcycles','5000000',
     '-directory',str(a.rom_dir.resolve()),'-autostartprgmode','1','-refreshonbreak','-initbreak','reset',
     '-moncommands',str(mon),'-exitscreenshot',str(work/'basic.png'),
     '-autostart',str(root/'preview/kff2-browser-border-preview.prg')]
for flag,name in [('kernal','kernal-901227-03.bin'),('basic','basic-901226-01.bin'),('chargen','chargen-901225-01.bin')]:cmd.extend(['-'+flag,str(a.rom_dir.resolve()/name)])
r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=40)
(work/'vice.log').write_bytes(r.stdout)
bank=(work/'vic-bank.bin').read_bytes()
assert bank[0x1c00:0x1fe8]==(work/'matrix.bin').read_bytes()
assert bank[0x2000:0x3f40]==(work/'bitmap.bin').read_bytes()
for i,reg in enumerate(regs):
    before=(work/('before-'+str(i)+'.bin')).read_bytes()[0]
    after=(work/('after-'+str(i)+'.bin')).read_bytes()[0]
    mask=127 if reg==0xd011 else 255
    assert before&mask==after&mask,(hex(reg),before,after)
report=root/'experiments/browser-border/measurements.json';result=json.loads(report.read_text())
result.update(vice_verified=True,vice_memory_matches_design=True,space_restores_display_registers=True)
report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
