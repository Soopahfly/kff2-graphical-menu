#!/usr/bin/env python3
"""Exercise G7 configuration and copy code against real upstream FatFs."""
from pathlib import Path
import argparse,os,re,shutil,subprocess,tempfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--upstream',required=True,type=Path)
p.add_argument('--firmware',type=Path)
a=p.parse_args();root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='kff-g7-') as d:
    work=Path(d);fs=work/'fatfs';shutil.copytree(a.upstream/'firmware/fatfs',fs)
    conf=fs/'ffconf.h';conf.write_text(conf.read_text().replace('#define FF_USE_MKFS\t\t0','#define FF_USE_MKFS\t\t1'))
    source=(root/'tests/g7_features.c').read_text()
    for token,path in [('COMMANDS',a.upstream/'firmware/commands.h'),('FILE_TYPES',a.upstream/'firmware/file_types.h'),('SETTINGS',root/'firmware/g7_settings.c'),('FAVOURITES',root/'firmware/favourites.c')]:
        source=source.replace('@'+token+'@',path.read_text())
    firmware=a.firmware or root/'launcher/build/arm-firmware/firmware'
    loader=(firmware/'loader.c').read_text()
    autoboot=loader[loader.index('static bool auto_boot(void)'):loader.index('static bool save_cfg(void)')]
    assert 'g7_autoboot_enabled()' in autoboot,'G7 auto-boot hook missing in built source'
    source=source.replace('@AUTO_BOOT@',autoboot)
    settings=(firmware/'menu_settings.c').read_text()
    save=settings[settings.index('static u8 settings_save('):settings.index('#include "g7_menu_settings.inc"')]
    assert 'g7_save_options(settings_g7)' in save
    source=source.replace('@SETTINGS_SAVE@',save)
    source=source.replace('@SETTINGS_CALLBACKS@',(root/'firmware/g7_menu_settings.inc').read_text())
    source=source.replace('@FAVOURITES_MENU@',(root/'firmware/menu_favourites.c').read_text())
    # Derive valid outer-loop commands from the real C64 dispatcher. A warning
    # exits menuLoop(), so merely completing CMD_SYNC cannot make READ_DIR valid.
    launcher=(root/'launcher/build/integration/source/launcher/main.c').read_text()
    outer=launcher.split('static void mainLoopKFF(void)\n{',1)[1].split('static const char *kff_receive_text',1)[0]
    cases=re.findall(r'case (CMD_\w+):',outer)
    assert 'CMD_MENU' in cases and 'CMD_WARNING' in cases and 'CMD_READ_DIR' not in cases
    browser=launcher.split('static uint8_t menuLoop(void)\n{',1)[1].split('static ',1)[0]
    assert 'case CMD_WARNING:' not in browser and 'return cmd;' in browser
    source=source.replace('@OUTER_COMMAND_CASES@','\n'.join('case '+c+':' for c in cases))
    f=work/'test.c';f.write_text(source);exe=work/'test'
    env=os.environ.copy();env.pop('C_INCLUDE_PATH',None);env['ASAN_OPTIONS']='detect_leaks=0'
    subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-fsanitize=address,undefined','-I',fs,f,fs/'ff.c',fs/'ffunicode.c','-o',exe],check=True,env=env)
    subprocess.run([exe],check=True,env=env)
    reu=(root/'tests/g7_reu.c').read_text()
    for token,path in [('FILE_TYPES',a.upstream/'firmware/file_types.h'),('SETTINGS',root/'firmware/g7_settings.c'),('REU',firmware/'cartridges/reu.c')]:
        reu=reu.replace('@'+token+'@',path.read_text())
    f.write_text(reu)
    subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-fsanitize=address,undefined','-fno-sanitize=alignment',f,'-o',exe],check=True,env=env)
    subprocess.run([exe],check=True,env=env)
