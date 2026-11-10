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
static uint8_t active,top;
static Directory *d;
static char clipped[40];
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
void browser_show(Directory *directory,const char *title)
{
    uint8_t row,col;
    d=directory;
    if (!active) {
        home_enter();
        if (home_command) {home_leave();return;}
        active=1;
    }
    REG(0xd011)&=0x6f;
    for (row=6;row<24;++row) clear_row(row,0x10);
    clear_row(4,0xf0);text(2,4,title,39,288);
    for (col=2;col<38;++col) {
        P_GFX_BITMAP[19*320+col*8+3]=0xff;
        P_GFX_BITMAP[22*320+col*8+3]=0xff;
        P_GFX_COLOR[19*40+col]=0xe0;
        P_GFX_COLOR[22*40+col]=0xe0;
    }
    memset(P_GFX_COLOR+21*40+2,0xf0,36);
    text(2,21,"F1 Help   SHIFT+RETURN Options",38,288);
    text(2,23,"RET Open  DEL Up  F2 Home  F4 Random",38,288);
    top=d->selected<ROWS ? 0 : d->selected-ROWS+1;
    page();REG(0xd011)|=0x10;
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
