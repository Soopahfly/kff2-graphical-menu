/* Folder Home actions. Altered version, 2026. See root LICENSE. */
#ifndef KFF_HOME_H
#define KFF_HOME_H
#include <stdint.h>
#define HOME_COUNT 4
#define HOME_GAMES 0
#define HOME_TOOLS 1
#define HOME_UTILITIES_FOLDER 2
#define HOME_FAVOURITES 3
#define HOME_BROWSE 4
#define HOME_SETTINGS 5
#define HOME_UTILITIES 6
#define HOME_BASIC 7
#define HOME_RANDOM 8
void home_enter(void);
void home_leave(void);
void home_select(uint8_t selected);
uint8_t home_run(void);
#endif
