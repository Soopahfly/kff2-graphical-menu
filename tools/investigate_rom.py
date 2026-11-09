#!/usr/bin/env python3
"""Reproduce launcher space measurements without modifying upstream sources.

Requires cc65, make and a KFF2 checkout. Runs two link-only UI experiments:
1. Put the current UI into the existing ROM and report fit or overflow.
2. Link UI code/font into a separate C64 RAM payload, keeping the launcher in ROM.
Neither experiment changes firmware or produces a flashable update.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def run(args, env, cwd=None, allow_failure=False):
    r = subprocess.run([str(x) for x in args], cwd=cwd, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode and not allow_failure:
        raise RuntimeError(' '.join(map(str, args))+'\n'+r.stdout)
    return r


def segments(map_path):
    text = map_path.read_text()
    section = text.split('Segment list:', 1)[1].split('Exports list', 1)[0]
    return {m[0]: {'start': int(m[1],16), 'end': int(m[2],16), 'size': int(m[3],16)}
            for m in re.findall(r'^([A-Z][A-Z0-9_]*)\s+([0-9A-F]{6})\s+([0-9A-F]{6})\s+([0-9A-F]{6})',section,re.M)}


def rom_usage(map_path, limit=0xb800):
    text = map_path.read_text()
    load = int(re.search(r'__DATA_LOAD__\s+([0-9A-F]+)',text)[1],16)
    size = int(re.search(r'__DATA_SIZE__\s+([0-9A-F]+)',text)[1],16)
    end = load+size
    return {'rom_start':0x8000,'rom_limit':limit,'rom_end_exclusive':end,
            'rom_used_including_padding':end-0x8000,'rom_free':limit-end,
            'segments':segments(map_path)}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--upstream', type=Path, required=True)
    ap.add_argument('--cc65-home', type=Path)
    ap.add_argument('--easyflash-upstream', type=Path)
    ap.add_argument('--launcher-patch', type=Path, help='Optional experimental patch for the copied launcher')
    args=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    up=args.upstream.resolve()
    work=root/'launcher/build/rom-investigation'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy()
    if args.cc65_home:
        env['CC65_HOME']=str(args.cc65_home.resolve())
        env['PATH']=str(args.cc65_home.resolve()/'bin')+os.pathsep+env['PATH']
    for cmd in ['cc65','ca65','ld65','make']:
        if not shutil.which(cmd,path=env.get('PATH')): raise RuntimeError('Missing '+cmd)
    source=work/'upstream'
    ignore=shutil.ignore_patterns('build','obj','*.o','*.lib','.git')
    shutil.copytree(up/'launcher', source/'launcher', dirs_exist_ok=True,ignore=ignore)
    shutil.copytree(up/'3rd_party/libef3usb', source/'3rd_party/libef3usb',dirs_exist_ok=True,ignore=ignore)
    (source/'firmware').mkdir(exist_ok=True)
    shutil.copy(up/'firmware/commands.h',source/'firmware/commands.h')
    if args.launcher_patch:
        run(['patch','--batch','--forward','-p1','-i',args.launcher_patch.resolve()],env,cwd=source)
    launcher=source/'launcher'
    baseline=run(['make','version=2.07'],env,cwd=launcher)
    (work/'baseline.log').write_text(baseline.stdout)
    base_map=launcher/'build/KungFuLauncher_v2.07.bin.map'
    result={'toolchain':run(['cc65','--version'],env).stdout.strip(),
            'upstream_commit':run(['git','-C',up,'rev-parse','HEAD'],env).stdout.strip(),
            'baseline':rom_usage(base_map)}
    if args.launcher_patch:
        import hashlib
        result['experimental_patch']={'file':args.launcher_patch.name,
            'sha256':hashlib.sha256(args.launcher_patch.read_bytes()).hexdigest()}
    original=[launcher/'build'/f'{x}.o' for x in
              ['crt0.crt','main','base','screen','dir','kff_data','disk','ef3usb_loader','launcher_asm']]
    lib=source/'3rd_party/libef3usb/libef3usb.lib'
    ui=root/'launcher/ui'
    for kind in ['inline','ram_payload']:
        dest=work/kind
        dest.mkdir(exist_ok=True)
        objects=[]
        for stem in ['home','text_plot']:
            asm=dest/f'{stem}.s'
            options=['--code-name','UICODE','--rodata-name','UIRODATA'] if kind=='ram_payload' else []
            run(['cc65','-t','c64','-O',*options,'-o',asm,ui/f'{stem}.c'],env)
            obj=dest/f'{stem}.o'
            run(['ca65','-t','c64','-o',obj,asm],env)
            objects.append(obj)
        asm_text=(ui/'text_plot_asm.s').read_text()
        font_asm=dest/'font-generated.s'
        run(['python3',root/'tools/make_font.py',ui/'charset.sed',font_asm],env)
        font_text=font_asm.read_text()
        for stem,text in [('text_plot_asm',asm_text),('charset',font_text)]:
            if kind=='ram_payload':
                text=text.replace('.rodata','.segment "UIRODATA"').replace('.code','.segment "UICODE"')
            asm=dest/f'{stem}.s'
            asm.write_text(text)
            obj=dest/f'{stem}.o'
            run(['ca65','-t','c64','-I',ui,'-o',obj,asm],env)
            objects.append(obj)
        cfg=(launcher/'ld.crt.cfg').read_text()
        if kind=='ram_payload':
            cfg=cfg.replace('    ROM:','    UI: start = $1000, size = $4000, file = "%O.ui.bin", fill = yes, fillval = $ff, define = yes;\n    ROM:')
            cfg=cfg.replace('    EAPI:     load = EAPI,',
                            '    UICODE: load = UI, type = ro, define = yes;\n    UIRODATA: load = UI, type = ro, define = yes;\n    EAPI:     load = EAPI,')
        config=dest/'layout.cfg'
        config.write_text(cfg)
        outfile=dest/'launcher.bin'
        mapfile=dest/'launcher.map'
        r=run(['ld65','-o',outfile,'-m',mapfile,'-C',config,*original,*objects,
               '--lib',lib,'--lib','c64.lib'],env,allow_failure=(kind=='inline'))
        (dest/'link.log').write_text(r.stdout)
        if kind=='inline':
            result[kind]={'link_succeeded':r.returncode==0,
                'diagnostic':r.stdout.strip().replace(str(root),'<project>')}
            if r.returncode:
                # Sizing only: deliberately relaxed allocation, not runnable.
                relaxed=dest/'sizing-only.cfg'
                relaxed.write_text(cfg.replace('size = $3800','size = $5800'))
                sizing_map=dest/'sizing-only.map'
                run(['ld65','-o',dest/'sizing-only.bin','-m',sizing_map,'-C',relaxed,
                     *original,*objects,'--lib',lib,'--lib','c64.lib'],env)
                measured=rom_usage(sizing_map)
            else:
                measured=rom_usage(mapfile)
            result[kind]['rom_required_including_padding']=measured['rom_used_including_padding']
            result[kind]['total_overflow_including_data']=max(0,-measured['rom_free'])
            result[kind]['rom_free']=max(0,measured['rom_free'])
        else:
            result[kind]=rom_usage(mapfile)
            seg=result[kind]['segments']
            ui_used=sum(seg[x]['size'] for x in ['UICODE','UIRODATA'])
            result[kind].update({'link_succeeded':True,'ui_payload_used':ui_used,
                'ui_payload_capacity':16384,'ui_payload_free':16384-ui_used,
                'resident_image_bytes':outfile.stat().st_size,
                'padded_payload_bytes':Path(str(outfile)+'.ui.bin').stat().st_size})
            assert result[kind]['rom_free']>=0
            assert result[kind]['resident_image_bytes']==16384
            assert result[kind]['padded_payload_bytes']==16384
            assert seg['UIRODATA']['end']<0x5000
    if args.easyflash_upstream:
        ef_source=work/'easyflash3'
        for name in ['efmenu','libef3usb','tools']:
            shutil.copytree(args.easyflash_upstream.resolve()/name,ef_source/name,
                            dirs_exist_ok=True,ignore=ignore)
        # Never reuse generated upstream binaries as evidence of this build.
        for name in ['efmenu.bin','efmenu.crt','efmenu.bin.map']:
            (ef_source/'efmenu'/name).unlink(missing_ok=True)
        built=run(['make','-C',ef_source/'efmenu'],env)
        (work/'easyflash3.log').write_text(built.stdout)
        ef_map=ef_source/'efmenu/efmenu.bin.map'
        result['easyflash3_menu']=rom_usage(ef_map,limit=0xbf80)
        result['easyflash3_menu']['upstream_commit']=run(
            ['git','-C',args.easyflash_upstream.resolve(),'rev-parse','HEAD'],env).stdout.strip()
        result['easyflash3_menu']['image_bytes']=(ef_source/'efmenu/efmenu.bin').stat().st_size
    (work/'measurements.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
