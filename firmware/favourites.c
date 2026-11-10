/* G7 bounded, no-overwrite copies. Uses FatFs only; no C64 bus/protocol access. */
#include <strings.h>
#define FAV_ROOT "/Favourites"
#define FAV_TEMP FAV_ROOT "/.KFF2-copy.tmp"
#define FAV_PATH_MAX 1024
#define FAV_DEPTH_MAX 8
#define FAV_FILE_MAX 4096
typedef enum { FAV_OK, FAV_ALREADY, FAV_COLLISION, FAV_PENDING, FAV_INVALID,
               FAV_LIMIT, FAV_IO_ERROR } FAV_RESULT;
static char fav_source[FAV_PATH_MAX],fav_target[FAV_PATH_MAX];
static u8 fav_buffer[4096];
static u32 fav_files;

static bool fav_component(const char *name)
{
    if (!name[0] || !strcmp(name,".") || !strcmp(name,"..")) return false;
    while (*name) {
        if (*name=='/' || *name=='\\' || *name==':') return false;
        ++name;
    }
    return true;
}
static bool fav_join(char *path,size_t length,const char *name)
{
    size_t n=strlen(name);
    if (length+n+2>FAV_PATH_MAX || !fav_component(name)) return false;
    path[length++]='/';memcpy(path+length,name,n+1);return true;
}
static FAV_RESULT fav_copy_file(void)
{
    FIL src,dst;
    UINT n,w;
    bool ok=true;
    if (++fav_files>FAV_FILE_MAX) return FAV_LIMIT;
    if (f_open(&src,fav_source,FA_READ)!=FR_OK) return FAV_IO_ERROR;
    if (f_open(&dst,fav_target,FA_WRITE|FA_CREATE_NEW)!=FR_OK) {
        f_close(&src);return FAV_IO_ERROR;
    }
    for (;;) {
        if (f_read(&src,fav_buffer,sizeof(fav_buffer),&n)!=FR_OK) {ok=false;break;}
        if (!n) break;
        if (f_write(&dst,fav_buffer,n,&w)!=FR_OK || w!=n) {ok=false;break;}
    }
    if (ok && f_sync(&dst)!=FR_OK) ok=false;
    if (f_close(&dst)!=FR_OK) ok=false;
    if (f_close(&src)!=FR_OK) ok=false;
    return ok ? FAV_OK : FAV_IO_ERROR;
}
static FAV_RESULT fav_copy_tree(u8 depth)
{
    DIR_t dir;
    FILINFO info;
    FAV_RESULT result=FAV_OK;
    size_t source_length=strlen(fav_source),target_length=strlen(fav_target);
    if (depth>FAV_DEPTH_MAX) return FAV_LIMIT;
    if (f_opendir(&dir,fav_source)!=FR_OK) return FAV_IO_ERROR;
    for (;;) {
        if (f_readdir(&dir,&info)!=FR_OK) {result=FAV_IO_ERROR;break;}
        if (!info.fname[0]) break;
        if (!strcmp(info.fname,".") || !strcmp(info.fname,"..")) continue;
        if (!fav_join(fav_source,source_length,info.fname) ||
            !fav_join(fav_target,target_length,info.fname)) {result=FAV_LIMIT;break;}
        if (info.fattrib & AM_DIR) {
            if (++fav_files>FAV_FILE_MAX) result=FAV_LIMIT;
            else if (f_mkdir(fav_target)!=FR_OK) result=FAV_IO_ERROR;
            else result=fav_copy_tree(depth+1);
        } else result=fav_copy_file();
        fav_source[source_length]=0;fav_target[target_length]=0;
        if (result!=FAV_OK) break;
    }
    fav_source[source_length]=0;fav_target[target_length]=0;
    if (f_closedir(&dir)!=FR_OK) result=FAV_IO_ERROR;
    return result;
}
/* Only remove staging created by this invocation, never a pre-existing stage. */
static void fav_cleanup(u8 depth)
{
    DIR_t dir;FILINFO info;
    size_t length=strlen(fav_target);
    if (depth>FAV_DEPTH_MAX+1) return;
    if (f_opendir(&dir,fav_target)==FR_OK) {
        while (f_readdir(&dir,&info)==FR_OK && info.fname[0]) {
            if (!strcmp(info.fname,".") || !strcmp(info.fname,"..")) continue;
            if (!fav_join(fav_target,length,info.fname)) break;
            if (info.fattrib & AM_DIR) fav_cleanup(depth+1);
            else f_unlink(fav_target);
            fav_target[length]=0;
        }
        f_closedir(&dir);
    }
    fav_target[length]=0;f_unlink(fav_target);
}
static bool fav_same_file(const char *target)
{
    FIL src,dst;UINT n,m;
    bool same=true;
    size_t half=sizeof(fav_buffer)/2;
    if (f_open(&src,fav_source,FA_READ)!=FR_OK) return false;
    if (f_open(&dst,target,FA_READ)!=FR_OK) {f_close(&src);return false;}
    if (f_size(&src)!=f_size(&dst)) same=false;
    while (same) {
        if (f_read(&src,fav_buffer,half,&n)!=FR_OK ||
            f_read(&dst,fav_buffer+half,half,&m)!=FR_OK || n!=m) {same=false;break;}
        if (!n) break;
        if (memcmp(fav_buffer,fav_buffer+half,n)) same=false;
    }
    if (f_close(&dst)!=FR_OK) same=false;
    if (f_close(&src)!=FR_OK) same=false;
    return same;
}
static FAV_RESULT fav_add(const char *folder,const char *name)
{
    FILINFO source_info,info;
    char destination[sizeof(FAV_ROOT)+257];
    size_t length=strlen(folder);
    FRESULT status;
    FAV_RESULT result;
    if (!length || folder[0]!='/' || length>=sizeof(fav_source) ||
        strlen(name)>255 || !fav_component(name)) return FAV_INVALID;
    memcpy(fav_source,folder,length+1);
    if (length==1) length=0;
    if (!fav_join(fav_source,length,name)) return FAV_INVALID;
    /* Reject the destination itself and anything already inside it. */
    if (!strncasecmp(fav_source,FAV_ROOT,sizeof(FAV_ROOT)-1) &&
        (fav_source[sizeof(FAV_ROOT)-1]==0 || fav_source[sizeof(FAV_ROOT)-1]=='/')) return FAV_INVALID;
    if (f_stat(fav_source,&source_info)!=FR_OK ||
        (source_info.fattrib & (AM_HID|AM_SYS))) return FAV_INVALID;
    strcpy(destination,FAV_ROOT);strcat(destination,"/");strcat(destination,name);
    status=f_stat(destination,&info);
    if (status==FR_OK) {
        if (!(source_info.fattrib & AM_DIR) && !(info.fattrib & AM_DIR) && fav_same_file(destination)) return FAV_ALREADY;
        return FAV_COLLISION;
    }
    if (status!=FR_NO_FILE && status!=FR_NO_PATH) return FAV_IO_ERROR;
    status=f_mkdir(FAV_ROOT);
    if (status!=FR_OK && status!=FR_EXIST) return FAV_IO_ERROR;
    if (f_stat(FAV_ROOT,&info)!=FR_OK || !(info.fattrib & AM_DIR)) return FAV_IO_ERROR;
    status=f_stat(FAV_TEMP,&info);
    if (status==FR_OK) return FAV_PENDING;
    if (status!=FR_NO_FILE) return FAV_IO_ERROR;
    strcpy(fav_target,FAV_TEMP);fav_files=0;
    if (source_info.fattrib & AM_DIR) {
        if (f_mkdir(fav_target)!=FR_OK) return FAV_IO_ERROR;
        result=fav_copy_tree(0);
    } else result=fav_copy_file();
    if (result==FAV_OK && f_rename(FAV_TEMP,destination)==FR_OK) return FAV_OK;
    if (result==FAV_OK) result=FAV_IO_ERROR;
    fav_cleanup(0);return result;
}
