/* Host fixture uses a real local file for FatFs-style journal operations. */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;typedef unsigned int UINT;typedef uint32_t FSIZE_t;typedef int FRESULT;
#define FR_OK 0
#define FR_NO_FILE 4
#define FA_READ 1
#define FA_WRITE 2
#define FA_OPEN_ALWAYS 16
#define CFG_DISK 1
#define CFG_PRG 2
#define CFG_CRT 3
#define DISK_MODE_D64 2
#define ELEMENT_NOT_SELECTED 65535
#define CFG_FLAG_AUTOSTART_D64 1
#define FILE_PRG 1
#define FILE_P00 2
#define FILE_CRT 3
#define FILE_ROM 4
#define FILE_D64 5
#define FILE_T64 6
#define FILE_DIR 7
typedef struct {FILE *fp;FSIZE_t fptr;} FIL;
typedef struct {u8 type;char fname[256];}FILINFO;
static struct {char path[750],file[256];int boot_type;unsigned int flags;struct{int mode,element;}img;struct{int type;}crt;}cfg_file;
static bool deny_io,fail_read,fail_sync,short_write,game_enabled;
static int open_files,writes;
static char disk_file[2048];
static u8 stat_type=FILE_PRG;
static FRESULT f_open(FIL*f,const char*p,u8 mode){
 assert(strcmp(p,"/.KFF2-history")==0);if(deny_io)return 1;
 f->fp=fopen(disk_file,(mode&FA_WRITE)?"r+b":"rb");
 if(!f->fp&&(mode&FA_OPEN_ALWAYS))f->fp=fopen(disk_file,"w+b");
 f->fptr=0;if(!f->fp)return FR_NO_FILE;++open_files;return FR_OK;
}
static FRESULT f_read(FIL*f,void*p,UINT n,UINT*got){if(fail_read)return 1;*got=(UINT)fread(p,1,n,f->fp);f->fptr+=*got;return ferror(f->fp)?1:0;}
static FRESULT f_close(FIL*f){--open_files;return fclose(f->fp)?1:0;}
static FSIZE_t f_tell(FIL*f){return f->fptr;}
static FRESULT f_lseek(FIL*f,FSIZE_t n){if(fseek(f->fp,n,SEEK_SET))return 1;f->fptr=n;return 0;}
static FRESULT f_truncate(FIL*f){assert(!game_enabled);return ftruncate(fileno(f->fp),f->fptr)?1:0;}
static FRESULT f_write(FIL*f,const void*p,UINT n,UINT*wrote){assert(!game_enabled);++writes;if(short_write)n/=2;*wrote=(UINT)fwrite(p,1,n,f->fp);f->fptr+=*wrote;return ferror(f->fp)?1:0;}
static FRESULT f_sync(FIL*f){if(fail_sync)return 1;return fflush(f->fp)?1:0;}
static bool file_stat(const char*p,FILINFO*i){(void)p;i->type=stat_type;return true;}
static u8 get_file_type(FILINFO*i){return i->type;}
@HISTORY@
#define FILE_DIR 7
static const char*pool[]={"One.prg","Two.prg","Three.prg","Four.prg","Five.prg"};
static unsigned int pool_size=5;
typedef struct {unsigned int index;const char*pat;}DIR_t;
static FRESULT f_opendir(DIR_t*d,const char*p){assert(!strcmp(p,"/Games"));d->index=0;return FR_OK;}
static bool dir_read(DIR_t*d,FILINFO*i){memset(i,0,sizeof(*i));if(d->index<pool_size){strcpy(i->fname,pool[d->index++]);i->type=FILE_PRG;}return true;}
static bool dir_close(DIR_t*d){(void)d;return true;}
@RANDOM@
/* PRG, CRT and disk cases are extracted from the actual patched loader. */
static bool good_load=true,supported=true,valid_crt=true;
static char scratch_buf[64];
static bool c64_is_reset(void){return true;}
static void c64_interface_sync(void){}
static void c64_send_command(int x){(void)x;}
#define CMD_WAIT_RESET 0
static void c64_disable(void){game_enabled=false;}
static unsigned int load_prg(char*n){(void)n;return good_load?32:0;}
static void c64_ef3_enable(void){game_enabled=true;}
static void send_prg(unsigned int n,char*p){(void)n;(void)p;assert(game_enabled);}
static bool crt_is_supported(int t){(void)t;return supported;}
static bool crt_buf_is_valid(void){return valid_crt;}
static bool load_crt(void){return good_load;}
static void c64_wait_valid_clock(void){}
static void crt_install_handler(void*p){(void)p;}
static void c64_enable(void){game_enabled=true;}
static bool load_disk(void){return good_load;}
static bool reu_enabled(void){return false;}
static void c64_launcher_reu_mode(void){}
static void c64_launcher_mode(void){}
static bool run_mode(void){bool result=false;c64_disable();switch(cfg_file.boot_type){
@MODE_CASES@
 default:break;
}return result;}
static void restart(bool clear_file){
 assert(open_files==0);if(clear_file)unlink(disk_file);
 memset(&cfg_file,0,sizeof(cfg_file));strcpy(cfg_file.path,"/Games");strcpy(cfg_file.file,"One.prg");cfg_file.boot_type=CFG_PRG;
 history_loaded=history_available=history_menu_session=history_random_origin=history_committed=false;
 history_recent_count=0;history_sequence=0;history_good_end=0;
 deny_io=fail_read=fail_sync=short_write=game_enabled=false;
 good_load=supported=valid_crt=true;stat_type=FILE_PRG;writes=0;
}
static void counts(const char*key,u32 total,u32 random){u32 t,r;assert(history_scan(key,&t,&r));assert(t==total&&r==random);assert(open_files==0);}
int main(int argc,char**argv){
 assert(argc==2);strcpy(disk_file,argv[1]);restart(true);
 assert(history_age("/Games","One.prg")==0);
 assert(history_append("/Games","One.prg",false));assert(history_append("/games","ONE.PRG",true));counts("/games/one.prg",2,1);
 restart(false);assert(history_age("/GAMES","ONE.PRG")>0);counts("/games/one.prg",2,1);
 for(int i=0;i<12;++i){char n[32];snprintf(n,sizeof(n),"Game%d.crt",i);assert(history_append("/Games/Sub",n,(i&1)!=0));}
 restart(false);assert(history_age("/Games/Sub","Game11.crt")==10);assert(history_age("/Games/Sub","Game2.crt")==1);assert(!history_age("/Games/Sub","Game1.crt"));
 /* Torn and checksum-invalid tails recover the last verified prefix. */
 FILE*f=fopen(disk_file,"ab");assert(f);assert(fwrite("KF3",1,3,f)==3);fclose(f);
 restart(false);assert(history_append("/Games","One.prg",false));counts("/games/one.prg",3,1);
 f=fopen(disk_file,"r+b");assert(f);fseek(f,-1,SEEK_END);int x=fgetc(f);fseek(f,-1,SEEK_END);fputc(x^1,f);fclose(f);
 restart(false);assert(history_append("/Games","One.prg",true));counts("/games/one.prg",3,2);
 /* No logging during automatic boots; exactly once for an explicit start. */
 restart(true);assert(run_mode());assert(!writes);
 restart(true);history_menu_session=true;assert(run_mode());assert(writes==1);assert(run_mode());assert(writes==1);game_enabled=false;counts("/games/one.prg",1,0);
 restart(true);history_menu_session=history_random_origin=true;assert(run_mode());game_enabled=false;counts("/games/one.prg",1,1);
 restart(true);history_menu_session=true;good_load=false;assert(!run_mode()&&!writes);
 restart(true);history_menu_session=true;cfg_file.boot_type=CFG_CRT;stat_type=FILE_CRT;assert(run_mode());assert(writes==1);
 restart(true);history_menu_session=true;cfg_file.boot_type=CFG_CRT;supported=false;assert(!run_mode()&&!writes);
 restart(true);history_menu_session=true;cfg_file.boot_type=CFG_DISK;cfg_file.img.mode=DISK_MODE_D64;cfg_file.img.element=0;stat_type=FILE_D64;assert(run_mode()&&writes==1);
 restart(true);history_menu_session=true;cfg_file.boot_type=CFG_DISK;cfg_file.img.mode=DISK_MODE_D64;cfg_file.img.element=ELEMENT_NOT_SELECTED;assert(run_mode()&&!writes);
 restart(true);history_menu_session=true;stat_type=FILE_DIR;assert(run_mode()&&!writes);
 restart(true);history_menu_session=true;strcpy(cfg_file.path,"/Tools");assert(run_mode()&&writes==1&&!history_recent_count);
 restart(true);history_menu_session=true;deny_io=true;assert(run_mode()&&game_enabled&&open_files==0);
 restart(true);history_menu_session=true;short_write=true;assert(run_mode()&&game_enabled&&open_files==0);restart(false);assert(history_append("/Games","Two.prg",false));counts("/games/two.prg",1,0);
 restart(true);history_menu_session=true;fail_sync=true;assert(run_mode()&&game_enabled&&open_files==0);
 /* Maximum-length keys and read errors remain bounded and fail open. */
 restart(true);char folder[750],name[256];memcpy(folder,"/Games/",7);memset(folder+7,'d',742);folder[749]=0;memset(name,'f',255);name[255]=0;
 assert(history_append(folder,name,false));assert(history_scan(NULL,NULL,NULL));assert(history_sequence==1);
 restart(false);fail_read=true;assert(!history_append("/Games","One.prg",false)&&open_files==0&&!writes);
 /* A foreign/versioned file is not silently replaced. */
 restart(true);f=fopen(disk_file,"wb");assert(f);for(int i=0;i<32;++i)fputc('X',f);fclose(f);assert(!history_append("/Games","One.prg",false));assert(!writes);
 /* Unsupported future record versions are never overwritten. */
 restart(true);assert(history_append("/Games","Version.prg",false));
 f=fopen(disk_file,"r+b");assert(f);fseek(f,7,SEEK_SET);fputc(2,f);fclose(f);writes=0;
 assert(!history_append("/Games","One.prg",false)&&writes==0);
 /* The actual sampler and actual persistent recency rules work together. */
 restart(true);assert(history_append("/Games","One.prg",false));assert(history_append("/Games","Two.prg",true));
 for(u32 seed=1;seed<=2000;++seed){random_state=0;assert(random_pick(seed));assert(strcmp(random_file,"One.prg")&&strcmp(random_file,"Two.prg"));}
 pool_size=2;assert(random_pick(1)&&!strcmp(random_file,"One.prg"));
 assert(history_append("/Games","One.prg",false));assert(random_pick(2)&&!strcmp(random_file,"Two.prg"));
 pool_size=1;assert(random_pick(3)&&!strcmp(random_file,"One.prg"));pool_size=5;
 restart(false);deny_io=true;assert(random_pick(3)&&random_count==5&&open_files==0);
 /* Leave a simple golden journal for the independent PC decoder. */
 restart(true);assert(history_append("/Games","Golden.prg",false));assert(history_append("/Games","Golden.prg",true));
 puts("PASS: persistent counts, origins, recent window, torn/corrupt tails, exact loader hook ordering, automatic boots, mount-only, IO failures");
 return 0;
}
