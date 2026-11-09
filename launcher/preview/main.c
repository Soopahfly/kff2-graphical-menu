/* Standalone VICE preview. Illustrative entries, no SD or KFF2 emulation. */
#include <conio.h>
#include <joystick.h>
#include <stdint.h>
#include "../base.h"
#include "../ui/home.h"

static void browser(void)
{
    static const char* entries[] = {
        "Games/", "Demos/", "Utilities/", "Prince of Persia.crt",
        "Sam's Journey.crt", "Ghosts'n Goblins.d64", "Boulder Dash.prg"
    };
    uint8_t i, c, selected = 0;
    while (1) {
        clrscr();
        textcolor(COLOR_CYAN);
        cputsxy(1, 1, "SD BROWSER / SAMPLE CONTENT");
        textcolor(COLOR_GRAY2);
        cputsxy(1, 3, "Preview only. No files are loaded.");
        for (i = 0; i < 7; ++i) {
            textcolor(i == selected ? COLOR_CYAN : COLOR_WHITE);
            revers(i == selected);
            cprintf("\r\n  %-35s", entries[i]);
        }
        revers(0);
        textcolor(COLOR_GRAY2);
        cputsxy(1, 23, "F2 / RUN-STOP: HOME   RETURN: SELECT");
        do { c = kbhit() ? cgetc() : getJoy(); } while (!c);
        if (c == CH_F2 || c == CH_STOP || c == CH_DEL) break;
        if (c == CH_CURS_UP) selected = selected ? selected - 1 : 6;
        if (c == CH_CURS_DOWN) selected = (selected + 1) % 7;
        if (c == CH_ENTER || c == CH_SHIFT_ENTER) {
            cputsxy(1, 16, "Selection received. Loader is mocked.");
            waitRelease();
            while (!kbhit() && !getJoy());
            if (kbhit()) cgetc();
        }
    }
    waitRelease();
}
int main(void)
{
    uint8_t action;
    bordercolor(COLOR_BLACK);
    bgcolor(COLOR_BLACK);
    clrscr();
    if (joy_install(&joy_static_stddrv) != JOY_ERR_OK) return 1;
    while (1) {
        action = home_run();
        if (action == HOME_BASIC) break;
        if (action == HOME_BROWSE) browser();
        else {
            clrscr();
            textcolor(COLOR_CYAN);
            cputsxy(2, 3, action == HOME_SETTINGS ? "SETTINGS" : "UTILITIES");
            textcolor(COLOR_WHITE);
            cputsxy(2, 6, "This action needs the KFF2 firmware.");
            cputsxy(2, 8, "The preview tests the menu interface.");
            cputsxy(2, 11, "Press a key or joystick fire for home.");
            while (!kbhit() && !getJoy());
            if (kbhit()) cgetc();
            waitRelease();
        }
    }
    joy_uninstall();
    clrscr();
    textcolor(COLOR_LIGHTBLUE);
    return 0;
}
