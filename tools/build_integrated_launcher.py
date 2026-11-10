#!/usr/bin/env python3
"""Build the compact launcher with the graphical home screen (not an MCU update)."""
import argparse
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys


def run(args,env,cwd=None):
    r=subprocess.run([str(a) for a in args],env=env,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    if r.returncode:raise RuntimeError(' '.join(map(str,args))+'\n'+r.stdout)
    return r.stdout


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--upstream',type=Path,required=True)
    ap.add_argument('--cc65-home',type=Path)
    ap.add_argument('--version',default='2.G2',help='Four-character experimental v2 version')
    args=ap.parse_args()
    if not re.fullmatch(r'2\.[A-Za-z0-9]{2}',args.version):
        raise ValueError('Version must fit the 20-byte launcher identifier, for example 2.G1')
    define='-DKFF_VER="'+args.version+'"'
    root=Path(__file__).resolve().parents[1]
    work=root/'launcher/build/integration'
    if work.exists():shutil.rmtree(work)
    work.mkdir(parents=True)
    env=os.environ.copy()
    if args.cc65_home:
        env['CC65_HOME']=str(args.cc65_home.resolve())
        env['PATH']=str(args.cc65_home.resolve()/'bin')+os.pathsep+env['PATH']
    source=work/'source'
    ignore=shutil.ignore_patterns('build','obj','*.o','*.lib','.git')
    for folder in ['launcher','3rd_party/libef3usb']:
        shutil.copytree(args.upstream.resolve()/folder,source/folder,ignore=ignore,dirs_exist_ok=True)
    (source/'firmware').mkdir(exist_ok=True)
    shutil.copy(args.upstream.resolve()/'firmware/commands.h',source/'firmware/commands.h')
    for patch in ['experiments/launcher-size/compact-launcher.patch',
                  'experiments/home-integration/home-menu.patch',
                  'experiments/home-integration/folder-home.patch']:
        run(['patch','--batch','--forward','--fuzz=0','-p1','-i',root/patch],env,cwd=source)
    shutil.copytree(root/'launcher/ui',source/'launcher/ui',dirs_exist_ok=True)
    launcher=source/'launcher'
    build=work/'native'
    build.mkdir()
    inc=['-I',launcher,'-I',source/'3rd_party/libef3usb/src']
    objects=[]
    def cobj(path,name,static=False):
        asm=build/(name+'.s');obj=build/(name+'.o')
        run(['cc65','-t','c64','-O','-g',*(['--static-locals'] if static else []),
             define,*inc,'-o',asm,path],env)
        run(['ca65','-t','c64','-g',*inc,'-o',obj,asm],env)
        return obj
    def aobj(path,name):
        obj=build/(name+'.o')
        run(['ca65','-t','c64','-g',*inc,'-I',launcher/'ui','-o',obj,path],env)
        return obj
    objects.append(aobj(launcher/'crt0.crt.s','crt0.crt'))
    for name in ['main','base','screen','dir','kff_data']:
        objects.append(cobj(launcher/(name+'.c'),name,True))
    for name in ['disk','ef3usb_loader','launcher_asm']:
        objects.append(aobj(launcher/(name+'.s'),name))
    for name in ['home']:
        objects.append(cobj(launcher/'ui'/(name+'.c'),name,True))
    objects.append(aobj(launcher/'ui/folder_unpack.s','folder_unpack'))
    run(['make','-C',source/'3rd_party/libef3usb'],env)
    image=build/'kff2-integrated-launcher.bin'
    mapfile=build/'launcher.map'
    log=run(['ld65','-o',image,'-m',mapfile,'-Ln',build/'launcher.lbl',
             '-C',launcher/'ld.crt.cfg',*objects,'--lib',source/'3rd_party/libef3usb/libef3usb.lib','--lib','c64.lib'],env)
    (build/'link.log').write_text(log)
    from investigate_rom import rom_usage
    result=rom_usage(mapfile)
    result['image_bytes']=image.stat().st_size
    result['version']=args.version
    result['cc65']=run(['cc65','--version'],env).strip()
    result['upstream_commit']=run(['git','-C',args.upstream.resolve(),'rev-parse','HEAD'],env).strip()
    assert result['image_bytes']==16384
    assert result['rom_free']>=0
    assert result['segments']['BSS']['end']<0xc800
    (work/'native-measurements.json').write_text(json.dumps(result,indent=2)+'\n')
    # PRG harness: retain native menu/readDir code, replace only hardware I/O.
    test=work/'vice'
    shutil.copytree(launcher,test,ignore=ignore,dirs_exist_ok=True)
    patched=(test/'main.c').read_text().replace('int main(void)','int launcher_main(void)',1)
    patched='#include "mock_backend.h"\n'+patched
    patched += """
void ui_test_init(void) {
    dir = &directory; bigBuffer = (uint8_t*)dir; pageBuffer = (uint16_t*)dir;
    initScreen(COLOR_BLACK, COLOR_BLACK, TEXTC);
    joy_install(&joy_static_stddrv);
    isC128 = false;
}
uint8_t ui_test_menu(void) { return menuLoop(); }
uint8_t ui_test_row(void) { return dir->selected; }
"""
    # The mock definitions affect only this copied test header.
    header=(test/'kff_data.h').read_text()
    header=header.replace('#define KFF_SEND_BYTE(data) KFF_DATA = (data)',
                          '#define KFF_SEND_BYTE(data) ui_mock_send_byte(data)')
    header='#include "mock_backend.h"\n'+header
    (test/'kff_data.h').write_text(header)
    for f in ['mock_backend.c','mock_backend.h']:
        shutil.copy(root/'launcher/integration'/f,test/f)
    # Preserve ../firmware/commands.h for the copied dir.h.
    (work/'firmware').mkdir(exist_ok=True)
    shutil.copy(source/'firmware/commands.h',work/'firmware/commands.h')
    # VICE-only state lives outside the graphical bank; cc65 CRT banks BASIC out.
    cfg=Path(env.get('CC65_HOME','/usr/share/cc65'))/'cfg/c64.cfg'
    harness_cfg=work/'harness.cfg'
    config=cfg.read_text()
    config=re.sub(r'BSS:      file = "",[^\n]+',
                  'BSS:      file = "", start = $8000, size = $1000;',config)
    harness_cfg.write_text(config)
    for scenario in range(6):
        output=work/('interactive' if scenario==0 else 'scenario-'+str(scenario))
        output.mkdir()
        flags=[] if scenario==0 else ['-DUI_TEST_AUTORUN','-DUI_TEST_SCENARIO='+str(scenario)]
        input_expr='c = kbhit() ? cgetc() : getJoy();'
        code=patched if scenario==0 else patched.replace(input_expr,'c = ui_test_key();')
        (test/'main.c').write_text(code)
        ui_code=(launcher/'ui/home.c').read_text()
        if scenario:
            ui_code='#include "mock_backend.h"\n'+ui_code.replace(input_expr,'c = ui_test_key();')
        (test/'ui/home.c').write_text(ui_code)
        sources=[test/(n+'.c') for n in ['main','base','screen','dir','mock_backend']]
        sources += [test/'ui/home.c']
        objs=[]
        for path in sources:
            obj=output/(path.stem+'.o')
            run(['cl65','-t','c64','-O','-g','-c',
                 *(['--static-locals'] if path.stem in ['main','base','screen','dir','home'] else []),
                 define,*flags,
                 '-I',test,'-I',source/'3rd_party/libef3usb/src','-o',obj,path],env)
            objs.append(obj)
        unpack=output/'folder_unpack.o'
        run(['ca65','-t','c64','-g','-o',unpack,test/'ui/folder_unpack.s'],env)
        objs.append(unpack)
        run(['cl65','-t','c64','-Wl','-D,__HIMEM__=0xc000','-C',harness_cfg,'-o',output/'kff2-integration-test.prg',
             '-m',output/'test.map','-Ln',output/'test.lbl',*objs,
             source/'3rd_party/libef3usb/libef3usb.lib'],env)
        prg=(output/'kff2-integration-test.prg').read_bytes()
        assert int.from_bytes(prg[:2],'little')+len(prg)-2<=0x4000
        state=re.search(r'^BSS\s+([0-9A-F]+)\s+([0-9A-F]+)',(output/'test.map').read_text(),re.M)
        assert 0x8000<=int(state[1],16)<=int(state[2],16)<0x9000
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
