#!/usr/bin/env python3
"""Exercise the real journal and patched pre-handoff loader cases on a host file."""
from pathlib import Path
import argparse,os,subprocess,tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--upstream',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='kff-history-') as d:
 work=Path(d);(work/'firmware').mkdir()
 loader=work/'firmware/loader.c';loader.write_bytes((a.upstream/'firmware/loader.c').read_bytes())
 (work/'firmware/main.c').write_bytes((a.upstream/'firmware/main.c').read_bytes())
 subprocess.run(['patch','--batch','--forward','--fuzz=0','-p1','-i',root/'experiments/home-integration/history-hooks.patch'],cwd=work,check=True,stdout=subprocess.PIPE)
 source=loader.read_text().split('static bool c64_set_mode(void)',1)[1]
 cases='case CFG_PRG:'+source.split('case CFG_PRG:',1)[1].split('case CFG_USB:',1)[0]
 cases+='case CFG_DISK:'+source.split('case CFG_DISK:',1)[1].split('case CFG_TXT:',1)[0]
 text=(root/'tests/launch_history.c').read_text().replace('@HISTORY@',(root/'firmware/launch_history.c').read_text()).replace('@MODE_CASES@',cases).replace('@RANDOM@',(root/'firmware/random_game.c').read_text())
 f=work/'test.c';f.write_text(text);exe=work/'test';env=os.environ.copy();env.pop('C_INCLUDE_PATH',None);env['ASAN_OPTIONS']='detect_leaks=0'
 subprocess.run(['gcc','-D_POSIX_C_SOURCE=200809L','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined',f,'-o',exe],check=True,env=env)
 subprocess.run([exe,work/'history.bin'],check=True,env=env)

 from history_report import read_history
 rows,warning=read_history(work/'history.bin')
 assert warning is None and rows==[{'path':'/games/golden.prg','launches':2,'random_launches':1,'manual_launches':1,'last_launch':2,'last_source':'random'}],rows
 print('PASS: independent PC report matches journal counts and launch origin')
