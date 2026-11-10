#!/usr/bin/env python3
"""Test the journal with upstream FatFs on a RAM-backed FAT32 block device."""
from pathlib import Path
import argparse,os,shutil,subprocess,tempfile
from history_report import read_history
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--upstream',required=True,type=Path);a=p.parse_args();root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='kff-fatfs-') as d:
 work=Path(d);fs=work/'fatfs';shutil.copytree(a.upstream/'firmware/fatfs',fs)
 config=fs/'ffconf.h';config.write_text(config.read_text().replace('#define FF_USE_MKFS\t\t0','#define FF_USE_MKFS\t\t1'))
 source=work/'test.c';source.write_text((root/'tests/history_fatfs.c').read_text().replace('@HISTORY@',(root/'firmware/launch_history.c').read_text()))
 env=os.environ.copy();env.pop('C_INCLUDE_PATH',None);env['ASAN_OPTIONS']='detect_leaks=0'
 exe=work/'test';subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Wno-unused-function','-Wno-unused-parameter','-fsanitize=address,undefined','-I',fs,source,fs/'ff.c',fs/'ffunicode.c','-o',exe],check=True,env=env)
 journal=work/'journal.bin';subprocess.run([exe,journal],check=True,env=env)
 rows,warning=read_history(journal);assert warning is None and rows[0]['launches']==3 and rows[0]['random_launches']==2,rows
 print('PASS: exported real-FatFs journal matches independent PC decoder')
