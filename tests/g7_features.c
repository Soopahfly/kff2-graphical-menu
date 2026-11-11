/* Real FatFs integration tests for G7 copies and configuration compatibility. */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ff.h"
#include "diskio.h"
typedef uint8_t u8;typedef int8_t s8;typedef uint16_t u16;typedef uint32_t u32;
#define DIR_t DIR
#define SECTORS 131072u
static BYTE *volume;
static bool read_only;
static int fail_writes;
DSTATUS disk_initialize(BYTE d){(void)d;return read_only?STA_PROTECT:0;}
DSTATUS disk_status(BYTE d){return disk_initialize(d);}
DRESULT disk_read(BYTE d,BYTE *b,LBA_t s,UINT n){(void)d;if(s>=SECTORS||n>SECTORS-s)return RES_PARERR;memcpy(b,volume+(size_t)s*512,(size_t)n*512);return RES_OK;}
DRESULT disk_write(BYTE d,const BYTE*b,LBA_t s,UINT n){(void)d;if(read_only)return RES_WRPRT;if(fail_writes){--fail_writes;return RES_ERROR;}if(s>=SECTORS||n>SECTORS-s)return RES_PARERR;memcpy(volume+(size_t)s*512,b,(size_t)n*512);return RES_OK;}
DRESULT disk_ioctl(BYTE d,BYTE c,void*b){(void)d;switch(c){case CTRL_SYNC:return RES_OK;case GET_SECTOR_COUNT:*(LBA_t*)b=SECTORS;return RES_OK;case GET_SECTOR_SIZE:*(WORD*)b=512;return RES_OK;case GET_BLOCK_SIZE:*(DWORD*)b=1;return RES_OK;default:return RES_PARERR;}}
@FILE_TYPES@
@SETTINGS@
static int button_calls,invalidated,enabled;
static bool signature;
static bool load_cfg(void){return true;}
static bool menu_signature(void){return signature;}
static bool menu_button_pressed(void){return button_calls-->0;}
static void invalidate_menu_signature(void){++invalidated;signature=false;}
static void menu_button_enable(void){++enabled;}
@AUTO_BOOT@
@FAVOURITES@
typedef struct {int unused;} OPTIONS_STATE;
typedef struct {int unused;} OPTIONS_ELEMENT;
static u8 settings_g7,settings_flags;
static int saves,restarts,back_to_dir;
/* Model the C64's two waits: flash operation, then warning acknowledgement.
 * The real launcher sends REPLY_OK and waits for CMD_SYNC after each. */
enum { PROTOCOL_READY, PROTOCOL_FLASH_WAIT, PROTOCOL_WARNING_WAIT };
static int protocol_state,warning_syncs;
static char displayed[128];
static const char *setting_print(const char *label,const char *value){assert(label);return value;}
static u8 settings_refresh(OPTIONS_ELEMENT *element,const char *text){(void)element;strcpy(displayed,text);return 123;}
static void sd_send_prg_message(const char *text){assert(text);assert(protocol_state==PROTOCOL_READY);protocol_state=PROTOCOL_FLASH_WAIT;}
static bool save_cfg(void){++saves;return true;}
static void restart_to_menu(void){++restarts;protocol_state=PROTOCOL_READY;}
static u8 c64_interface_sync(void){assert(protocol_state!=PROTOCOL_READY);if(protocol_state==PROTOCOL_WARNING_WAIT)++warning_syncs;protocol_state=PROTOCOL_READY;return 0;}
static void c64_send_warning(const char *text){assert(protocol_state==PROTOCOL_READY);strcpy(displayed,text);protocol_state=PROTOCOL_WARNING_WAIT;}
static u8 options_prev_dir(OPTIONS_STATE *s,OPTIONS_ELEMENT *e,u8 flags){(void)s;(void)e;(void)flags;assert(protocol_state==PROTOCOL_READY);++back_to_dir;return 124;}
#define CMD_NONE 0
@SETTINGS_CALLBACKS@
@SETTINGS_SAVE@
@FAVOURITES_MENU@
_Static_assert(sizeof(CFG_FILE)==1024,"Original configuration size changed");
_Static_assert(offsetof(CFG_FILE,path)==18,"Original path offset changed");
_Static_assert(offsetof(CFG_FILE,file)==768,"Original filename offset changed");
static void put(const char *name,const void *bytes,UINT size)
{
    FIL f;UINT n;assert(f_open(&f,name,FA_WRITE|FA_CREATE_ALWAYS)==FR_OK);
    assert(f_write(&f,bytes,size,&n)==FR_OK && n==size);assert(f_close(&f)==FR_OK);
}
static void equal(const char *name,const void *bytes,UINT size)
{
    FIL f;UINT n;char *out=malloc(size+1);assert(out);
    assert(f_open(&f,name,FA_READ)==FR_OK && f_size(&f)==size);
    assert(f_read(&f,out,size+1,&n)==FR_OK && n==size);assert(!memcmp(out,bytes,size));
    assert(f_close(&f)==FR_OK);free(out);
}
static void config_checks(void)
{
    CFG_FILE original;
    memset(&cfg_file,0,sizeof(cfg_file));
    memcpy(cfg_file.signature,CFG_SIGNATURE,5);cfg_file.phi2_offset=-3;
    cfg_file.flags=0xa3;cfg_file.boot_type=CFG_CRT;
    strcpy(cfg_file.path,"/Games");strcpy(cfg_file.file,"Test.crt");original=cfg_file;
    assert(g7_autoboot_enabled() && g7_reu_mask()==0xfffff);
    for(u8 size=0;size<3;++size) for(u8 off=0;off<2;++off) {
        u8 options=size|(off?G7_NO_AUTOBOOT:0);
        g7_save_options(options);assert(g7_options()==options);
        assert(g7_autoboot_enabled()==!off);
        u32 bytes=(size==0?1024u:size==1?512u:256u)*1024;
        assert(g7_reu_mask()==bytes-1);
        /* DMA reads, writes, swaps and compares must alias at selected size. */
        for(u32 address=0;address<0x1000000;address+=65521) assert((address & g7_reu_mask())==address%bytes);
        assert(cfg_file.flags==original.flags && cfg_file.phi2_offset==original.phi2_offset);
        assert(!strcmp(cfg_file.path,original.path) && !strcmp(cfg_file.file,original.file));
        CFG_FILE downgrade=cfg_file;downgrade.boot_type=CFG_DISK;cfg_file=downgrade;
        assert(g7_options()==options); /* G6 round-trip retains the reserved word. */
    }
    cfg_file.reserved=0xdeadbeef;assert(g7_options()==0 && g7_autoboot_enabled());
    g7_save_options(0);settings_g7=g7_options();
    assert(settings_reu_size_change(NULL,NULL,0)==123 && !strcmp(displayed,"512 KB"));
    settings_autoboot_change(NULL,NULL,0);assert(!strcmp(displayed,"no") && (settings_g7 & 3)==1);
    assert(g7_options()==0); /* Changing the menu does not save before Save. */
    settings_flags=original.flags;assert(settings_save(NULL,NULL,0)==CMD_NONE && saves==1 && restarts==1);
    assert(g7_options()==(1|G7_NO_AUTOBOOT));
    settings_reu_size_change(NULL,NULL,0);assert(!strcmp(displayed,"256 KB"));
    settings_reu_size_change(NULL,NULL,0);assert(!strcmp(displayed,"1 MB"));
    settings_autoboot_change(NULL,NULL,0);assert(!strcmp(displayed,"yes"));
    g7_save_options(3);assert(g7_reu_mask()==0xfffff); /* Unknown size is safe default. */
    cfg_file.boot_type=CFG_CRT;button_calls=0;signature=false;
    g7_save_options(0);assert(auto_boot());
    g7_save_options(G7_NO_AUTOBOOT);assert(!auto_boot());
    g7_save_options(0);signature=true;assert(!auto_boot() && invalidated==1);
    button_calls=2;assert(!auto_boot());
    g7_save_options(G7_NO_AUTOBOOT);button_calls=110;enabled=0;
    assert(auto_boot() && cfg_file.boot_type==CFG_DIAG && !enabled);
}
int main(void)
{
    config_checks();
    volume=calloc(SECTORS,512);assert(volume);BYTE work[4096];FATFS fs;
    MKFS_PARM fmt={.fmt=FM_FAT32,.au_size=512};
    assert(f_mkfs("",&fmt,work,sizeof(work))==FR_OK);assert(f_mount(&fs,"",1)==FR_OK);
    assert(f_mkdir("/Games")==FR_OK);assert(f_mkdir("/Games/Set")==FR_OK);
    assert(f_mkdir("/Games/Set/Sub")==FR_OK);
    char data[12001];for(size_t i=0;i<sizeof(data);++i)data[i]=(char)(i*37);
    put("/Games/Test [EF].crt",data,sizeof(data));
    assert(fav_add("/Games","Test [EF].crt")==FAV_OK);
    equal("/Favourites/Test [EF].crt",data,sizeof(data));equal("/Games/Test [EF].crt",data,sizeof(data));
    assert(fav_add("/Games","Test [EF].crt")==FAV_ALREADY);
    strcpy(cfg_file.path,"/Games");strcpy(cfg_file.file,"Test [EF].crt");
    assert(favourite_supported(FILE_DIR) && favourite_supported(FILE_CRT) && !favourite_supported(FILE_D64_PRG));
    assert(favourite_copy(NULL,NULL,0)==124 && back_to_dir==1);
    assert(strstr(displayed,"already") && !strcmp(cfg_file.path,"/Games"));
    assert(warning_syncs==1);
    put("/Games/Ack.prg","ack",3);strcpy(cfg_file.file,"Ack.prg");
    assert(favourite_copy(NULL,NULL,0)==124 && back_to_dir==2);
    assert(strstr(displayed,"Added") && warning_syncs==2);
    equal("/Favourites/Ack.prg","ack",3);equal("/Games/Ack.prg","ack",3);
    put("/Games/Ack.prg","different",9);
    assert(favourite_copy(NULL,NULL,0)==124 && back_to_dir==3);
    assert(strstr(displayed,"Nothing overwritten") && warning_syncs==3);
    equal("/Favourites/Ack.prg","ack",3);
    strcpy(cfg_file.file,"Missing.prg");
    assert(favourite_copy(NULL,NULL,0)==124 && back_to_dir==4 && warning_syncs==4);
    assert(protocol_state==PROTOCOL_READY);
    put("/Games/Test [EF].crt","changed",7);
    assert(fav_add("/Games","Test [EF].crt")==FAV_COLLISION);equal("/Favourites/Test [EF].crt",data,sizeof(data));
    put("/Games/Set/side1.d64","side1",5);put("/Games/Set/side2.d64","side2",5);
    put("/Games/Set/.support","hidden",6);put("/Games/Set/Sub/data","payload",7);
    assert(fav_add("/Games","Set")==FAV_OK);
    equal("/Favourites/Set/side1.d64","side1",5);equal("/Favourites/Set/side2.d64","side2",5);
    equal("/Favourites/Set/.support","hidden",6);equal("/Favourites/Set/Sub/data","payload",7);
    assert(fav_add("/Games","Set")==FAV_COLLISION);
    assert(fav_add("/","Favourites")==FAV_INVALID);
    assert(fav_add("/fAvOuRiTeS","Set")==FAV_INVALID);
    assert(fav_add("/Games","../Test.crt")==FAV_INVALID);
    put(FAV_TEMP,"previous interrupted copy",25);put("/Games/New.prg","new",3);
    assert(fav_add("/Games","New.prg")==FAV_PENDING);equal(FAV_TEMP,"previous interrupted copy",25);
    assert(f_unlink(FAV_TEMP)==FR_OK);
    read_only=true;assert(fav_add("/Games","New.prg")==FAV_IO_ERROR);read_only=false;
    equal("/Games/New.prg","new",3);
    assert(f_mkdir("/Games/Deep")==FR_OK);
    char deep[200]="/Games/Deep";
    for(int i=0;i<11;++i){strcat(deep,"/D");assert(f_mkdir(deep)==FR_OK);}
    assert(fav_add("/Games","Deep")==FAV_LIMIT);
    FILINFO info;assert(f_stat("/Favourites/Deep",&info)==FR_NO_FILE);
    assert(f_stat(FAV_TEMP,&info)==FR_NO_FILE);
    fail_writes=1;assert(fav_add("/Games","New.prg")==FAV_IO_ERROR);fail_writes=0;
    equal("/Games/New.prg","new",3);assert(f_stat("/Favourites/New.prg",&info)==FR_NO_FILE);
    /* Remount verifies persisted copies and configuration bytes, not just caches. */
    g7_save_options(2|G7_NO_AUTOBOOT);put("/.KFF2.cfg",&cfg_file,sizeof(cfg_file));
    assert(f_mount(NULL,"",0)==FR_OK);memset(&fs,0,sizeof(fs));assert(f_mount(&fs,"",1)==FR_OK);
    equal("/Favourites/Set/Sub/data","payload",7);equal("/.KFF2.cfg",&cfg_file,sizeof(cfg_file));
    assert(f_mount(NULL,"",0)==FR_OK);free(volume);
    puts("PASS: G7 config layout/defaults/downgrade, REU sizes, real FAT32 file/folder copies, companions, no-overwrite, interrupted copy, read-only, depth and I/O failures, copy-result acknowledgement handshake");
    return 0;
}
