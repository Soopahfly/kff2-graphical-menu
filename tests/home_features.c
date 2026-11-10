/* Host fixture for the actual Home handlers and random scanner. */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef uint8_t u8;
typedef uint32_t u32;
typedef int FRESULT;
#define FR_OK 0
#define CMD_NONE 0
#define CMD_READ_DIR 9
#define CMD_WAIT_SYNC 80
#define ELEMENT_NOT_SELECTED 65535
#define SELECT_FLAG_C128 0x80
#define SELECT_FLAG_MOUNT 2
#define CRT_C128_CARTRIDGE 0x8000
#define CFG_NONE 0
#define CFG_DISK 1
#define DISK_MODE_FS 1
#define AM_HID 2
#define AM_SYS 4
#define FILE_CRT 1
#define FILE_PRG 2
#define FILE_P00 3
#define FILE_D64 4
#define FILE_T64 5
#define FILE_DIR 6
#define FILE_UPD 7
#define FILE_TXT 8
#define FILE_ROM 9
struct MENU_s {void *state;u8(*dir)(void*);};
typedef struct MENU_s MENU;
static u8 image_dir(void*s){(void)s;return CMD_READ_DIR;}
static const MENU sd_menu={0,0},d64_menu={0,image_dir},t64_menu={0,image_dir},options_menu={0,0};
static const MENU *menu;
static struct {const MENU*prev_menu;} options_state;
static struct {int image;} d64_state,t64_state;
static struct {char search[32];} sd_state;
static struct {char path[750],file[256];int boot_type;struct{int element,mode;}img;}cfg_file;
typedef struct {char fname[256];u8 fattrib,type;} FILINFO;
typedef struct {unsigned int index;char path[750];const char*pat;} DIR_t;
typedef int FIL;
typedef struct {u32 cartridge_type;}CRT_HEADER;
static struct {u32 CYCCNT;}dwt;
#define DWT (&dwt)
static int active_dirs,read_failure,missing,empty,deep,long_names,changes;
static int d64_closed,t64_closed,reopened,unsaved,prompts,errors,options_opened,loaded,tape_loaded;
static u8 loaded_type,loaded_flags;
static bool header_valid;
static u32 cartridge_type;
static bool history_random_origin;
static u8 history_age(const char *folder,const char *file){(void)folder;(void)file;return 0;}
static char cwd[750];
static const struct{const char*parent,*name;u8 type,attr;}entries[]={
 {"/Games","one.crt",FILE_CRT,0},{"/Games","notes.txt",FILE_TXT,0},
 {"/Games","upgrade.upd",FILE_UPD,0},{"/Games",".hidden.prg",FILE_PRG,0},
 {"/Games","hidden.crt",FILE_CRT,AM_HID},{"/Games","system.crt",FILE_CRT,AM_SYS},
 {"/Games","raw.rom",FILE_ROM,0},{"/Games","Sub",FILE_DIR,0},
 {"/Games/Sub","two.prg",FILE_PRG,0},{"/Games/Sub","three.p00",FILE_P00,0},
 {"/Games/Sub","Nested",FILE_DIR,0},
 {"/Games/Sub/Nested","four.d64",FILE_D64,0},{"/Games/Sub/Nested","five.t64",FILE_T64,0}
};
static FRESULT f_opendir(DIR_t*d,const char*p){
 if(missing)return 1;d->index=0;strcpy(d->path,p);++active_dirs;return FR_OK;
}
static FRESULT f_findnext(DIR_t*d,FILINFO*i){
 if(read_failure)return 1;
 memset(i,0,sizeof(*i));if(empty)return FR_OK;
 if(deep||long_names){if(!d->index++){i->type=FILE_DIR;if(long_names){memset(i->fname,'x',255);i->fname[255]=0;}else strcpy(i->fname,"D");}return FR_OK;}
 while(d->index<sizeof(entries)/sizeof(entries[0])){
  unsigned int n=d->index++;
  if(!strcmp(entries[n].parent,d->path)){strcpy(i->fname,entries[n].name);i->type=entries[n].type;i->fattrib=entries[n].attr;break;}
 }return FR_OK;
}
static FRESULT f_closedir(DIR_t*d){(void)d;--active_dirs;return FR_OK;}
#define err(...) ((void)0)
static void led_on(void){}
/* The real upstream dir_read filtering routine is inserted here. */
@DIR_READ@
static bool dir_close(DIR_t*d){return f_closedir(d)==FR_OK;}
static u8 get_file_type(FILINFO*i){return i->type;}
static bool dir_change(const char*p){++changes;strcpy(cwd,p);return true;}
static bool dir_current(char*p,size_t n){assert(strlen(cwd)<n);strcpy(p,cwd);return true;}
static bool sd_crt_updated(void*s){(void)s;return unsaved;}
static void sd_handle_save_updated_crt(u8 n){(void)n;}
static u8 handle_unsaved_crt(const char*f,void(*cb)(u8)){assert(!strcmp(f,"modified.crt"));assert(cb==sd_handle_save_updated_crt);++prompts;return 13;}
static void d64_close(void*i){assert(i==&d64_state.image);++d64_closed;}
static void t64_close(void*i){assert(i==&t64_state.image);++t64_closed;}
static u8 sd_handle_dir(void*s){
 assert(s==&sd_state);
 /* Exercise upstream's automatic image reopening condition. */
 if(cfg_file.img.element!=ELEMENT_NOT_SELECTED&&cfg_file.file[0]){++reopened;menu=&d64_menu;}
 return CMD_READ_DIR;
}
static void fail_to_read_sd(void){assert(!"unexpected SD failure");}
static u8 handle_unsupported_ex(const char*t,const char*m,const char*f){assert(t&&m&&f);++errors;return CMD_READ_DIR;}
static u8 handle_unsupported(const char*f){return handle_unsupported_ex("Unsupported","Invalid file",f);}
static void sd_file_open(FIL*f,const char*n){(void)n;*f=1;}
static bool crt_load_header(FIL*f,CRT_HEADER*h){assert(*f==1);h->cartridge_type=cartridge_type;return header_valid;}
static void file_close(FIL*f){assert(*f==1);*f=0;}
static u8 sd_handle_load(void*s,const char*f,u8 type,u8 flags,u8 item){assert(s==&sd_state);assert(!strcmp(f,cfg_file.file));assert(item==0);loaded_type=type;loaded_flags=flags;++loaded;return CMD_WAIT_SYNC;}
static u8 t64_load_first(const char*f){assert(!strcmp(f,cfg_file.file));++tape_loaded;return CMD_WAIT_SYNC;}
typedef int OPTIONS_STATE;
static OPTIONS_STATE*options_init(const char*t){assert(!strcmp(t,"Utilities"));++options_opened;return 0;}
#define utilities_sort_dir 0
static void options_add_text_element(OPTIONS_STATE*s,int cb,const char*t){(void)s;(void)cb;(void)t;}
static void options_add_dir(OPTIONS_STATE*s,const char*t){(void)s;(void)t;}
static u8 handle_options(void){return CMD_READ_DIR;}
/* The actual upstream utilities guard, not an always-successful mock. */
@UTILITIES@
@RANDOM@
@HOME@
static void reset(void){
 memset(&cfg_file,0,sizeof(cfg_file));strcpy(cfg_file.path,"/Old");strcpy(cfg_file.file,"modified.crt");strcpy(cwd,"/Old");strcpy(sd_state.search,"filter");cfg_file.img.element=ELEMENT_NOT_SELECTED;
 menu=&sd_menu;options_state.prev_menu=&sd_menu;
 active_dirs=read_failure=missing=empty=deep=long_names=changes=0;
 d64_closed=t64_closed=reopened=unsaved=prompts=errors=options_opened=loaded=tape_loaded=0;
 cartridge_type=0;header_valid=true;random_state=0;dwt.CYCCNT=123456;
}
static u32 seed_for(u8 type){
 for(u32 seed=1;seed<10000;++seed){random_state=0;assert(random_pick(seed));if(random_type==type)return seed;}
 assert(!"unreachable file type");return 0;
}
int main(void){
 reset();unsigned int counts[6]={0};
 for(u32 seed=1;seed<=10000;++seed){random_state=0;assert(random_pick(seed));assert(random_count==5&&active_dirs==0&&changes==0);assert(!strcmp(cwd,"/Old"));assert(random_type>=1&&random_type<=5);++counts[random_type];}
 for(int i=1;i<=5;++i)assert(counts[i]>1500&&counts[i]<2500);
 reset();missing=1;assert(!random_pick(1)&&active_dirs==0);
 reset();empty=1;assert(random_pick(1)&&random_count==0&&active_dirs==0);
 reset();read_failure=1;assert(!random_pick(1)&&active_dirs==0);
 reset();deep=1;assert(!random_pick(1)&&active_dirs==0);
 reset();long_names=1;assert(!random_pick(1)&&active_dirs==0);
 reset();menu=&d64_menu;cfg_file.img.element=0;assert(home_browse()==CMD_READ_DIR&&menu==&sd_menu&&d64_closed==1&&!reopened);
 reset();menu=&t64_menu;cfg_file.img.element=0;assert(home_browse()==CMD_READ_DIR&&menu==&sd_menu&&t64_closed==1&&!reopened);
 reset();menu=&options_menu;options_state.prev_menu=&d64_menu;cfg_file.img.element=0;assert(home_browse()==CMD_READ_DIR&&menu==&sd_menu&&d64_closed==1&&!reopened);
 reset();assert(home_browse()==CMD_NONE&&!changes&&!reopened);
 reset();menu=&options_menu;assert(home_utilities()==CMD_READ_DIR&&menu==&sd_menu&&options_opened==1);
 for(u8 i=0;i<4;++i){reset();menu=&d64_menu;cfg_file.img.element=0;assert(home_folder(i)==CMD_READ_DIR&&d64_closed==1&&!reopened&&!cfg_file.file[0]&&!sd_state.search[0]);}
 reset();assert(home_folder(4)==CMD_NONE&&!changes);
 reset();unsaved=1;assert(home_random(0)==13&&prompts==1&&!changes&&!loaded&&!strcmp(cfg_file.file,"modified.crt"));
 reset();empty=1;assert(home_random(0)==CMD_READ_DIR&&errors==1&&!loaded);
 reset();missing=1;assert(home_random(0)==CMD_READ_DIR&&errors==1&&!loaded);
 for(u8 type=1;type<=5;++type){reset();u32 seed=seed_for(type);reset();dwt.CYCCNT=seed;assert(home_random(0)==CMD_WAIT_SYNC&&active_dirs==0);assert(!strcmp(cfg_file.path,random_folder)&&!strcmp(cfg_file.file,random_file));
  if(type==FILE_PRG)assert(!loaded&&cfg_file.boot_type==CFG_DISK&&cfg_file.img.mode==DISK_MODE_FS);
  else if(type==FILE_T64)assert(tape_loaded==1&&!loaded);
  else {assert(loaded==1&&loaded_type==type);if(type==FILE_D64)assert((loaded_flags&SELECT_FLAG_MOUNT)&&cfg_file.img.element==0);}
 }
 reset();u32 seed=seed_for(FILE_CRT);reset();dwt.CYCCNT=seed;cartridge_type=CRT_C128_CARTRIDGE;assert(home_random(0)==CMD_READ_DIR&&errors==1&&!loaded);
 reset();dwt.CYCCNT=seed;cartridge_type=CRT_C128_CARTRIDGE;assert(home_random(SELECT_FLAG_C128)==CMD_WAIT_SYNC&&loaded_flags==SELECT_FLAG_C128);
 printf("PASS: 10000 selection seeds, nested/hidden/non-game files, error cleanup, all five launch paths, C128 guard, image exits and F3 context\n");
 return 0;
}
