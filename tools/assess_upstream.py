#!/usr/bin/env python3
"""Assess isolated community candidates without modifying released firmware.

Runs the actual loader/runtime functions with host test doubles, inspects Cortex-M7
code size, compares complete ARM builds, and checks donor configuration semantics.
"""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

BASE = '9c84d999f4e2f5b2c7688cbc37a127069f5401b0'
DONOR = 'da19c9a892f6e12a40b943a7006e25d413968570'
GMOD = '653e03d779220841acd31c22ad46403c2696b402'


def run(args, **kw):
    return subprocess.check_output([str(x) for x in args], text=True, stderr=subprocess.STDOUT, **kw)


def function(text, signature):
    start = text.index(signature)
    brace = text.index('{', start)
    depth = 0
    for i in range(brace, len(text)):
        if text[i] == '{': depth += 1
        if text[i] == '}': depth -= 1
        if not depth: return text[start:i+1]
    raise ValueError(signature)


TYPES = '''#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>
typedef uint8_t u8; typedef int8_t s8; typedef uint16_t u16;
typedef int16_t s16; typedef uint32_t u32; typedef int32_t s32;
#define EXPORT
'''

LOADER_TEST = r'''
#define __REV __builtin_bswap32
#define __REV16 __builtin_bswap16
#define CRT_CHIP_SIGNATURE "CHIP"
#define wrn(...) ((void)0)
#define err(...) ((void)0)
typedef struct { unsigned char *data; size_t size,pos; } FIL;
static unsigned char crt_buf[1024*1024],input[65536];
static u32 file_read(FIL *f,void *out,size_t count) {
    if(count>f->size-f->pos)count=f->size-f->pos;
    memcpy(out,f->data+f->pos,count);f->pos+=count;return count;
}
static bool file_seek(FIL *f,size_t pos){f->pos=pos>f->size?f->size:pos;return true;}
static size_t f_tell(FIL *f){return f->pos;}
static bool f_eof(FIL *f){return f->pos>=f->size;}
@FUNCTIONS@
static void word(unsigned char *p,u16 v){p[0]=v>>8;p[1]=v;}
static size_t chip(size_t p,u16 bank,u16 address,u16 size,u8 value) {
    memcpy(input+p,"CHIP",4);u32 packet=__REV((u32)size+16);
    memcpy(input+p+4,&packet,4);word(input+p+8,0);word(input+p+10,bank);
    word(input+p+12,address);word(input+p+14,size);
    memset(input+p+16,value,size);return p+16+size;
}
typedef u8 (*load_fn)(FIL*,u16);
static u8 load(load_fn fn,size_t size,u16 type) {
    FIL f={input,size,0};return fn(&f,type);
}
int main(void) {
    load_fn funcs[]={baseline_load,skip_load,reject_load};
    unsigned cases=0;
    for(unsigned i=0;i<3;i++) {
        for(u16 bank=0;bank<64;bank++) {
            size_t n=chip(0,bank,0x8000,16384,0x51);
            assert(load(funcs[i],n,CRT_EASYFLASH)==bank+1);
            assert(crt_buf[(size_t)bank*16384]==0x51);
            assert(crt_buf[(size_t)(bank+1)*16384-1]==0x51);cases++;
        }
        size_t n=chip(0,63,0xa000,8192,0x63);
        assert(load(funcs[i],n,CRT_EASYFLASH)==64 && crt_buf[1048575]==0x63);cases++;
        n=chip(0,127,0x8000,8192,0x71);
        assert(load(funcs[i],n,CRT_MAGIC_DESK_DOMARK_HES_AUSTRALIA)==64);
        assert(crt_buf[1048575]==0x71);cases++;
        n=chip(0,0,0x8000,4096,0x44);
        assert(load(funcs[i],n,CRT_EASYFLASH)==1 && crt_buf[4096]==0x44);cases++;
        assert(load(funcs[i],n-1,CRT_EASYFLASH)==0);cases++;
        assert(load(funcs[i],15,CRT_EASYFLASH)==0);cases++;
        n=chip(0,0,0x8000,8192,0x22);input[0]='X';
        assert(load(funcs[i],n,CRT_EASYFLASH)==0);cases++;
        n=chip(0,0,0x8000,8192,0x22);memset(input+4,0,4);
        assert(load(funcs[i],n,CRT_EASYFLASH)==0);cases++;
    }
    size_t a=chip(0,0,0x8000,8192,0x11);
    size_t n=chip(a,64,0x8000,8192,0x33);
    assert(load(baseline_load,n,CRT_EASYFLASH)==0);
    assert(load(skip_load,n,CRT_EASYFLASH)==1); /* Silently incomplete ROM. */
    assert(load(reject_load,n,CRT_EASYFLASH)==0);cases+=3;
    /* A skipped payload resembling a CHIP record can be mistaken for real data. */
    n=chip(a,64,0x8000,8192,0x33);
    chip(a+16,0,0x8000,8176,0x77);
    assert(load(baseline_load,n,CRT_EASYFLASH)==1 && crt_buf[0]==0x77);
    assert(load(skip_load,n,CRT_EASYFLASH)==1 && crt_buf[0]==0x11);
    assert(load(reject_load,n,CRT_EASYFLASH)==0);cases+=3;
    printf("{\"cases\":%u,\"baseline_misparses_skipped_payload\":true,"
           "\"skip_alone_accepts_incomplete_rom\":true,\"fail_fast_passed\":true}\n",cases);
}
'''

COPY_TEST = r'''
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>
@FUNCTIONS@
static unsigned char source[8200] __attribute__((aligned(16)));
static unsigned char dest[8200] __attribute__((aligned(16)));
static unsigned char expected[8200] __attribute__((aligned(16)));
int main(void) {
    unsigned cases=0;
    void *(*copies[])(void*,const void*,size_t)={word_copy,alias_copy};
    for(unsigned variant=0;variant<2;variant++) {
    for(size_t s=0;s<8;s++)for(size_t d=0;d<8;d++)for(size_t n=0;n<=1024;n++) {
        for(size_t i=0;i<sizeof(source);i++) source[i]=(unsigned char)(i*37+n);
        memset(dest,0xa5,sizeof(dest));memset(expected,0xa5,sizeof(expected));
        for(size_t i=0;i<n;i++) expected[d+i]=source[s+i];
        assert(copies[variant](dest+d,source+s,n)==dest+d);
        assert(!memcmp(dest,expected,sizeof(dest)));cases++;
    }
    for(size_t n=4095;n<=4097;n++) {
        memset(dest,0xa5,sizeof(dest));memset(expected,0xa5,sizeof(expected));
        for(size_t i=0;i<n;i++)expected[i]=source[i];
        copies[variant](dest,source,n);assert(!memcmp(dest,expected,sizeof(dest)));cases++;
    }
    }
    size_t page=(size_t)sysconf(_SC_PAGESIZE);
    unsigned char *s=mmap(NULL,page*3,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    unsigned char *d=mmap(NULL,page*3,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    assert(s!=MAP_FAILED && d!=MAP_FAILED);
    assert(!mprotect(s+page,page,PROT_READ|PROT_WRITE));
    assert(!mprotect(d+page,page,PROT_READ|PROT_WRITE));
    memset(s+page,0x5b,page);
    for(unsigned variant=0;variant<2;variant++)for(size_t n=0;n<=256;n++) {
        copies[variant](d+2*page-n,s+2*page-n,n);
        for(size_t i=0;i<n;i++)assert(d[2*page-n+i]==0x5b);
        cases++;
    }
    assert(!munmap(s,page*3) && !munmap(d,page*3));
    puts("PASS: aligned/unaligned copies, tails, zero length, return pointer and guard bytes");
    printf("%u\n",cases);
}
'''

BENCH = r'''
#include <time.h>
#include <stdlib.h>
@FUNCTIONS@
static unsigned char src[65544] __attribute__((aligned(16)));
static unsigned char dst[65544] __attribute__((aligned(16)));
static double bench(void *(*fn)(void*,const void*,size_t),size_t n,unsigned off) {
    void *(*volatile call)(void*,const void*,size_t)=fn;
    size_t reps=33554432/n;
    struct timespec a,b;clock_gettime(CLOCK_MONOTONIC,&a);
    for(size_t i=0;i<reps;i++)call(dst+off,src+off,n);
    clock_gettime(CLOCK_MONOTONIC,&b);
    return (b.tv_sec-a.tv_sec)+(b.tv_nsec-a.tv_nsec)*1e-9;
}
int main(void) {
    size_t sizes[]={64,512,4096,16384};
    puts("[");
    for(unsigned i=0;i<4;i++)for(unsigned off=0;off<2;off++) {
        double a=bench(byte_copy,sizes[i],off),b=bench(word_copy,sizes[i],off);
        printf("{\"bytes\":%zu,\"offset\":%u,\"byte_seconds\":%.6f,\"word_seconds\":%.6f,\"ratio\":%.3f}%s\n",
            sizes[i],off,a,b,a/b,(i==3&&off==1)?"":",");
    }
    puts("]");
}
'''


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--upstream',type=Path,required=True)
    ap.add_argument('--baseline-build',type=Path,required=True,help='G7.03 patched ARM source directory')
    ap.add_argument('--launcher',type=Path,required=True)
    ap.add_argument('--arm-bin',type=Path,required=True)
    ap.add_argument('--newlib-include',type=Path,required=True)
    ap.add_argument('--newlib-libdir',type=Path,required=True)
    a=ap.parse_args();root=Path(__file__).resolve().parents[1]
    out=root/'experiments/upstream-assessment';out.mkdir(parents=True,exist_ok=True)
    show=lambda ref,path:run(['git','-C',a.upstream,'show',ref+':'+path])
    original=show(BASE,'firmware/loader.c')
    body=function(original,'static u8 crt_load_file(')
    assert body.count('continue;   // Skip image')==1
    failfast=body.replace('continue;   // Skip image','return 0;   // Reject incomplete cartridge; do not parse skipped payload.')
    skip=body.replace('continue;   // Skip image','if (!file_seek(crt_file, f_tell(crt_file) + header.image_size)) return 0;\n            continue;')
    donor_loader=show(GMOD,'firmware/loader.c')
    assert 'file_seek(crt_file, f_tell(crt_file) + header.image_size)' in donor_loader
    patched=original.replace(body,failfast)
    (out/'crt-reject-unsupported.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),patched.splitlines(True),fromfile='a/firmware/loader.c',tofile='b/firmware/loader.c')))
    runtime=show(BASE,'firmware/runtime.c');donor_runtime=show(DONOR,'firmware/runtime.c')
    byte=function(runtime,'EXPORT void *memcpy(');word=function(donor_runtime,'EXPORT void *memcpy(')
    # Assessment only: retain the exact donor implementation, including its casts.
    (out/'community-word-copy.patch').write_text(''.join(difflib.unified_diff(runtime.splitlines(True),runtime.replace(byte,word).splitlines(True),fromfile='a/firmware/runtime.c',tofile='b/firmware/runtime.c')))
    alias=word.replace('    u8 *dst8 =','    typedef u32 copy_word __attribute__((__may_alias__));\n    u8 *dst8 =',1)
    alias=alias.replace('u32 *dst32 = (u32 *)dst','copy_word *dst32 = (copy_word *)dst').replace('const u32 *src32 = (const u32 *)src','const copy_word *src32 = (const copy_word *)src')
    (out/'alias-safe-word-copy.patch').write_text(''.join(difflib.unified_diff(runtime.splitlines(True),runtime.replace(byte,alias).splitlines(True),fromfile='a/firmware/runtime.c',tofile='b/firmware/runtime.c')))
    copies=byte.replace('EXPORT void *memcpy','void *byte_copy')+'\n'+word.replace('EXPORT void *memcpy','void *word_copy')+'\n'+alias.replace('EXPORT void *memcpy','void *alias_copy')
    result={'baseline':BASE,'community':DONOR,'gmod_donor':GMOD,'hardware_benchmark':False}
    env=os.environ.copy();env.pop('C_INCLUDE_PATH',None);env['ASAN_OPTIONS']='detect_leaks=0'
    with tempfile.TemporaryDirectory(prefix='kff-assessment-') as temp:
        w=Path(temp);f=w/'test.c';exe=w/'test'
        headers=show(BASE,'firmware/file_types.h')
        funcs=function(original,'static bool crt_load_chip_header(')+'\n'+function(original,'static s32 crt_get_offset(')
        funcs+='\n'+body.replace('crt_load_file','baseline_load')+'\n'+skip.replace('crt_load_file','skip_load')+'\n'+failfast.replace('crt_load_file','reject_load')
        f.write_text(TYPES+headers+LOADER_TEST.replace('@FUNCTIONS@',funcs))
        flags=['gcc','-std=c11','-Os','-g','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-variable','-fsanitize=address,undefined']
        run([*flags,f,'-o',exe],env=env);result['parser']=json.loads(run([exe],env=env))
        f.write_text('#define _GNU_SOURCE\n'+TYPES+COPY_TEST.replace('@FUNCTIONS@',copies))
        run([*flags,'-fno-builtin',f,'-o',exe],env=env);lines=run([exe],env=env).splitlines();result['copy_cases']=int(lines[-1])
        f.write_text('#define _POSIX_C_SOURCE 200809L\n'+TYPES+BENCH.replace('@FUNCTIONS@',copies))
        run(['gcc','-std=c11','-Os','-fno-builtin','-fno-tree-loop-distribute-patterns',f,'-o',exe],env=env)
        result['host_benchmark_only']=json.loads(run([exe],env=env))
        f.write_text(TYPES+copies)
        gcc=a.arm_bin/'arm-none-eabi-gcc';obj=w/'copy.o'
        run([gcc,'-std=c11','-Os','-mcpu=cortex-m7','-mthumb','-ffreestanding','-ffunction-sections','-I',a.newlib_include.resolve(),'-c',f,'-o',obj])
        nm=run([a.arm_bin/'arm-none-eabi-nm','-S','--size-sort',obj])
        result['arm_copy_function_bytes']={name:int(size,16) for _,size,name in re.findall(r'([0-9a-f]+)\s+([0-9a-f]+)\s+T\s+(\w+)',nm)}
        (out/'arm-copy-disassembly.txt').write_text(run([a.arm_bin/'arm-none-eabi-objdump','-dr',obj]))
        layout={}
        for name,ref in [('original',BASE),('community',DONOR)]:
            hdr=show(ref,'firmware/file_types.h')
            s=TYPES+hdr+'\nint main(void){printf("%zu %zu %zu %zu %zu\\n",sizeof(CFG_FILE),offsetof(CFG_FILE,flags),offsetof(CFG_FILE,reserved),offsetof(CFG_FILE,path),offsetof(CFG_FILE,file));}\n'
            f.write_text(s);run(['gcc',f,'-o',exe]);values=list(map(int,run([exe]).split()))
            layout[name]=dict(zip(['size','flags','reserved','path','file'],values))
        result['configuration_layout']=layout
        donor_fn=function(show(DONOR,'firmware/loader.c'),'static inline bool no_autostart_prg(')
        f.write_text(TYPES+show(DONOR,'firmware/file_types.h')+'\n'+donor_fn+r'''
int main(void){
    for(unsigned enabled=0;enabled<2;enabled++)for(unsigned type=0;type<9;type++){
        cfg_file.flags=enabled?CFG_FLAG_AUTOSTART_PRG:0;cfg_file.boot_type=type;
        bool expected=!enabled&&(type==CFG_PRG||type==CFG_DISK);
        assert(no_autostart_prg()==expected);
    }
    puts("PASS");
}''')
        run(['gcc',f,'-o',exe]);assert run([exe]).strip()=='PASS'
        main=show(DONOR,'firmware/main.c')
        assert main.count('no_autostart_prg()')==1
        assert 'if (!auto_boot() || no_autostart_prg())' in main
        assert main.index('no_autostart_prg()')<main.index('menu_loop();')<main.index('if (!c64_set_mode())')
        result['program_option']={'truth_table_cases':18,'hook':'startup before menu_loop, not manual load/RUN','configuration_layout_compatible':False}
        builds={}
        for name,loader_text,runtime_text in [('baseline',original,runtime),('reject_only',patched,runtime),('copy_only',original,runtime.replace(byte,word)),('combined',patched,runtime.replace(byte,word)),('alias_copy_only',original,runtime.replace(byte,alias)),('reject_and_alias',patched,runtime.replace(byte,alias))]:
            dest=w/name;shutil.copytree(a.baseline_build,dest,ignore=shutil.ignore_patterns('build'))
            # The assessment's loader file includes the existing G7 boot hook.
            g7_loader=(dest/'loader.c').read_text();g7_body=function(g7_loader,'static u8 crt_load_file(')
            selected_loader=function(loader_text,'static u8 crt_load_file(')
            (dest/'loader.c').write_text(g7_loader.replace(g7_body,selected_loader))
            assert ('return 0;   // Reject incomplete cartridge' in selected_loader)==(loader_text==patched)
            (dest/'runtime.c').write_text(runtime_text)
            arm_env=env.copy();arm_env['C_INCLUDE_PATH']=str(a.newlib_include.resolve())
            command=['make','-C',dest,'version=2.G7','LAUNCHER='+str(a.launcher.resolve()),'-o',a.launcher.resolve(),'GCC_PATH='+str(a.arm_bin.resolve()),'LIBDIR=-L'+str(a.newlib_libdir.resolve())]
            log=run(command,env=arm_env);(out/(name+'-build.log')).write_text(log)
            elf=dest/'build/KungFuFlash_v2.G7.elf';binary=w/(name+'.bin')
            run([a.arm_bin/'arm-none-eabi-objcopy','-O','binary','--gap-fill','0xff',elf,binary])
            size=run([a.arm_bin/'arm-none-eabi-size','-A',elf]);bss=re.search(r'^\.bss\s+(\d+)\s+(\d+)',size,re.M)
            builds[name]={'arm_bytes':binary.stat().st_size,'arm_bss_bytes':int(bss[1]),'sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}
        result['arm_builds']=builds
        release=(root/'firmware/releases/G7.03/KungFuFlash_v2.G7.03.upd').read_bytes()
        result['released_upd_sha256']=hashlib.sha256(release).hexdigest()
        assert result['released_upd_sha256']=='2d7456f99b3864578da30b0da6280bd0a9ed26ba9e78034f38bb7841253ee402'
        assert hashlib.sha256(release[:builds['baseline']['arm_bytes']]).hexdigest()==builds['baseline']['sha256'],'Baseline build differs from released ARM image'
        result['baseline_matches_released_arm']=True
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
