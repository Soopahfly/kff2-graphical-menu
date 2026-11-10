#!/usr/bin/env python3
"""Check the actual new menu handler against upstream KFF buffer semantics."""
from pathlib import Path
import argparse,re,subprocess,tempfile,os
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--upstream',type=Path,required=True);a=p.parse_args()
r=Path(__file__).resolve().parents[1];source=r/'launcher/build/arm-firmware/firmware'
menu=(source/'menu.c').read_text();case=menu.split('case REPLY_HOME_ASSETS:',1)[1].split('case REPLY_OK:',1)[0].replace('break;','')
kff=(a.upstream/'firmware/cartridges/kff.c').read_text();kff=kff[kff.index('#define KFF_BUF'):kff.index('/******************************************************************************')]
commands=(a.upstream/'firmware/commands.c').read_text();send=commands[commands.index('static void c64_send_data('):commands.index('static u8 c64_wait_for_command')]
fixture='''#include <stdint.h>
#include <stdbool.h>
#define CMD_NONE 0
#include <stddef.h>
#include <string.h>
#include <assert.h>
typedef uint8_t u8; typedef uint16_t u16;
#define COMPILER_BARRIER() __asm__ volatile ("" ::: "memory")
static u8 dat_buf[65536], crt_ram_buf[256];
'''+kff+'''\nstatic void c64_send_byte(u8 x){kff_send_byte(x);}\n'''+send+'''\n#include "ui_assets.h"
static void graphics(u8 *command){u8 cmd=255;'''+case+'''*command=cmd;}
int main(void){
 u8 reply,cmd; memset(dat_buf,0xa5,sizeof(dat_buf));memset(crt_ram_buf,0,sizeof(crt_ram_buf));
 kff_set_command(1);KFF_COMMAND=0x9c;assert(kff_get_reply(1,&reply)&&reply==0x9c);
 graphics(&cmd);assert(cmd==0);assert(KFF_WRITE_PTR==16384);
 assert(!memcmp(dat_buf,ui_bank,16384));assert(dat_buf[16384]==0xa5);
 kff_set_command(cmd);assert(KFF_READ_PTR==0&&KFF_WRITE_PTR==0);
 assert(!kff_get_reply(cmd,&reply));
 for(unsigned i=0;i<16384;++i)assert(kff_receive_byte()==ui_bank[i]);
 assert(KFF_READ_PTR==16384);
 return 0;
}
'''.replace('CMD_NONE','0')
env=os.environ.copy();env.pop('C_INCLUDE_PATH',None);env['ASAN_OPTIONS']='detect_leaks=0'
with tempfile.TemporaryDirectory() as d:
 f=Path(d)/'assets.c';exe=Path(d)/'assets';f.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-fsanitize=address,undefined','-g','-I',source,f,'-o',exe],check=True,env=env)
 subprocess.run([exe],check=True,env=env)
print('ARM assets: actual reply handler, 16384 bytes, KFF pointer reset and buffer bounds passed')
