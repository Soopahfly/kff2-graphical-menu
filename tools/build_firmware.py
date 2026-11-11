#!/usr/bin/env python3
"""Package experimental STM32 firmware with the current VICE-checked launcher."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys
from build_integrated_launcher import run


def digest(data):return hashlib.sha256(data).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--upstream',type=Path,required=True)
    ap.add_argument('--package-version',help='Download version, e.g. 2.G7.0.1; internal launcher identifier stays unchanged')
    ap.add_argument('--arm-bin',type=Path,help='Directory containing arm-none-eabi tools; defaults to PATH')
    ap.add_argument('--newlib-include',type=Path,help='Only needed for an unpacked toolchain without configured headers')
    ap.add_argument('--newlib-libdir',type=Path,help='Only needed for unpacked newlib archives')
    args=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    ui=root/'launcher/build/integration'
    metadata=json.loads((ui/'native-measurements.json').read_text())
    tests=json.loads((ui/'test-results.json').read_text())
    launcher=ui/'native/kff2-integrated-launcher.bin'
    native=launcher.read_bytes()
    version=metadata['version']
    package_version=args.package_version or version
    assert package_version==version or re.fullmatch(re.escape(version)+r'(?:\.\d+)+',package_version),'Package version must extend the internal version with numeric components'
    assert len(native)==16384
    assert tests['native_image_sha256']==digest(native),'VICE results do not match this launcher build'
    assert tests['interactive_prg_sha256']==digest((ui/'interactive/kff2-integration-test.prg').read_bytes())
    assert all(r['passed'] and not r['error'] for r in tests['scenarios']) and tests['keyboard']['passed']
    assert {r['scenario'] for r in tests['scenarios']}==set(range(1,9))
    assert all(r.get('browser_screen_checked') for r in tests['scenarios'] if r['scenario'] in (3,6,7))
    uniform=json.loads((ui/'uniform-results.json').read_text())
    assert uniform['native_image_sha256']==digest(native),'Uniform UI checks do not match this launcher'
    assert len(uniform['screens'])==12 and all(r['passed'] for r in uniform['screens'])
    assert uniform['reader_forward_back'] and uniform['native_fallback']
    env=os.environ.copy()
    if args.newlib_include:
        env['C_INCLUDE_PATH']=str(args.newlib_include.resolve())+(os.pathsep+env['C_INCLUDE_PATH'] if env.get('C_INCLUDE_PATH') else '')
    work=root/'launcher/build/arm-firmware'
    if work.exists():shutil.rmtree(work)
    source=work/'firmware'
    shutil.copytree(args.upstream.resolve()/'firmware',source,ignore=shutil.ignore_patterns('build'))
    shutil.copy(ui/'source/firmware/commands.h',source/'commands.h')
    run(['patch','--batch','--forward','--fuzz=0','-p1','-i',
         root/'experiments/home-integration/folder-arm.patch'],env,cwd=work)
    run(['patch','--batch','--forward','--fuzz=0','-p1','-i',root/'experiments/home-integration/history-hooks.patch'],env,cwd=work)
    run(['patch','--batch','--forward','--fuzz=0','-p1','-i',root/'experiments/home-integration/browser-arm.patch'],env,cwd=work)
    run(['patch','--batch','--forward','--fuzz=0','-p1','-i',root/'experiments/home-integration/bitmap-assets-arm.patch'],env,cwd=work)
    run(['patch','--batch','--forward','--fuzz=0','-p1','-i',root/'experiments/home-integration/g7-features.patch'],env,cwd=work)
    assert digest((ui/'ui-assets/bank.bin').read_bytes())==metadata['ui_bank_sha256']
    shutil.copy(ui/'ui-assets/ui_assets.h',source/'ui_assets.h')
    for name in ['random_game.c','menu_home.c','launch_history.c','g7_settings.c','g7_menu_settings.inc','favourites.c','menu_favourites.c']:
        shutil.copy(root/'firmware'/name,source/name)
    route_tests=run([sys.executable,root/'tools/test_home_features.py','--upstream',args.upstream.resolve()],env)
    history_tests=run([sys.executable,root/'tools/test_launch_history.py','--upstream',args.upstream.resolve()],env)
    fatfs_tests=run([sys.executable,root/'tools/test_history_fatfs.py','--upstream',args.upstream.resolve()],env)
    (work/'host-tests.log').write_text(route_tests+history_tests+fatfs_tests)
    asset_tests=run([sys.executable,root/'tools/test_ui_assets.py','--upstream',args.upstream.resolve()],env)
    g7_tests=run([sys.executable,root/'tools/test_g7_features.py','--upstream',args.upstream.resolve()],env)
    (work/'host-tests.log').write_text(route_tests+history_tests+fatfs_tests+asset_tests+g7_tests)
    options=['version='+version,'LAUNCHER='+str(launcher),'-o',launcher]
    if args.arm_bin:options.append('GCC_PATH='+str(args.arm_bin.resolve()))
    if args.newlib_libdir:options.append('LIBDIR=-L'+str(args.newlib_libdir.resolve()))
    log=run(['make','-C',source,*options],env)
    (work/'build.log').write_text(log)
    built=source/'build'/('KungFuFlash_v'+version)
    upd=Path(str(built)+'.upd').read_bytes()
    objcopy=str(args.arm_bin.resolve()/'arm-none-eabi-objcopy') if args.arm_bin else 'arm-none-eabi-objcopy'
    arm_reference=work/'arm-gap-filled.bin'
    run([objcopy,'-O','binary','--gap-fill','0xff',Path(str(built)+'.elf'),arm_reference],env)
    arm=arm_reference.read_bytes()
    assert len(upd)==131072
    assert len(arm)<=98304 and upd[:len(arm)]==arm
    assert upd[98304:114688]==b'\xff'*16384
    assert upd[114688:]==native
    identifier=bytes((b&127) if b&128 else b+32 if 65<=b<=90 else b for b in native[:20]).split(b'\0')[0].decode('ascii')
    assert identifier=='Kung Fu Flash v'+version
    sp,reset=struct.unpack('<II',upd[:8])
    assert sp==0x20020000 and reset&1 and 0x08000000<=(reset&~1)<0x08018000
    gcc=str(args.arm_bin.resolve()/'arm-none-eabi-gcc') if args.arm_bin else 'arm-none-eabi-gcc'
    size_tool=str(args.arm_bin.resolve()/'arm-none-eabi-size') if args.arm_bin else 'arm-none-eabi-size'
    size_text=run([size_tool,'-A',Path(str(built)+'.elf')],env)
    bss=re.search(r'^\.bss\s+(\d+)\s+(\d+)',size_text,re.M)
    result={'arm_bss_bytes':int(bss[1]),'arm_bss_end':hex(int(bss[1])+int(bss[2])),
        'version':version,'experimental':True,'hardware_tested':False,
        'upstream_commit':metadata['upstream_commit'],
        'arm_compiler':run([gcc,'--version'],env).splitlines()[0],
        'cc65':metadata['cc65'],'update_bytes':len(upd),'arm_binary_bytes':len(arm),
        'launcher_offset':114688,'launcher_bytes':len(native),'launcher_rom_free':metadata['rom_free'],
        'blank_region_preserved':True,'initial_sp':hex(sp),'reset_vector':hex(reset),
        'sha256':digest(upd),'launcher_sha256':digest(native),
        'vice_harness_matches_build':True,'ui_bank_sha256':metadata['ui_bank_sha256'],'arm_supplied_home_font_bank':True,'browser_visible_rows':12,'browser_home_border_exact':True,'browser_f4_random':True,'sd_extension_labels':True,'folder_shortcuts':True,'arm_source_changed':True,
        'uniform_menus_help_search':True,'cached_message_frame':True,'reader_columns':32,'reader_rows':16,'uniform_ui_checked_screens':12,'startup_text_fallback':True,
        'upstream_release':'v2.07','upstream_commits_after_release':1,'favourites_copy':True,'reu_sizes_kb':[256,512,1024],'autoboot_toggle':True,'config_layout_unchanged':True,
        'home_graphics_lossless':True,'random_game_f4':True,'persistent_history':True,'history_real_fatfs_tested':True,'recent_distinct_window':10,'menu_context_regressions_tested':True,'arm_folder_dispatch_host_tested':True,
        'compiler_warning_kinds':sorted(set(line.strip() for line in log.splitlines() if 'warning:' in line))}
    dest=root/'firmware/experimental'
    dest.mkdir(parents=True,exist_ok=True)
    if package_version!=version:
        result['package_version']=package_version
    result['favourites_acknowledgement_sync']=True
    filename='KungFuFlash_v'+package_version+'.upd'
    (dest/filename).write_bytes(upd)
    (dest/'build-report.json').write_text(json.dumps(result,indent=2)+'\n')
    (dest/'SHA256SUMS').write_text(''.join(digest(p.read_bytes())+'  '+p.name+'\n' for p in sorted(dest.glob('*.upd'))))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
