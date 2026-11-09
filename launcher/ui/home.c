/* Graphical launcher prototype, altered version, 2026. Zlib license, see LICENSE.
 * Proportional text renderer and font: Thomas Giesel / EasyFlash 3.
 * No SD or cartridge-register access: usable by the launcher and VICE preview.
 */
#include <stdint.h>
#include <string.h>
#include <conio.h>
#include "../base.h"
#include "home.h"
#include "memcfg.h"
#include "text_plot.h"
#include "kicker.h"

#define REG(a) (*(volatile uint8_t*)(a))
static uint8_t saved[8];
static const char* labels[HOME_COUNT] = {
    "Browse SD card", "Utilities", "Settings", "Return to BASIC"
};
static const char* hints[HOME_COUNT] = {
    "Games, cartridges and disk images",
    "Open the cartridge utilities",
    "Configure your Kung Fu Flash 2",
    "Start BASIC with cartridge active"
};
static const char* shortcuts[HOME_COUNT] = {"B", "U", "S", "Q"};

static void colors(uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t color)
{
    while (h--) {
        memset(P_GFX_COLOR + (uint16_t)y * 40 + x, color, w);
        ++y;
    }
}
static void text(uint8_t x, uint8_t y, const char* s)
{
    text_plot_puts(x, 0, y, s);
}
/* Count/value RLE, written directly into the VIC bitmap without a buffer. */
static void artwork(uint8_t x, uint8_t y, uint8_t width, const uint8_t* src)
{
    uint8_t count, value;
    uint16_t column = 0;
    uint16_t row_bytes = (uint16_t)width * 8;
    uint8_t* dest = P_GFX_BITMAP + (uint16_t)y * 320 + x * 8;
    while ((count = *src++) != 0) {
        value = *src++;
        do {
            *dest++ = value;
            if (++column == row_bytes) {
                column = 0;
                dest += 320 - row_bytes;
            }
        } while (--count);
    }
}
void home_select(uint8_t selected)
{
    uint8_t i, y;
    for (i = 0; i < HOME_COUNT; ++i) {
        y = 7 + i * 3;
        colors(2, y, 24, 2, i == selected ? 0x03 : 0xfb);
        /* Text stays in the bitmap; selection changes matrix colours only. */
    }
    memset(P_GFX_BITMAP + 21 * 320, 0, 320);
    text(2, 21, hints[selected]);
}
void home_enter(void)
{
    uint8_t i, y;
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
    memset(P_GFX_BITMAP, 0, 8000);
    memset(P_GFX_COLOR, 0x10, 1000);
    artwork(2, 1, TITLE_TILE_COLS, title_rle);
    colors(2, 1, 36, 2, 0x30);
    text(2, 4, "GRAPHICAL LAUNCHER / DEVELOPMENT PREVIEW");
    colors(2, 4, 36, 1, 0xc0);
    for (i = 0; i < HOME_COUNT; ++i) {
        y = 7 + i * 3;
        text(3, y, shortcuts[i]);
        text(6, y, labels[i]);
    }
    /* The same native pixels, stored as a compact stream. */
    artwork(29, 7, KICKER_TILE_COLS, kicker_rle);
    colors(29, 7, 8, KICKER_TILE_ROWS, 0x30);

    text(2, 23, "CURSOR / JOY 2: MOVE    RETURN / FIRE: OPEN");
    colors(2, 23, 36, 1, 0xc0);
    /* Header and footer rules. All writes stay within the 320x200 bitmap. */
    for (i = 2; i < 38; ++i) {
        P_GFX_BITMAP[5 * 320 + i * 8 + 4] = 0xff;
        P_GFX_BITMAP[22 * 320 + i * 8 + 3] = 0xff;
    }
    colors(2, 5, 36, 1, 0x60);
    colors(2, 22, 36, 1, 0x60);
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
    uint8_t c, selected = 0;
    home_enter();
    waitRelease();
    while (1) {
        c = kbhit() ? cgetc() : getJoy();
        if (c == CH_CURS_UP || c == CH_CURS_LEFT)
            selected = selected ? selected - 1 : HOME_COUNT - 1;
        else if (c == CH_CURS_DOWN || c == CH_CURS_RIGHT)
            selected = (selected + 1) % HOME_COUNT;
        else if (c == 'b' || c == CH_F2 || c == CH_STOP) { selected = HOME_BROWSE; break; }
        else if (c == 'u' || c == CH_F3) { selected = HOME_UTILITIES; break; }
        else if (c == 's' || c == CH_F5) { selected = HOME_SETTINGS; break; }
        else if (c == 'q' || c == CH_F7) { selected = HOME_BASIC; break; }
        else if (c == CH_ENTER || c == CH_SHIFT_ENTER) break;
        else continue;
        home_select(selected);
    }
    waitRelease();
    home_leave();
    return selected;
}
