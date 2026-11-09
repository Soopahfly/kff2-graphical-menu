/* VICE-only KFF command/byte stand-in. No SD, USB or cartridge emulation.
 * Native menuLoop/readDir/home code consumes these packets without alteration.
 */
#include <stdint.h>
#include <string.h>
#include <conio.h>
#include <joystick.h>
#include "mock_backend.h"
#include "base.h"
#include "dir.h"
#include "launcher_asm.h"

uint8_t test_key_index, test_error, test_result;
uint8_t test_reply_count, test_replies[48];
uint8_t test_selected, test_folder, test_page, test_select_count;
uint8_t test_seen;
static uint8_t dialog;
static uint16_t readpos, writepos;
static char packet[1024];
static const char* root_files[] = {
    "Games                            dir", "Demos                            dir",
    "Utilities                        dir", "Boulder Dash.prg                  32K",
    "Prince of Persia.crt             512K", "Sam's Journey.crt                  1M"
};
static const char* child_files[] = {
    "..                               dir", "Impossible Mission.prg            36K",
    "The Last Ninja.d64               171K"
};

static void field(const char* value, uint8_t size)
{
    while (size--) packet[writepos++] = *value ? *value++ : ' ';
}
static uint8_t directory(uint8_t command, uint8_t selected)
{
    uint8_t i, count;
    const char* name;
    writepos = readpos = 0;
    if (command == CMD_READ_DIR) {
        name = dialog == 1 ? " Settings (simulated)" : dialog == 2 ?
               " Utilities (simulated)" : test_folder ? "\xa0/Games" : "\xa0/";
        field(name, DIR_NAME_LENGTH);
    }
    count = dialog ? 3 : test_folder ? 3 : test_page ? 7 : MAX_ELEMENTS_PAGE;
    for (i=0; i<count; ++i) {
        packet[writepos++] = i == selected ? SELECTED_ELEMENT : NORMAL_ELEMENT;
        if (dialog) name = i == 0 ? "Back to browser" : i == 1 ?
                          "Simulated cartridge action" : "F2 opens the home screen";
        else if (test_folder) name = child_files[i];
        else if (!test_page && i<6) name = root_files[i];
        else name = "Sample entry.prg                  32K";
        field(name, ELEMENT_LENGTH-1);
    }
    if (count<MAX_ELEMENTS_PAGE) {
        packet[writepos++] = 0;
        field("", ELEMENT_LENGTH-1);
    }
    if (writepos>sizeof(packet)) test_error = 1;
    return command;
}
void ui_mock_send_byte(uint8_t value) { test_selected = value; }
void __fastcall__ kff_receive_data(void* dest, uint16_t size)
{
    if (readpos+size>writepos) { test_error=2; memset(dest,0,size); return; }
    memcpy(dest,packet+readpos,size);
    readpos += size;
}
void __fastcall__ kff_send_size_data(void* data, uint8_t size)
{
    /* Search text is passed through the real menu code; this mock does not filter. */
    (void)data; (void)size;
}
uint8_t kff_send_reply_progress(uint8_t reply)
{
    uint8_t item;
    if (test_reply_count<48) test_replies[test_reply_count++] = reply;
    else test_error=3;
    switch(reply) {
        case REPLY_OK: return CMD_NONE;
        case REPLY_DIR:
            dialog=0;
            test_seen |= 1;
            return directory(CMD_READ_DIR,0);
        case REPLY_DIR_NEXT_PAGE:
            test_page=1;test_seen|=16;
            return directory(CMD_READ_DIR_PAGE,0);
        case REPLY_DIR_PREV_PAGE:
            test_page=0;test_seen|=32;
            return directory(CMD_READ_DIR_PAGE,MAX_ELEMENTS_PAGE-1);
        case REPLY_DIR_ROOT:
        case REPLY_DIR_UP:
            dialog=test_folder=test_page=0;
            return directory(CMD_READ_DIR,0);
        case REPLY_SELECT:
            ++test_select_count;
            item=test_selected & 0x3f;
            if (dialog || (test_folder && item==0)) {
                dialog=test_folder=test_page=0;
                return directory(CMD_READ_DIR,0);
            }
            if (!(test_selected & SELECT_FLAG_OPTIONS) && !test_folder && !test_page && item==0) {
                test_folder=1;test_seen|=2;
                return directory(CMD_READ_DIR,0);
            }
            return CMD_MOUNT_DISK; /* Stop before the real loader; record selection only. */
        case REPLY_SETTINGS:
            dialog=1;test_seen|=4;
            return directory(CMD_READ_DIR,0);
        case REPLY_UTILITIES:
            dialog=2;test_seen|=8;
            return directory(CMD_READ_DIR,0);
        case REPLY_BASIC:
            test_seen|=64;
            return CMD_WAIT_RESET;
    }
    test_error=4;
    return CMD_WAIT_RESET;
}
uint8_t __fastcall__ kff_send_reply(uint8_t reply) { return kff_send_reply_progress(reply); }
void kff_wait_for_sync(void) { test_error=5; }
void wait_for_reset(void) { test_error=6; }
uint8_t is_c128(void) { return 0; }
void disk_mount_and_load(void) { test_error=7; }
void ef3usb_load_and_run(void) { test_error=8; }

#ifdef UI_TEST_AUTORUN
#ifndef UI_TEST_SCENARIO
#define UI_TEST_SCENARIO 1
#endif
#if UI_TEST_SCENARIO == 1
static const uint8_t keys[] = {
    'b', CH_ENTER, CH_CURS_DOWN, CH_F2, 'b', CH_F2, 's',
    CH_F2, 'u', CH_F2, 'q'
};
#elif UI_TEST_SCENARIO == 2
static const uint8_t keys[] = {'b', CH_CURS_DOWN, CH_CURS_DOWN, CH_CURS_DOWN, CH_SHIFT_ENTER};
#else
static const uint8_t keys[] = {
    'b', CH_CURS_DOWN,CH_CURS_DOWN,CH_CURS_DOWN,CH_CURS_DOWN,
    CH_CURS_DOWN,CH_CURS_DOWN,CH_CURS_DOWN,CH_CURS_DOWN,
    CH_CURS_DOWN,CH_CURS_DOWN,CH_CURS_DOWN,CH_CURS_DOWN,
    CH_CURS_DOWN,CH_CURS_DOWN,CH_CURS_DOWN,CH_CURS_DOWN,
    CH_CURS_DOWN,CH_CURS_DOWN,CH_CURS_DOWN,CH_CURS_DOWN,
    CH_CURS_DOWN,CH_CURS_DOWN,CH_CURS_DOWN,
    CH_CURS_UP,CH_F2,'b',CH_ENTER
};
#endif
#endif
void ui_test_checkpoint(void) { }
void ui_test_finished(void) { }
uint8_t ui_test_key(void)
{
#ifdef UI_TEST_AUTORUN
    volatile uint16_t delay;
    /* Give VICE time to draw a complete frame before each checkpoint. */
    for (delay=0;delay<5000;++delay);
    ui_test_checkpoint();
#if UI_TEST_SCENARIO == 1
    if (test_key_index==5 && (ui_test_row()!=1 || test_folder!=1)) test_error=10;
#endif
    if (test_key_index<sizeof(keys)) return keys[test_key_index++];
    test_error=9;
    return CH_F7;
#else
    return kbhit() ? cgetc() : getJoy();
#endif
}
int main(void)
{
    uint8_t command;
    ui_test_init();
    while (1) {
        command = ui_test_menu();
#ifdef UI_TEST_AUTORUN
#if UI_TEST_SCENARIO == 1
        test_result = !test_error && command==CMD_WAIT_RESET && test_seen==79 &&
                      test_select_count==1 && test_key_index==sizeof(keys);
#elif UI_TEST_SCENARIO == 2
        test_result = !test_error && command==CMD_MOUNT_DISK && test_selected==(3|SELECT_FLAG_OPTIONS);
#else
        test_result = !test_error && command==CMD_MOUNT_DISK && test_selected==22 &&
                      (test_seen & 48)==48;
#endif
        ui_test_finished();
        clrscr();
        textcolor(test_result ? COLOR_LIGHTGREEN : COLOR_LIGHTRED);
        cputsxy(1,3,test_result ? "INTEGRATION TEST PASSED" : "INTEGRATION TEST FAILED");
        while(1);
#else
        if (command==CMD_WAIT_RESET) {
            test_result = !test_error; ui_test_finished();
            joy_uninstall(); clrscr(); return 0;
        }
        clrscr();
        textcolor(COLOR_CYAN);
        cputsxy(1,3,"SELECTION SENT BY NATIVE LAUNCHER");
        textcolor(COLOR_WHITE);
        cputsxy(1,6,"This harness records the selection.");
        cputsxy(1,8,"No game or SD image is loaded.");
        cputsxy(1,11,"Press a key to return to home.");
        while(!kbhit() && !getJoy());
        if(kbhit()) cgetc();
        waitRelease();
        dialog=test_folder=test_page=0;
#endif
    }
}
