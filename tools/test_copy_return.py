#!/usr/bin/env python3
"""Exercise the real C64 warning-to-Home path with one buffered key in VICE."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from test_integrated_launcher import labels

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--vice',type=Path,required=True)
    p.add_argument('--rom-dir',type=Path,required=True)
    p.add_argument('--expect-stale-screen',action='store_true',help='Confirm the G7.0.2 regression before applying the fix')
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    work=root/'launcher/build/integration';out=work/'scenario-10'
    s=labels(out/'test.lbl')
    commands=[f'break exec ${s["_ui_copy_stop"]:04x}','g']
    names=['copy-result','home-after-one-key','browser','home-again']
    for i,name in enumerate(names):
        for suffix in ['bin','png']:(out/(name+'.'+suffix)).unlink(missing_ok=True)
        commands += [f'bsave "{out/name}.bin" 0 $4000 $7fff',f'screenshot "{out/name}.png" 2']
        if i==0:commands += ['> $0277 $0d','> $00c6 $01']
        if i<3:commands += ['g']
    start=min(s[n] for n in ['_test_result','_test_error','_test_copy_syncs','_test_key_index'])
    end=max(s[n] for n in ['_test_result','_test_error','_test_copy_syncs','_test_key_index'])
    commands += ['delete 1',f'break exec ${s["_ui_test_finished"]:04x}','g',f'bsave "{out/"complete.bin"}" 0 ${start:04x} ${end:04x}','quit']
    script=out/'copy-return.mon';script.write_text('\n'.join(commands)+'\n')
    cmd=[str(a.vice.resolve()),'-console','-default','+sound','+warp','-directory',str(a.rom_dir.resolve()),'-kernal',str(a.rom_dir.resolve()/'kernal-901227-03.bin'),'-basic',str(a.rom_dir.resolve()/'basic-901226-01.bin'),'-chargen',str(a.rom_dir.resolve()/'chargen-901225-01.bin'),'-autostartprgmode','1','-limitcycles','50000000','-refreshonbreak','-initbreak','reset','-moncommands',str(script),'-autostart',str(out/'kff2-integration-test.prg')]
    (out/'complete.bin').unlink(missing_ok=True)
    r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=55)
    (out/'copy-return-vice.log').write_bytes(r.stdout)
    state=(out/'complete.bin').read_bytes()
    get=lambda n:state[s[n]-start]
    assert get('_test_result')==1 and not get('_test_error'),'Copy fixture did not complete'
    assert get('_test_copy_syncs')==2 and get('_test_key_index')==3,'Wrong command/key sequence'
    expected=bytearray((work/'ui-assets/bank.bin').read_bytes())
    expected[0x2000+19*320:0x2000+20*320]=expected[:320]
    home=(out/'home-after-one-key.bin').read_bytes()
    again=(out/'home-again.bin').read_bytes()
    stale=home!=expected
    if a.expect_stale_screen:
        assert stale,'Old stale-status bug was not reproduced'
    else:
        assert home==expected,'One key left the stale status screen over Home'
        assert again==expected,'Returning from the browser left stale status over Home'
    result={'passed':not stale,'old_bug_reproduced':stale,'warning_dismissal_keys':1,
            'syncs':get('_test_copy_syncs'),'browser_and_home_navigation':True,
            'native_image_sha256':hashlib.sha256((work/'native/kff2-integrated-launcher.bin').read_bytes()).hexdigest(),
            'manual_prg_sha256':hashlib.sha256((work/'scenario-11/kff2-integration-test.prg').read_bytes()).hexdigest()}
    (work/('copy-return-old-results.json' if a.expect_stale_screen else 'copy-return-results.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
