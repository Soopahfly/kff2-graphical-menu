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
from build_integrated_launcher import run


def digest(data):return hashlib.sha256(data).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--upstream',type=Path,required=True)
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
    assert len(native)==16384
    assert tests['native_image_sha256']==digest(native),'VICE results do not match this launcher build'
    assert tests['interactive_prg_sha256']==digest((ui/'interactive/kff2-integration-test.prg').read_bytes())
    assert all(r['passed'] and not r['error'] for r in tests['scenarios']) and tests['keyboard']['passed']
    env=os.environ.copy()
    if args.newlib_include:
        env['C_INCLUDE_PATH']=str(args.newlib_include.resolve())+(os.pathsep+env['C_INCLUDE_PATH'] if env.get('C_INCLUDE_PATH') else '')
    work=root/'launcher/build/arm-firmware'
    if work.exists():shutil.rmtree(work)
    source=work/'firmware'
    shutil.copytree(args.upstream.resolve()/'firmware',source,ignore=shutil.ignore_patterns('build'))
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
    result={'version':version,'experimental':True,'hardware_tested':False,
        'upstream_commit':metadata['upstream_commit'],
        'arm_compiler':run([gcc,'--version'],env).splitlines()[0],
        'cc65':metadata['cc65'],'update_bytes':len(upd),'arm_binary_bytes':len(arm),
        'launcher_offset':114688,'launcher_bytes':len(native),'launcher_rom_free':metadata['rom_free'],
        'blank_region_preserved':True,'initial_sp':hex(sp),'reset_vector':hex(reset),
        'sha256':digest(upd),'launcher_sha256':digest(native),
        'vice_harness_matches_build':True,
        'compiler_warning_kinds':sorted(set(line.strip() for line in log.splitlines() if 'warning:' in line))}
    dest=root/'firmware/experimental'
    dest.mkdir(parents=True,exist_ok=True)
    filename='KungFuFlash_v'+version+'.upd'
    (dest/filename).write_bytes(upd)
    (dest/'build-report.json').write_text(json.dumps(result,indent=2)+'\n')
    (dest/'SHA256SUMS').write_text(digest(upd)+'  '+filename+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
