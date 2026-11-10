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
    ap.add_argument('--version',default='2.G7',help='Four-character experimental v2 version')
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
    from make_ui_bank import generate
    bank_info=generate(work/'ui-assets')
    source=work/'source'
    ignore=shutil.ignore_patterns('build','obj','*.o','*.lib','.git')
    for folder in ['launcher','3rd_party/libef3usb']:
        shutil.copytree(args.upstream.resolve()/folder,source/folder,ignore=ignore,dirs_exist_ok=True)
    (source/'firmware').mkdir(exist_ok=True)
    shutil.copy(args.upstream.resolve()/'firmware/commands.h',source/'firmware/commands.h')
    for patch in ['experiments/launcher-size/compact-launcher.patch',
                  'experiments/home-integration/home-menu.patch',
                  'experiments/home-integration/folder-home.patch',
                  'experiments/home-integration/browser.patch',
                  'experiments/home-integration/bitmap-browser.patch',
                  'experiments/home-integration/uniform-ui.patch']:
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
    for name in ['home','home_assets','browser','text_plot']:
        objects.append(cobj(launcher/'ui'/(name+'.c'),name,True))
    objects.append(aobj(launcher/'ui/text_plot_asm.s','text_plot_asm'))
    run(['make','-C',source/'3rd_party/libef3usb'],env)
    image=build/'kff2-integrated-launcher.bin'
    mapfile=build/'launcher.map'
    log=run(['ld65','-o',image,'-m',mapfile,'-Ln',build/'launcher.lbl',
             '-C',launcher/'ld.crt.cfg',*objects,'--lib',source/'3rd_party/libef3usb/libef3usb.lib','--lib','c64.lib'],env)
    (build/'link.log').write_text(log)
    from investigate_rom import rom_usage
    result=rom_usage(mapfile)
    result.update(bank_info)
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
    patched += '\n#if defined(UI_TEST_SCENARIO) && UI_TEST_SCENARIO == 9\n#include "uniform_checks.inc"\n#endif\n'
    # The mock definitions affect only this copied test header.
    header=(test/'kff_data.h').read_text()
    header=header.replace('#define KFF_SEND_BYTE(data) KFF_DATA = (data)',
                          '#define KFF_SEND_BYTE(data) ui_mock_send_byte(data)')
    header=header.replace('#define KFF_DATA        *((volatile uint8_t*) 0xde00)',
                          '#define KFF_DATA ui_mock_read_byte()')
    header=header.replace('#define KFF_READ_PTR    *((volatile uint16_t*) 0xde04)',
                          '#define KFF_READ_PTR ui_mock_read_ptr')
    header='#include "mock_backend.h"\n'+header
    (test/'kff_data.h').write_text(header)
    for f in ['mock_backend.c','mock_backend.h','uniform_checks.inc']:
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
    config=config.replace('size = __HIMEM__ - __HEADER_LAST__;','size = $9000 - __HEADER_LAST__, fill = yes;')
    config=config.replace('    BSS:      file = "", start = $8000, size = $1000;',
                          '    BSS:      file = "", start = $8000, size = $1000;\n    MOCK: file = %O, start = $9000, size = $2000;')
    config=config.replace('    ZEROPAGE: load = ZP,       type = zp;',
                          '    MOCK_ASSET: load = MOCK, type = ro;\n    MOCK_CODE: load = MOCK, type = ro, optional = yes;\n    ZEROPAGE: load = ZP,       type = zp;')
    harness_cfg.write_text(config)
    for scenario in range(10):
        output=work/('interactive' if scenario==0 else 'scenario-'+str(scenario))
        output.mkdir()
        flags=[] if scenario==0 else ['-DUI_TEST_AUTORUN','-DUI_TEST_SCENARIO='+str(scenario)]
        input_expr='c = kbhit() ? cgetc() : getJoy();'
        code=patched if scenario==0 else patched.replace(input_expr,'c = ui_test_key();')
        if scenario==9:
            code=code.replace('if (kbhit())','if (1)').replace('c = cgetc();','c = ui_test_key();')
        (test/'main.c').write_text(code)
        base_code=(launcher/'base.c').read_text()
        if scenario==9:
            base_code=base_code.replace('void waitKey(void)\n{','void waitKey(void)\n{\n    ui_test_key(); return;')
            base_code='#include "mock_backend.h"\n'+base_code
        (test/'base.c').write_text(base_code)
        ui_code=(launcher/'ui/home.c').read_text()
        if scenario:
            ui_code='#include "mock_backend.h"\n'+ui_code.replace(input_expr,'c = ui_test_key();')
        (test/'ui/home.c').write_text(ui_code)
        sources=[test/(n+'.c') for n in ['main','base','screen','dir','mock_backend']]
        sources += [test/'ui/home.c',test/'ui/home_assets.c',test/'ui/browser.c',test/'ui/text_plot.c',work/'ui-assets/mock_assets.c']
        objs=[]
        for path in sources:
            obj=output/(path.stem+'.o')
            run(['cl65','-t','c64','-O','-g','-c',
                 *(['--static-locals'] if path.stem in ['main','base','screen','dir','home','browser','text_plot'] else []),
                 define,*flags,
                 '-I',test,'-I',source/'3rd_party/libef3usb/src','-o',obj,path],env)
            objs.append(obj)
        (test/'ui/mock_unpack.s').write_text((test/'ui/folder_unpack.s').read_text().replace('_unpack_home','_unpack_home_fixture'))
        unpack=output/'folder_unpack.o'
        run(['ca65','-t','c64','-g','-o',unpack,test/'ui/mock_unpack.s'],env)
        objs.append(unpack)
        plot=output/'text_plot_asm.o'
        run(['ca65','-t','c64','-g','-I',test/'ui','-o',plot,test/'ui/text_plot_asm.s'],env)
        objs.append(plot)
        run(['cl65','-t','c64','-Wl','-D,__HIMEM__=0xc000','-C',harness_cfg,'-o',output/'kff2-integration-test.prg',
             '-m',output/'test.map','-Ln',output/'test.lbl',*objs,
             source/'3rd_party/libef3usb/libef3usb.lib'],env)
        prg=(output/'kff2-integration-test.prg').read_bytes()
        assert int.from_bytes(prg[:2],'little')==0x0801
        segments=(output/'test.map').read_text()
        for seg,start,end in re.findall(r'^(CODE|RODATA|DATA|ONCE)\s+([0-9A-F]+)\s+([0-9A-F]+)',segments,re.M):
            assert int(end,16)<0x4000,(seg,end)
        assert int.from_bytes(prg[:2],'little')+len(prg)-2<0xb000
        state=re.search(r'^BSS\s+([0-9A-F]+)\s+([0-9A-F]+)',(output/'test.map').read_text(),re.M)
        assert 0x8000<=int(state[1],16)<=int(state[2],16)<0x9000
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
