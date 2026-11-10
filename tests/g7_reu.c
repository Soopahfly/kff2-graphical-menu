/* Exercise actual patched REU DMA callbacks with bus read/write test doubles. */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef uint8_t u8;typedef int8_t s8;typedef uint16_t u16;typedef uint32_t u32;
@FILE_TYPES@
@SETTINGS@
static u8 crt_buf[1024*1024],crt_ram_buf[1024];
static u8 bus_in,bus_out;
static void (*installed)(void);
#define FORCE_INLINE static inline
#define C64_IO2 1
#define C64_WRITE_LOW 1
#define C64_DMA_LOW 2
#define C64_DMA_HIGH 4
#define C64_IRQ_LOW 8
#define C64_IRQ_HIGH 16
#define STATUS_LED_ON 32
#define CRT_PORT_NONE 64
#define C64_ADDR_WRITE(x) ((void)(x))
#define C64_CONTROL_WRITE(x) ((void)(x))
#define C64_DATA_WRITE(x) (bus_out=(x))
#define C64_CRT_CONTROL(x) ((void)(x))
#define C64_DMA_DATA_READ() u32 data=bus_in
#define C64_DMA_WRITE_END() ((void)0)
#define C64_HANDLER_ENABLE() ((void)0)
#define C64_DMA_HANDLER_ENABLE() ((void)0)
#define C64_INSTALL_HANDLER(x) (installed=(x))
#define COMPILER_BARRIER() ((void)0)
#define C64_BUS_HANDLER(x) void x##_handler(void){}
#define C64_DMA_BUS_HANDLER(x) void x##_dma_handler(void){}
@REU@
int main(void)
{
    for(u8 size=0;size<3;++size) {
        g7_save_options(size);reu_init();assert(REU_BASE_MASK==g7_reu_mask());
        u32 mask=REU_BASE_MASK;
        memset(crt_buf,0x5a,sizeof(crt_buf));REU->reu_base=mask;REU->trans_len=3;
        bus_in=0xaa;reu_read_dma_bus_handler();assert(crt_buf[mask]==0xaa);
        bus_in=0xbb;reu_read_dma_bus_handler();assert(crt_buf[0]==0xbb && REU->reu_base==1);
        if(mask+1<sizeof(crt_buf)) assert(crt_buf[mask+1]==0x5a);
        reu_init();REU->reu_base=mask+1;REU->trans_len=2;crt_buf[0]=0xcc;
        reu_write_dma_bus_handler();assert(bus_out==0xcc && REU->reu_base==1);
        reu_init();REU->reu_base=mask+1;REU->trans_len=2;crt_buf[0]=0x31;bus_in=0x62;
        reu_swap_dma_bus_handler();assert(crt_buf[0]==0x62 && REU->temp==0x31 && installed==reu_swap2_dma_handler);
        reu_swap2_dma_bus_handler();assert(bus_out==0x31);
        reu_init();REU->reu_base=mask+1;REU->trans_len=2;bus_in=crt_buf[0];installed=NULL;
        reu_verify_dma_bus_handler();assert(installed==NULL && REU->reu_base==1);
        REU->reu_base=mask+1;REU->trans_len=2;bus_in=crt_buf[0]^255;
        reu_verify_dma_bus_handler();assert(installed==reu_verify_error_dma_handler);
        reu_init();REU->reu_base=mask;REU->trans_len=2;REU->reu_inc=0;
        bus_in=0x7a;reu_read_dma_bus_handler();assert(REU->reu_base==mask);
    }
    puts("PASS: actual REU read/write/swap/verify callbacks wrap at 256/512/1024 KB and preserve fixed-address transfers");
    return 0;
}
