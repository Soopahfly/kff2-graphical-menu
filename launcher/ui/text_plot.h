
#ifndef _TEXT_PLOT_H_
#define _TEXT_PLOT_H_

#include <stdint.h>
#include <c64.h>

void __fastcall__ text_plot_puts(
        uint8_t x_pos, uint8_t x_offset, uint8_t y_pos,
        const char* str);

/* Used internally only: */
void __fastcall__ text_plot_str(const char* str);

#endif
