/* Persistent launch journal, altered version, 2026. See root LICENSE.
 * Stored on SD, never in the emulated cartridge/REU buffers.
 * Counts loader-prepared explicit starts, not elapsed play time.
 */
#define HISTORY_FILE "/.KFF2-history"
#define HISTORY_RECENT 10
#define HISTORY_PATH_MAX (sizeof(cfg_file.path) + sizeof(cfg_file.file))
#define HISTORY_HEADER 24
#define HISTORY_RECORD_MAX (HISTORY_HEADER + HISTORY_PATH_MAX + 4)
static char history_key[HISTORY_PATH_MAX];
static char history_recent[HISTORY_RECENT][HISTORY_PATH_MAX];
static u8 history_record[HISTORY_RECORD_MAX];
static u8 history_recent_count;
static u32 history_sequence;
static FSIZE_t history_good_end;
static bool history_loaded, history_available;
static bool history_menu_session, history_random_origin, history_committed;

static u32 history_u32(const u8 *p)
{
    return (u32)p[0] | (u32)p[1]<<8 | (u32)p[2]<<16 | (u32)p[3]<<24;
}
static void history_put32(u8 *p, u32 n)
{
    for (u8 i=0; i<4; ++i) { p[i]=(u8)n; n>>=8; }
}
static u32 history_crc(const u8 *p, size_t n)
{
    u32 crc=0xffffffffu;
    while (n--)
    {
        crc^=*p++;
        for (u8 bit=0;bit<8;++bit) crc=(crc>>1)^((0u-(crc&1))&0xedb88320u);
    }
    return ~crc;
}
static bool history_make_key(const char *folder, const char *file)
{
    size_t n=strlen(folder), m=strlen(file);
    if (!n || !m || n+m+2>sizeof(history_key)) return false;
    memcpy(history_key,folder,n);
    if (history_key[n-1]!='/') history_key[n++]='/';
    memcpy(history_key+n,file,m+1);
    for (char *p=history_key;*p;++p)
        if (*p>='A'&&*p<='Z') *p+=32;
    return history_key[0]=='/';
}
static void history_touch(const char *key)
{
    if(strncmp(key,"/games/",7)!=0) return; /* Tools do not displace recent games. */
    u8 i;
    for(i=0;i<history_recent_count;++i) if(strcmp(history_recent[i],key)==0) break;
    if(i==HISTORY_RECENT) --i;
    else if(i==history_recent_count) ++history_recent_count;
    while(i) { strcpy(history_recent[i],history_recent[i-1]); --i; }
    strcpy(history_recent[0],key);
}
static bool history_scan(const char *query, u32 *total, u32 *random_runs)
{
    FIL f;
    history_recent_count=0; history_sequence=0; history_good_end=0;
    if(total) *total=0;
    if(random_runs) *random_runs=0;
    FRESULT res=f_open(&f,HISTORY_FILE,FA_READ);
    if(res==FR_NO_FILE) return true;
    if(res!=FR_OK) return false;
    bool ok=true;
    while(true)
    {
        UINT got;
        res=f_read(&f,history_record,HISTORY_HEADER,&got);
        if(res!=FR_OK) { ok=false; break; }
        if(got==0) break;
        /* Incomplete/corrupt tail: retain only the verified prefix. Unknown
         * formats at the start are preserved and never overwritten.
         */
        if(got<HISTORY_HEADER) break;
        if(memcmp(history_record,"KF3H",4)!=0)
        { if(!history_good_end) ok=false; break; }
        if(history_record[7]!=1) { ok=false; break; }
        unsigned int length=history_record[4]|(unsigned int)history_record[5]<<8;
        unsigned int pathlen=history_record[20]|(unsigned int)history_record[21]<<8;
        if(!pathlen || pathlen>=HISTORY_PATH_MAX || length!=HISTORY_HEADER+pathlen+4 ||
           (history_record[6]&~1) || history_record[22] || history_record[23]) break;
        res=f_read(&f,history_record+HISTORY_HEADER,pathlen+4,&got);
        if(res!=FR_OK) { ok=false; break; }
        if(got!=pathlen+4 || history_crc(history_record,length-4)!=history_u32(history_record+length-4)) break;
        u32 seq=history_u32(history_record+8), count=history_u32(history_record+12), rnd=history_u32(history_record+16);
        if(seq<=history_sequence || !count || rnd>count || memchr(history_record+HISTORY_HEADER,0,pathlen)) break;
        history_record[HISTORY_HEADER+pathlen]=0;
        const char *key=(const char*)history_record+HISTORY_HEADER;
        history_touch(key);
        history_sequence=seq; history_good_end=f_tell(&f);
        if(query && strcmp(query,key)==0) { *total=count; *random_runs=rnd; }
    }
    if(f_close(&f)!=FR_OK) ok=false;
    return ok;
}
static u8 history_age(const char *folder, const char *file)
{
    if(!history_loaded)
    {
        history_available=history_scan(NULL,NULL,NULL);
        history_loaded=true;
    }
    if(!history_available || !history_make_key(folder,file)) return 0;
    for(u8 i=0;i<history_recent_count;++i)
        if(strcmp(history_recent[i],history_key)==0) return history_recent_count-i;
    return 0; /* Outside the recent window: equal random chance. */
}
static bool history_append(const char *folder, const char *file, bool random_run)
{
    if(!history_make_key(folder,file)) return false;
    u32 total,rnd;
    history_available=history_scan(history_key,&total,&rnd); history_loaded=true;
    if(!history_available || history_sequence==0xffffffffu) return false;
    if(total!=0xffffffffu) ++total;
    if(random_run && rnd!=0xffffffffu) ++rnd;
    size_t pathlen=strlen(history_key), length=HISTORY_HEADER+pathlen+4;
    memset(history_record,0,HISTORY_HEADER);
    memcpy(history_record,"KF3H",4);
    history_record[4]=(u8)length;history_record[5]=(u8)(length>>8);
    history_record[6]=random_run?1:0;history_record[7]=1;
    history_put32(history_record+8,history_sequence+1);
    history_put32(history_record+12,total);history_put32(history_record+16,rnd);
    history_record[20]=(u8)pathlen;history_record[21]=(u8)(pathlen>>8);
    memcpy(history_record+HISTORY_HEADER,history_key,pathlen);
    history_put32(history_record+length-4,history_crc(history_record,length-4));
    FIL f;
    if(f_open(&f,HISTORY_FILE,FA_WRITE|FA_OPEN_ALWAYS)!=FR_OK) return false;
    UINT wrote=0;
    bool ok=f_lseek(&f,history_good_end)==FR_OK && f_truncate(&f)==FR_OK &&
            f_write(&f,history_record,length,&wrote)==FR_OK && wrote==length && f_sync(&f)==FR_OK;
    if(f_close(&f)!=FR_OK) ok=false;
    if(ok) { ++history_sequence; history_good_end+=length; history_touch(history_key); }
    return ok;
}
static void history_before_launch(void)
{
    if(!history_menu_session || history_committed || !cfg_file.file[0]) return;
    /* Mounting a disk without autostart is not a program start. */
    if(cfg_file.boot_type==CFG_DISK && cfg_file.img.mode==DISK_MODE_D64 &&
       cfg_file.img.element==ELEMENT_NOT_SELECTED && !(cfg_file.flags&CFG_FLAG_AUTOSTART_D64)) return;
    FILINFO info;
    if(!file_stat(cfg_file.file,&info)) return;
    u8 type=get_file_type(&info);
    if(type!=FILE_PRG && type!=FILE_P00 && type!=FILE_CRT && type!=FILE_ROM &&
       type!=FILE_D64 && type!=FILE_T64) return;
    history_committed=true;
    /* Best effort. A full/read-only/bad history file never blocks the game. */
    (void)history_append(cfg_file.path,cfg_file.file,history_random_origin);
}
