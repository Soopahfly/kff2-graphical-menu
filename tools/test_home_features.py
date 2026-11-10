#!/usr/bin/env python3
"""Compile the actual ARM Home/random code with filesystem and loader test doubles."""
from pathlib import Path
import argparse,os,subprocess,tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--upstream',required=True,type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[1]
fs=(a.upstream/'firmware/filesystem.c').read_text()
read=fs[fs.index('static bool dir_read('):fs.index('static bool dir_close(')]
u=(a.upstream/'firmware/menu_utilities.c').read_text();utilities='static u8 handle_utilities(void)'+u.split('static u8 handle_utilities(void)',1)[1]
source=(root/'tests/home_features.c').read_text().replace('@DIR_READ@',read).replace('@UTILITIES@',utilities).replace('@RANDOM@',(root/'firmware/random_game.c').read_text()).replace('@HOME@',(root/'firmware/menu_home.c').read_text())
env=os.environ.copy();env.pop('C_INCLUDE_PATH',None)
# Address/undefined checks remain enabled; leak checking is incompatible with traced hosts.
env['ASAN_OPTIONS']='detect_leaks=0'
with tempfile.TemporaryDirectory(prefix='kff-home-tests-') as d:
 f=Path(d)/'home.c';exe=Path(d)/'home-tests';f.write_text(source)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fsanitize=address,undefined','-g',f,'-o',exe],env=env,check=True)
 subprocess.run([exe],env=env,check=True)
