#ifndef KFF_BROWSER_H
#define KFF_BROWSER_H
#include "../dir.h"
void browser_show(Directory *directory, const char *title);
void browser_update(Directory *directory,uint8_t last_selected);
void browser_leave(void);
#endif
