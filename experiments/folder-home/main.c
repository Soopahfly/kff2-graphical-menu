/* Folder Home design preview. Altered version, 2026. See root LICENSE.
 * C64-only visual/input prototype. Does not access SD or cartridge registers.
 */
#include <stdint.h>
#include <string.h>
#include <conio.h>
#include <joystick.h>
#include "../../launcher/base.h"
#include "../../launcher/ui/memcfg.h"
#include "assets.h"

#define REG(a) (*(volatile uint8_t*)(a))
static uint8_t saved[8];
static uint8_t selected;

static void unpack(uint8_t* dest, const uint8_t* src)
{
    uint8_t count,value;
    while ((count=*src++) != 0) {
        value=*src++;
        do { *dest++=value; } while (--count);
    }
}

static void select_card(void)
{
    unpack(P_GFX_COLOR,folder_palettes[selected]);
    unpack(P_GFX_BITMAP+19*320,folder_hints[selected]);
}

static void enter(void)
{
    saved[0]=REG(0xd011)&0x7f; saved[1]=REG(0xd016);
    saved[2]=REG(0xd018); saved[3]=REG(0xdd00);
    saved[4]=REG(0xdd02); saved[5]=REG(0xd020);
    saved[6]=REG(0xd015); saved[7]=REG(0x0291);
    REG(0xd011)=saved[0]&0x6f;
    REG(0xd015)=0; REG(0x0291)=0x80;
    unpack(P_GFX_BITMAP,folder_bitmap);
    select_card();
    REG(0xdd02)=saved[4]|3;
    REG(0xdd00)=(saved[3]&0xfc)|2;
    REG(0xd018)=0x78; REG(0xd016)=(saved[1]&0xe0)|8;
    REG(0xd020)=0; REG(0xd011)=(saved[0]&7)|0x38;
}

static void leave(void)
{
    REG(0xd011)=saved[0]&0x6f;
    REG(0xdd00)=saved[3]; REG(0xdd02)=saved[4];
    REG(0xd018)=saved[2]; REG(0xd016)=saved[1];
    REG(0xd020)=saved[5]; REG(0xd015)=saved[6];
    REG(0x0291)=saved[7]; REG(0xd011)=saved[0];
}

static uint8_t run_home(void)
{
    uint8_t c,action;
    enter();waitRelease();
    while (1) {
        c=kbhit()?cgetc():getJoy();
        if (c==CH_CURS_LEFT || c==CH_CURS_RIGHT) selected^=1;
        else if (c==CH_CURS_UP || c==CH_CURS_DOWN) selected^=2;
        else if (c=='g') { action=0;break; }
        else if (c=='t') { action=1;break; }
        else if (c=='u') { action=2;break; }
        else if (c=='f') { action=3;break; }
        else if (c==CH_ENTER || c==CH_SHIFT_ENTER) { action=selected;break; }
        else if (c=='b' || c==CH_F2 || c==CH_STOP) { action=4;break; }
        else if (c=='s' || c==CH_F5) { action=5;break; }
        else if (c==CH_F3) { action=6;break; }
        else if (c=='q' || c==CH_F7) { action=7;break; }
        else continue;
        select_card();
    }
    if (action<4) selected=action;
    waitRelease();leave();return action;
}

int main(void)
{
    uint8_t action;
    bordercolor(COLOR_BLACK);bgcolor(COLOR_BLACK);clrscr();
    if (joy_install(&joy_static_stddrv)!=JOY_ERR_OK) return 1;
    while ((action=run_home())!=7) {
        clrscr();textcolor(COLOR_CYAN);
        if (action<4) cputsxy(2,3,folder_paths[action]);
        else if (action==4) cputsxy(2,3,"SD CARD BROWSER");
        else if (action==5) cputsxy(2,3,"SETTINGS");
        else cputsxy(2,3,"BUILT-IN CART UTILITIES");
        textcolor(COLOR_WHITE);
        cputsxy(2,7,"FOLDER HOME / DESIGN PREVIEW");
        cputsxy(2,10,"Folder routing is not connected yet.");
        cputsxy(2,12,"No SD files are read in this PRG.");
        cputsxy(2,16,"Press a key or fire to return Home.");
        while (!kbhit() && !getJoy());
        if (kbhit()) cgetc();
        waitRelease();
    }
    joy_uninstall();clrscr();textcolor(COLOR_LIGHTBLUE);return 0;
}
