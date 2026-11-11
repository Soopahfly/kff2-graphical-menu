/* G7 additions to native file options. Copying leaves originals in place. */
static bool favourite_supported(u8 type)
{
    return type==FILE_DIR || type==FILE_CRT || type==FILE_ROM || type==FILE_PRG ||
           type==FILE_P00 || type==FILE_D64 || type==FILE_T64;
}
static u8 favourite_copy(OPTIONS_STATE *state,OPTIONS_ELEMENT *element,u8 flags)
{
    static const char *messages[]={
        "Added to /Favourites. Original kept.",
        "This file is already in /Favourites.",
        "Name already exists. Nothing overwritten.",
        "Incomplete copy exists. Remove\r\n/Favourites/.KFF2-copy.tmp on a PC.",
        "Cannot copy this selection to Favourites.",
        "Folder too deep, too many files, or path too long. Copy not added.",
        "Copy failed. Check space and SD card. Original kept."
    };
    sd_send_prg_message("Copying to /Favourites. Please wait.");
    FAV_RESULT result=fav_add(cfg_file.path,cfg_file.file);
    c64_interface_sync();
    c64_send_warning(messages[result]);
    /* CMD_WARNING acknowledges the key, then waits for CMD_SYNC before it can
     * accept another command. Finish that handshake before sending directory data. */
    c64_interface_sync();
    return options_prev_dir(state,element,flags);
}
