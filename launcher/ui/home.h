/* Graphical launcher prototype, altered version, 2026. Zlib license, see LICENSE. */
#ifndef KFF_HOME_H
#define KFF_HOME_H
#include <stdint.h>
#define HOME_COUNT 4
#define HOME_BROWSE 0
#define HOME_UTILITIES 1
#define HOME_SETTINGS 2
#define HOME_BASIC 3
void home_enter(void);
void home_leave(void);
void home_select(uint8_t selected);
uint8_t home_run(void);
#endif
