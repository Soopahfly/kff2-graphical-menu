/* G7 native Settings callbacks. Existing menu renderer/protocol is reused. */
static const char *settings_reu_size_text(void)
{
    const char *size;
    switch (settings_g7 & G7_REU_SIZE_MASK) {
        case 1: size="512 KB";break;
        case 2: size="256 KB";break;
        default: size="1 MB";break;
    }
    return setting_print("REU size",size);
}
static u8 settings_reu_size_change(OPTIONS_STATE *state,OPTIONS_ELEMENT *element,u8 flags)
{
    u8 size=(settings_g7 & G7_REU_SIZE_MASK)+1;
    if (size>2) size=0;
    settings_g7=(settings_g7 & ~G7_REU_SIZE_MASK) | size;
    return settings_refresh(element,settings_reu_size_text());
}
static const char *settings_autoboot_text(void)
{
    return setting_print("Autoboot last selection",settings_g7 & G7_NO_AUTOBOOT ? "no" : "yes");
}
static u8 settings_autoboot_change(OPTIONS_STATE *state,OPTIONS_ELEMENT *element,u8 flags)
{
    settings_g7^=G7_NO_AUTOBOOT;
    return settings_refresh(element,settings_autoboot_text());
}
