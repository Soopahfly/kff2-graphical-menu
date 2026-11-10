/* Graphical folder Home, altered version, 2026. See root LICENSE.
 * Exact bitmap/font artwork generated from the folder Home design.
 * Bank $4000-$7fff is scratch while Home is visible: descriptions $4000,
 * four matrices $4500, active matrix $5c00 and bitmap $6000.
 */
#include <stdint.h>
#include <string.h>
#include <conio.h>
#include "../base.h"
#include "home.h"
#include "memcfg.h"
#include "folder_packed.h"
#define REG(a) (*(volatile uint8_t*)(a))
static uint8_t saved[8],selected;
void unpack_home(void);
void home_select(uint8_t index)
{
    memcpy(P_GFX_COLOR,(void*)(0x4500+(uint16_t)index*1000),1000);
    memcpy(P_GFX_BITMAP+19*320,(void*)(0x4000+(uint16_t)index*320),320);
}
void home_enter(void)
{
    saved[0] = REG(0xd011) & 0x7f;
    saved[1] = REG(0xd016);
    saved[2] = REG(0xd018);
    saved[3] = REG(0xdd00);
    saved[4] = REG(0xdd02);
    saved[5] = REG(0xd020);
    saved[6] = REG(0xd015);
    saved[7] = REG(0x0291);
    REG(0xd011) = saved[0] & 0x6f; /* blank while drawing */
    REG(0xd015) = 0;
    REG(0x0291) = 0x80; /* lock character-set toggle while bitmap is active */
    unpack_home();
    home_select(0);
    REG(0xdd02) = saved[4] | 3;
    REG(0xdd00) = (saved[3] & 0xfc) | 2;
    REG(0xd018) = 0x78; /* matrix $5c00, bitmap $6000, VIC bank $4000 */
    REG(0xd016) = (saved[1] & 0xe0) | 8;
    REG(0xd020) = 0;
    REG(0xd011) = (saved[0] & 7) | 0x38;
}
void home_leave(void)
{
    REG(0xd011) = saved[0] & 0x6f;
    REG(0xdd00) = saved[3];
    REG(0xdd02) = saved[4];
    REG(0xd018) = saved[2];
    REG(0xd016) = saved[1];
    REG(0xd020) = saved[5];
    REG(0xd015) = saved[6];
    REG(0x0291) = saved[7];
    REG(0xd011) = saved[0];
}
uint8_t home_run(void)
{
    uint8_t c,action;
    selected=0;home_enter();waitRelease();
    while (1) {
        c = kbhit() ? cgetc() : getJoy();
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
        else if (c==CH_F4) { action=HOME_RANDOM;break; }
        else if (c=='q' || c==CH_F7) { action=7;break; }
        else continue;
        home_select(selected);
    }
    if (action<4) selected=action;
    waitRelease();home_leave();return action;
}
