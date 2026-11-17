#!/usr/bin/env python3
"""Regression-test the actual prepared G8 loader, with G7 negative controls."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
from assess_upstream import BASE, TYPES, LOADER_TEST, function


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--upstream',type=Path,required=True)
    ap.add_argument('--source',type=Path,required=True,help='Prepared ARM source after all patches')
    args=ap.parse_args()
    def original(path):
        return subprocess.check_output(['git','-C',str(args.upstream),'show',BASE+':firmware/'+path],text=True)
    base=original('loader.c')
    fixed=(args.source/'loader.c').read_text()
    baseline=function(base,'static u8 crt_load_file(')
    selected=function(fixed,'static u8 crt_load_file(')
    assert baseline.count('continue;   // Skip image')==1
    expected=baseline.replace('continue;   // Skip image','return 0;   // Reject incomplete cartridge; do not parse skipped payload.')
    assert selected==expected,'Prepared firmware does not contain the assessed parser fix'
    skip=baseline.replace('continue;   // Skip image','if (!file_seek(crt_file, f_tell(crt_file) + header.image_size)) return 0;\n            continue;')
    funcs=function(fixed,'static bool crt_load_chip_header(')+'\n'+function(fixed,'static s32 crt_get_offset(')
    funcs+='\n'+baseline.replace('crt_load_file','baseline_load')+'\n'+skip.replace('crt_load_file','skip_load')+'\n'+selected.replace('crt_load_file','reject_load')
    env=os.environ.copy()
    env.pop('C_INCLUDE_PATH',None)
    env['ASAN_OPTIONS']='detect_leaks=0'
    with tempfile.TemporaryDirectory(prefix='kff-crt-test-') as tmp:
        src=Path(tmp)/'test.c';exe=Path(tmp)/'test'
        src.write_text(TYPES+original('file_types.h')+LOADER_TEST.replace('@FUNCTIONS@',funcs))
        subprocess.run(['gcc','-std=c11','-Os','-g','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-variable','-fsanitize=address,undefined',str(src),'-o',str(exe)],env=env,check=True)
        results=json.loads(subprocess.check_output([str(exe)],env=env,text=True))
    results['prepared_source_tested']=True
    results['address_and_undefined_sanitizers']=True
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    main()
