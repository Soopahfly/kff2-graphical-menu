/* Integration test: real FatFs on a 64MB RAM-backed FAT32 volume. */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ff.h"
#include "diskio.h"
typedef uint8_t u8;typedef uint32_t u32;
#define SECTORS 131072u
static BYTE *volume;
static bool read_only;
DSTATUS disk_initialize(BYTE drive){(void)drive;return read_only?STA_PROTECT:0;}
DSTATUS disk_status(BYTE drive){return disk_initialize(drive);}
DRESULT disk_read(BYTE drive,BYTE*buffer,LBA_t sector,UINT count){(void)drive;if(sector>=SECTORS||count>SECTORS-sector)return RES_PARERR;memcpy(buffer,volume+(size_t)sector*512,(size_t)count*512);return RES_OK;}
DRESULT disk_write(BYTE drive,const BYTE*buffer,LBA_t sector,UINT count){(void)drive;if(read_only)return RES_WRPRT;if(sector>=SECTORS||count>SECTORS-sector)return RES_PARERR;memcpy(volume+(size_t)sector*512,buffer,(size_t)count*512);return RES_OK;}
DRESULT disk_ioctl(BYTE drive,BYTE cmd,void*buffer){(void)drive;switch(cmd){case CTRL_SYNC:return RES_OK;case GET_SECTOR_COUNT:*(LBA_t*)buffer=SECTORS;return RES_OK;case GET_SECTOR_SIZE:*(WORD*)buffer=512;return RES_OK;case GET_BLOCK_SIZE:*(DWORD*)buffer=1;return RES_OK;default:return RES_PARERR;}}
#define CFG_DISK 1
#define DISK_MODE_D64 2
#define ELEMENT_NOT_SELECTED 65535
#define CFG_FLAG_AUTOSTART_D64 1
#define FILE_PRG 1
#define FILE_P00 2
#define FILE_CRT 3
#define FILE_ROM 4
#define FILE_D64 5
#define FILE_T64 6
static struct{char path[750],file[256];int boot_type;unsigned int flags;struct{int mode,element;}img;}cfg_file;
static bool file_stat(const char*n,FILINFO*i){return f_stat(n,i)==FR_OK;}
static u8 get_file_type(FILINFO*i){(void)i;return FILE_PRG;}
@HISTORY@
int main(int argc,char**argv){
 assert(argc==2);volume=calloc(SECTORS,512);assert(volume);BYTE work[4096];FATFS fs;
 MKFS_PARM options={.fmt=FM_FAT32,.au_size=512};
 assert(f_mkfs("",&options,work,sizeof(work))==FR_OK);assert(f_mount(&fs,"",1)==FR_OK);assert(fs.fs_type==FS_FAT32);
 assert(history_append("/Games","Test.prg",false));assert(history_append("/Games","Test.prg",true));
 assert(f_mount(NULL,"",0)==FR_OK);memset(&fs,0,sizeof(fs));assert(f_mount(&fs,"",1)==FR_OK);
 u32 total,rnd;assert(history_scan("/games/test.prg",&total,&rnd));assert(total==2&&rnd==1);
 FIL f;UINT n;assert(f_open(&f,HISTORY_FILE,FA_WRITE)==FR_OK);assert(f_lseek(&f,f_size(&f))==FR_OK);assert(f_write(&f,"KF3H",4,&n)==FR_OK&&n==4);assert(f_close(&f)==FR_OK);
 assert(history_append("/Games","Test.prg",true));assert(history_scan("/games/test.prg",&total,&rnd)&&total==3&&rnd==2);
 read_only=true;assert(!history_append("/Games","Test.prg",false));assert(history_scan("/games/test.prg",&total,&rnd)&&total==3&&rnd==2);read_only=false;
 assert(f_open(&f,HISTORY_FILE,FA_READ)==FR_OK);FILE*out=fopen(argv[1],"wb");assert(out);
 do{assert(f_read(&f,work,sizeof(work),&n)==FR_OK);assert(fwrite(work,1,n,out)==n);}while(n);fclose(out);assert(f_close(&f)==FR_OK);
 assert(f_mount(NULL,"",0)==FR_OK);free(volume);
 puts("PASS: real FatFs FAT32 create/append/sync/remount, truncated-tail repair and read-only media");return 0;
}
