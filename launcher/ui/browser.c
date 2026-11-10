/* Patterned browser, altered project work, 2026. See root LICENSE.
 * Home/font bank $4000-$7fff. No persistent use outside menu graphics.
 */
#include <stdint.h>
#include <string.h>
#include "home.h"
#include "browser.h"
#include "text_plot.h"
#include "memcfg.h"
#define REG(a) (*(volatile uint8_t*)(a))
#define ROWS 12
static uint8_t active,top,native_view;
static Directory *d;
static char clipped[41];
static const uint8_t icons[4][8]={
    {0,0x70,0xfe,0x82,0x82,0x82,0xfe,0},
    {0,0x78,0x4c,0x44,0x54,0x54,0x7c,0},
    {0,0x7e,0x52,0x5e,0x42,0x5a,0x7e,0},
    {0,0x7e,0x42,0x5a,0x42,0x7e,0x24,0}};
static void text(uint8_t x,uint8_t row,const char *s,uint8_t length,uint16_t width)
{
    uint8_t i=0,w;
    while (i<length && s[i]) {
        w=((uint8_t*)0x5a40)[(uint8_t)s[i]];
        if (w>width) break;
        width-=w;clipped[i]=s[i];++i;
    }
    clipped[i]=0;text_plot_puts(x,0,row,clipped);
}
static void clear_row(uint8_t row,uint8_t color)
{
    memset(P_GFX_BITMAP+(uint16_t)row*320+16,0,288);
    memset(P_GFX_COLOR+(uint16_t)row*40+2,color,36);
}
static void element(uint8_t index)
{
    uint8_t row,kind=1,sd_style;
    char *s;
    if (index<top || index>=top+ROWS) return;
    row=index-top+7;
    clear_row(row,index==d->selected ? 0x03 : 0x10);
    if (index>=d->no_of_elements) return;
    s=d->elements[index];
    if (d->name[0]==' ') {
        if (*s==TEXT_ELEMENT) memset(P_GFX_COLOR+(uint16_t)row*40+2,0xf0,36);
        text(3,row,s+1,38,280);
        return;
    }
    sd_style=s[34]==' ' && s[35]==' ';
    if (!memcmp(s+36,"dir",3) || (s[1]=='.' && s[2]=='.')) kind=0;
    else if (!memcmp(s+36,"CRT",3)) kind=3;
    else if (s[36]=='D' || s[36]=='d') kind=2;
    if (kind==0 && index!=d->selected)
        memset(P_GFX_COLOR+(uint16_t)row*40+2,0x30,32);
    memcpy(P_GFX_BITMAP+(uint16_t)row*320+16,icons[kind],8);
    if (sd_style) {
        text(4,row,s+1,33,232);
        text(34,row,s+36,3,32);
    } else text(4,row,s+1,38,272); /* Preserve image flags, e.g. *PRG<. */
}
static void details(void)
{
    clear_row(20,0x30);
    if (d->selected<d->no_of_elements) text(2,20,d->elements[d->selected]+1,38,288);
}
static void page(void)
{
    uint8_t i;
    for (i=0;i<ROWS;++i) element(top+i);
    details();
}
void browser_leave(void)
{
    if (active) {home_leave();active=0;}
}
void browser_line(uint8_t row,const char *value,uint8_t color)
{
    clear_row(row,color);text(2,row,value,40,288);
}
void browser_panel(const char *title,const char *footer)
{
    uint8_t row,col;
    native_view=0;
    if (!active) {
        home_enter(1);
        if (home_command) {home_leave();return;}
        active=1;
    }
    for (row=6;row<24;++row) clear_row(row,0x10);
    browser_line(4,title,0xf0);
    for (col=2;col<38;++col) {
        P_GFX_BITMAP[19*320+col*8+3]=0xff;
        P_GFX_BITMAP[22*320+col*8+3]=0xff;
        P_GFX_COLOR[19*40+col]=0xe0;
        P_GFX_COLOR[22*40+col]=0xe0;
    }
    browser_line(23,footer,0xf0);
    REG(0xd011)|=0x10;
}
void browser_show(Directory *directory,const char *title)
{
    d=directory;
    browser_panel(title,d->name[0]==' ' ? "RET Select  DEL Back  F2 Home" :
                  "RET Open  DEL Up  F2 Home  F4 Random");
    if (home_command) return;
    browser_line(21,d->name[0]==' ' ? "CURSOR / JOY 2: Move   F1 Help" :
                 "F1 Help   SHIFT+RETURN Options",0xf0);
    top=d->selected<ROWS ? 0 : d->selected-ROWS+1;
    page();REG(0xd011)|=0x10;
}
void browser_block(const char *value)
{
    uint8_t row=7,n;
    while (*value && row<22) {
        n=0;
        while (*value && *value!='\r' && *value!='\n' && n<38) clipped[n++]=*value++;
        clipped[n]=0;
        /* text() uses the same buffer; copying in place is intentional. */
        browser_line(row++,clipped,0x10);
        if (*value=='\r') ++value;
        if (*value=='\n') ++value;
    }
}
void browser_search(const char *value,uint8_t cursor,uint8_t visible)
{
    uint16_t x=16;
    uint8_t i;
    browser_line(4,value,0xf0);
    if (!visible) return;
    for (i=0;i<cursor;++i) x+=((uint8_t*)0x5a40)[(uint8_t)value[i]];
    if (x<304) P_GFX_BITMAP[4*320+(x>>3)*8+7]^=0x80>>(x&7);
}
void browser_update(Directory *directory,uint8_t last_selected)
{
    uint8_t old_top=top;
    d=directory;
    if (d->selected<top) top=d->selected;
    else if (d->selected>=top+ROWS) top=d->selected-ROWS+1;
    if (old_top!=top) page();
    else {element(last_selected);element(d->selected);details();}
}
/* Native conio remains the terminal for cartridge messages and streamed text.
 * Mirror it into the existing bank, without requesting or consuming KFF data.
 * Before any graphics have arrived, native diagnostics remain available. */
void browser_native_begin(uint8_t reader)
{
    browser_leave();native_view=reader+1;
}
void browser_capture(void)
{
    uint8_t row,col,c,color,view;
    if (!native_view || !home_ready) return;
    view=native_view;
    if (!active) {home_enter(0);active=1;}
    browser_panel("Cartridge status",view==2 ? "CRSR Page  HOME First  RET Exit" :
                  "PRESS A KEY / FIRE when prompted");
    native_view=view;
    for (row=0;row<17;++row) {
        color=1;
        for (col=0;col<40;++col) {
            c=((uint8_t*)0x0400)[(uint16_t)row*40+col]&0x7f;
            if (c<32) c+=64;
            else if (c>=64) c+=128;
            clipped[col]=c;
            if (c!=' ') color=((uint8_t*)0xd800)[(uint16_t)row*40+col]&15;
        }
        clipped[40]=0;
        if (color==13) color=1;
        browser_line(row ? row+5 : 4,clipped,row ? color<<4 : 0xf0);
    }
}
