#ifndef KFF_BROWSER_H
#define KFF_BROWSER_H
#include "../dir.h"
void browser_show(Directory *directory, const char *title);
void browser_update(Directory *directory,uint8_t last_selected);
void browser_leave(void);
void browser_panel(const char *title,const char *footer);
void browser_line(uint8_t row,const char *value,uint8_t color);
void browser_block(const char *value);
void browser_search(const char *value,uint8_t cursor,uint8_t visible);
void browser_native_begin(uint8_t reader);
void browser_capture(void);
#endif
