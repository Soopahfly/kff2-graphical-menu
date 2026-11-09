#!/usr/bin/env python3
"""Host-check the exact patched ARM folder dispatcher with filesystem doubles."""
from pathlib import Path
import argparse,subprocess,tempfile,os
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('menu',type=Path);args=ap.parse_args()
source=args.menu.read_text();case=source.split('            case REPLY_HOME_FOLDER:',1)[1].split('            case REPLY_UTILITIES:',1)[0]
pre=r'''
#include <assert.h>
#include <stdbool.h>
#include <string.h>
#include <stdint.h>
typedef uint8_t u8;
#define CMD_NONE 0
struct {char search[32];} sd_state;
struct {char file[64];} cfg_file;
static int sd_menu,other_menu;
static int *menu;
static int input,reads,warning,changes,missing,unsaved,prompt,failure;
static char requested[2][32];
static u8 c64_receive_byte(void){++reads;return input;}
static bool sd_crt_updated(void *s){(void)s;return unsaved;}
static void sd_handle_save_updated_crt(u8 n){(void)n;}
static u8 handle_unsaved_crt(char *f,void(*cb)(u8)){
 assert(strcmp(f,"modified.crt")==0);assert(cb==sd_handle_save_updated_crt);++prompt;return 3;
}
static bool dir_change(const char *path){strcpy(requested[changes++],path);return !(missing && changes==1);}
static u8 handle_unsupported_ex(const char *title,const char *message,const char *path){assert(strstr(title,"Folder"));assert(strstr(message,"folder"));assert(!strcmp(path,"/Games"));++warning;return 4;}
static void fail_to_read_sd(void){++failure;}
static u8 sd_handle_dir(void *s){assert(s==&sd_state);return 2;}
static u8 dispatch(void){u8 data,cmd=99;switch(0){case 0:
'''
browse=source.split('            case REPLY_HOME_BROWSE:',1)[1].split('            /* Altered version:',1)[0]
post=r'''
}return cmd;}
static void reset(void){menu=&other_menu;reads=warning=changes=prompt=failure=0;unsaved=missing=0;strcpy(cfg_file.file,"modified.crt");strcpy(sd_state.search,"filter");memset(requested,0,sizeof(requested));}
static u8 dispatch_browse(void);
int main(void){
 const char *expected[]={"/Games","/Tools","/Utilities","/Favourites"};
 for(input=0;input<4;++input){reset();assert(dispatch()==2);assert(reads==1&&changes==1&&menu==&sd_menu);assert(!strcmp(requested[0],expected[input]));assert(!cfg_file.file[0]&&!sd_state.search[0]);assert(!warning&&!failure);}
 input=4;reset();assert(dispatch()==0);assert(reads==1&&!changes&&menu==&other_menu);assert(!strcmp(cfg_file.file,"modified.crt"));
 input=0;reset();missing=1;assert(dispatch()==4);assert(warning==1&&changes==2&&!strcmp(requested[1],"/"));
 input=0;reset();unsaved=1;assert(dispatch()==3);assert(prompt==1&&!changes);assert(!strcmp(cfg_file.file,"modified.crt")&&!strcmp(sd_state.search,"filter"));
 reset();menu=&sd_menu;assert(dispatch_browse()==0&&menu==&sd_menu&&!changes);
 reset();assert(dispatch_browse()==2&&menu==&sd_menu&&!changes);
 return 0;
}
'''
env=os.environ.copy();env.pop('C_INCLUDE_PATH',None)
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'routes.c').write_text(pre+case+post+'\nstatic u8 dispatch_browse(void){u8 cmd=99;switch(0){case 0:'+browse+'}return cmd;}\n')
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',p/'routes.c','-o',p/'routes'],check=True,env=env)
 subprocess.run([p/'routes'],check=True,env=env)
print('ARM folder routes: four paths, invalid index, missing-folder fallback and unsaved-CRT guard and Browse context return passed')
