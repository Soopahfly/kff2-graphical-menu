#!/usr/bin/env python3
"""Run the native-menu PRG harness in VICE. Requires user's own C64 ROM files."""
import argparse
import json
import hashlib
from pathlib import Path
import re
import subprocess


def labels(path):
    return {m[1]:int(m[0],16) for m in re.findall(r'^al ([0-9A-F]+) \.(_\w+)',path.read_text(),re.M)}


def attach_build_identity(work,result):
    result['version']=json.loads((work/'native-measurements.json').read_text())['version']
    result['native_image_sha256']=hashlib.sha256((work/'native/kff2-integrated-launcher.bin').read_bytes()).hexdigest()
    result['interactive_prg_sha256']=hashlib.sha256((work/'interactive/kff2-integration-test.prg').read_bytes()).hexdigest()
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--vice',type=Path,required=True)
    ap.add_argument('--rom-dir',type=Path,required=True)
    args=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    work=root/'launcher/build/integration'
    results=[]
    base=[str(args.vice.resolve()),'-console','-default','+sound','-warp',
          '-directory',str(args.rom_dir.resolve()),
          '-kernal',str(args.rom_dir.resolve()/'kernal-901227-03.bin'),
          '-basic',str(args.rom_dir.resolve()/'basic-901226-01.bin'),
          '-chargen',str(args.rom_dir.resolve()/'chargen-901225-01.bin'),
          '-autostartprgmode','1','-limitcycles','50000000']
    expected={1:[0x82,0x80,0x87,0x80,0x8f,0x89,0x80,0x9a,0x80,0x8a],
              2:[0x82,0x80,0x87],3:[0x82,0x80,0x86,0x80,0x85,0x80,0x8f,0x87],
              4:[0x8e,0x80,0x8e,0x80,0x8e,0x80,0x8e,0x80,0x8f,0x8e,0x80,0x8a],5:[0x9b],6:[0x8e,0x80,0x9b]}
    for scenario in range(1,7):
        output=work/('scenario-'+str(scenario))
        syms=labels(output/'test.lbl')
        names=['_test_key_index','_test_error','_test_result','_test_reply_count',
               '_test_replies','_test_selected','_test_folder','_test_page',
               '_test_select_count','_test_seen']
        start=min(syms[n] for n in names)
        end=max(syms[n]+(47 if n=='_test_replies' else 0) for n in names)
        dump=output/'status.bin'
        dump.unlink(missing_ok=True)
        for old in output.glob('*.png'): old.unlink()
        commands=[]
        if scenario==1:
            commands += [f'break exec ${syms["_ui_test_checkpoint"]:04x}','g',
                f'screenshot "{output / "home.png"}" 2',
                f'bsave "{output / "home-bank.bin"}" 0 $4000 $7fff','g',
                f'screenshot "{output / "browser.png"}" 2','g',
                f'screenshot "{output / "child.png"}" 2','g','g',
                f'screenshot "{output / "home-return.png"}" 2','g',
                f'screenshot "{output / "cached-browser.png"}" 2','delete 1']
        commands += [f'break exec ${syms["_ui_test_finished"]:04x}','g']
        if scenario in (3,6):
            commands += [f'bsave "{output / "screen.bin"}" 0 $0400 $07e7',
                         f'bsave "{output / "colors.bin"}" 0 $d800 $dbe7',
                         f'screenshot "{output / "browser-final.png"}" 2']
        commands += [f'bsave "{dump}" 0 ${start:04x} ${end:04x}','quit']
        script=output/'test.mon';script.write_text('\n'.join(commands)+'\n')
        timing=['+warp','-limitcycles','30000000'] if scenario==1 else []
        cmd=base+timing+['-refreshonbreak','-initbreak','reset','-moncommands',str(script),
                  '-monlog','-monlogname',str(output/'monitor.log'),
                  '-autostart',str(output/'kff2-integration-test.prg'),
                  '-exitscreenshot',str(output/'result.png')]
        r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=50)
        (output/'vice.log').write_bytes(r.stdout)
        if scenario==1:
            expected_bank=bytearray((root/'launcher/build/folder-home/vic-bank.bin').read_bytes())
            expected_bank[0x2000+19*320:0x2000+20*320]=expected_bank[:320]
            assert (output/'home-bank.bin').read_bytes()==expected_bank, 'VIC bank differs from the design'
        if not dump.exists():raise RuntimeError(f'Scenario {scenario} did not reach its final checkpoint.')
        data=dump.read_bytes()
        def value(name):return data[syms[name]-start]
        count=value('_test_reply_count')
        offset=syms['_test_replies']-start
        trace=list(data[offset:offset+count])
        result={'scenario':scenario,'passed':value('_test_result')==1,
                'error':value('_test_error'),'reply_trace':trace,
                'selected_byte':value('_test_selected'),'keys_used':value('_test_key_index')}
        assert result['passed'] and not result['error'],result
        assert trace==expected[scenario],result
        if scenario in (3,6):
            screen=(output/'screen.bin').read_bytes()
            colors=bytes(c&15 for c in (output/'colors.bin').read_bytes())
            assert len(screen)==len(colors)==1000
            assert screen[:40]==b' '*40 and screen[24*40:]==b' '*40, 'Overscan margin contains text'
            assert all(c==1 for c in colors[2*40+1:2*40+38]), 'Path must be white'
            selected_row=20 if scenario==3 else 4
            selected=screen[selected_row*40+1:selected_row*40+39]
            assert all(c&128 for c in selected), 'Selection must fill the row'
            assert colors[selected_row*40+1:selected_row*40+39]==bytes([3])*38, 'Selection must be cyan'
            if scenario==3:
                assert not any(screen[4*40+1:20*40+39][i]&128
                               for i in range(16*40) if i%40<38), 'Stale selection after viewport scroll'
            result['browser_screen_checked']=True
        results.append(result)
        print(json.dumps(result))
    # Exercise the uninstrumented input paths with real C64 keyboard-buffer bytes.
    output=work/'interactive'
    syms=labels(output/'test.lbl')
    image=(output/'kff2-integration-test.prg').read_bytes()
    load=int.from_bytes(image[:2],'little')
    call=bytes([0x20,syms['_kbhit']&255,syms['_kbhit']>>8])
    def poll(name):
        pos=image.find(call,syms[name]-load+2,syms[name]-load+2+1024)
        assert pos>=0,name
        return load+pos-2
    def stop(name):
        return [f'break exec ${poll(name):04x}','ignore 1 200','g']
    dump=output/'keyboard-status.bin';dump.unlink(missing_ok=True)
    start=syms['_test_key_index'];end=syms['_test_seen']
    commands=stop('_home_run')+['keybuf "b"','delete 1']+stop('_menuLoop')
    commands += [f'screenshot "{output / "keyboard-browser.png"}" 2',
                 '> $0277 $89','> $00c6 $01','delete 1']+stop('_home_run')
    commands += [f'screenshot "{output / "keyboard-home-return.png"}" 2',
                 'keybuf "b"','delete 1']+stop('_menuLoop')
    commands += ['> $0277 $89','> $00c6 $01','delete 1']+stop('_home_run')
    commands += ['keybuf "q"','delete 1',f'break exec ${syms["_ui_test_finished"]:04x}',
                 'g',f'bsave "{dump}" 0 ${start:04x} ${end:04x}','delete 1','g']
    script=output/'keyboard.mon';script.write_text('\n'.join(commands)+'\n')
    r=subprocess.run(base+['+warp','-limitcycles','30000000','-refreshonbreak',
                '-initbreak','reset','-moncommands',str(script),
                '-monlog','-monlogname',str(output/'keyboard-monitor.log'),
                '-autostart',str(output/'kff2-integration-test.prg'),
                '-exitscreenshot',str(output/'keyboard-basic.png')],
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=50)
    (output/'keyboard-vice.log').write_bytes(r.stdout)
    assert dump.exists(),'Interactive keyboard test did not finish'
    data=dump.read_bytes()
    get=lambda name:data[syms[name]-start]
    offset=syms['_test_replies']-start
    trace=list(data[offset:offset+get('_test_reply_count')])
    assert get('_test_result')==1 and not get('_test_error') and trace==[0x82,0x80,0x8f,0x8a],trace
    keyboard={'passed':True,'reply_trace':trace,'input':'B, F2, B, F2, Q via C64 keyboard buffer'}
    print(json.dumps(keyboard))
    # NTSC startup uses the same interactive harness without injected keys.
    output=work/'interactive'
    r=subprocess.run(base+['-ntsc','-autostart',str(output/'kff2-integration-test.prg'),
                           '-exitscreenshot',str(output/'home-ntsc.png')],
                     stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=50)
    (output/'vice-ntsc.log').write_bytes(r.stdout)
    (work/'test-results.json').write_text(json.dumps(attach_build_identity(work,{'scenarios':results,'keyboard':keyboard,'ntsc_startup_capture':True}),indent=2)+'\n')

if __name__=='__main__':main()
