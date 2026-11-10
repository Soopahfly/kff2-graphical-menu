/* G7 additions, 2026. Original KFF2 configuration layout is retained. */
#define G7_OPTIONS_TAG 0x47370000u
#define G7_REU_SIZE_MASK 3u
#define G7_NO_AUTOBOOT 4u

static u8 g7_options(void)
{
    u32 value=cfg_file.reserved;
    return (value & ~7u)==G7_OPTIONS_TAG ? value & 7u : 0;
}
static void g7_save_options(u8 options)
{
    cfg_file.reserved=G7_OPTIONS_TAG | (options & 7u);
}
static bool g7_autoboot_enabled(void)
{
    return !(g7_options() & G7_NO_AUTOBOOT);
}
static u32 g7_reu_mask(void)
{
    switch (g7_options() & G7_REU_SIZE_MASK) {
        case 1: return 0x7ffffu;
        case 2: return 0x3ffffu;
        default: return 0xfffffu;
    }
}
