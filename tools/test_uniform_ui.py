#!/usr/bin/env python3
"""Check shared menu/message frames and streamed reader pages in VICE."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from test_integrated_launcher import labels

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--vice',type=Path,required=True)
    ap.add_argument('--rom-dir',type=Path,required=True)
    args=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    work=root/'launcher/build/integration';out=work/'scenario-9'
    syms=labels(out/'test.lbl');names=['settings','utilities','options','options-scroll','help','search','warning','progress','reader-first','reader-next','reader-back','startup-fallback']
    commands=[f'break exec ${syms["_ui_uniform_stop"]:04x}','g']
    start=min(syms[n] for n in ['_test_seen','_test_error','_test_asset_count'])
    end=max(syms[n] for n in ['_test_seen','_test_error','_test_asset_count'])
    for i,name in enumerate(names,1):
        for suffix in ['bin','png','state']:(out/(name+'.'+suffix)).unlink(missing_ok=True)
        commands += [f'bsave "{out/name}.bin" 0 $4000 $7fff',f'bsave "{out/name}.state" 0 ${start:04x} ${end:04x}',f'screenshot "{out/name}.png" 2','g']
    # Replace the last continue so completion is caught before returning.
    commands[-1]='delete 1'
    commands += [f'break exec ${syms["_ui_test_finished"]:04x}','g',f'bsave "{out/"complete.bin"}" 0 ${syms["_test_result"]:04x} ${syms["_test_result"]:04x}','quit']
    script=out/'uniform.mon';script.write_text('\n'.join(commands)+'\n')
    cmd=[str(args.vice.resolve()),'-console','-default','+sound','+warp','-directory',str(args.rom_dir.resolve()),'-kernal',str(args.rom_dir.resolve()/'kernal-901227-03.bin'),'-basic',str(args.rom_dir.resolve()/'basic-901226-01.bin'),'-chargen',str(args.rom_dir.resolve()/'chargen-901225-01.bin'),'-autostartprgmode','1','-limitcycles','50000000','-refreshonbreak','-initbreak','reset','-moncommands',str(script),'-autostart',str(out/'kff2-integration-test.prg')]
    r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=55)
    (out/'vice.log').write_bytes(r.stdout)
    assert (out/'complete.bin').read_bytes()==b'\x01','Uniform checks did not complete'
    original=(work/'ui-assets/bank.bin').read_bytes();results=[]
    for i,name in enumerate(names,1):
        bank=(out/(name+'.bin')).read_bytes();state=(out/(name+'.state')).read_bytes()
        assert state[syms['_test_seen']-start]==i,(name,'wrong checkpoint')
        assert not state[syms['_test_error']-start],(name,'C check failed')
        assert state[syms['_test_asset_count']-start]==1,(name,'extra asset request')
        assert bank[0x1500:0x1b40]==original[0x1500:0x1b40],(name,'font overwritten')
        assert bank[0x2000+320:0x2000+4*320]==original[0x2000+320:0x2000+4*320],(name,'masthead pixels')
        assert bank[0x1c00+40:0x1c00+4*40]==original[0x1c00+40:0x1c00+4*40],(name,'masthead colors')
        for row in range(25):
            for col in range(40):
                if row in (0,24) or col in (0,39):
                    cell=row*40+col
                    assert bank[0x1c00+cell]==original[0x1c00+cell],(name,'border color')
                    assert bank[0x2000+cell*8:0x2000+cell*8+8]==original[0x2000+cell*8:0x2000+cell*8+8],(name,'border pixels')
        if i in (1,2,3,4):
            selected_row={1:8,2:7,3:9,4:18}[i]
            assert bank[0x1c00+selected_row*40+2:0x1c00+selected_row*40+38]==bytes([3])*36,(name,'selection')
        results.append({'screen':name,'passed':True,'asset_requests':1})
    assert (out/'reader-first.bin').read_bytes()==(out/'reader-back.bin').read_bytes(),'Reader back navigation changed page'
    assert (out/'reader-first.bin').read_bytes()!=(out/'reader-next.bin').read_bytes(),'Reader did not advance'
    from make_font import read_font,glyph
    font,offsets=read_font(root/'launcher/ui/charset.sed')
    wide=bytearray(288);x=0
    for _ in range(32):
        for column in glyph(font,offsets[ord('W')|128]):
            for y in range(8):
                if column & (1<<y):wide[x//8*8+y] |= 128>>(x%8)
            x+=1
        x+=1
    first=(out/'reader-first.bin').read_bytes()
    assert first[0x2000+6*320+16:0x2000+6*320+304]==wide,'Wide reader glyphs lost at the frame edge'
    result={'version':json.loads((work/'native-measurements.json').read_text())['version'],'native_image_sha256':hashlib.sha256((work/'native/kff2-integrated-launcher.bin').read_bytes()).hexdigest(),'screens':results,'reader_forward_back':True,'native_fallback':True}
    (work/'uniform-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
