/* Altered version, 2026. Move Home/font assets into ARM firmware. */
#include "../kff_data.h"
#include "../dir.h"
uint8_t home_command;
void unpack_home(void)
{
    home_command=kff_send_reply(REPLY_HOME_ASSETS);
    if (home_command==CMD_NONE) kff_receive_data((void*)0x4000,16384);
}
