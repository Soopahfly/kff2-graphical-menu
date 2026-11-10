/* Graphical Home dispatch, altered version, 2026. See root LICENSE. */
static u8 home_crt_guard(void)
{
    if (sd_crt_updated(&sd_state))
    {
        menu = &sd_menu;
        return handle_unsaved_crt(cfg_file.file, sd_handle_save_updated_crt);
    }
    return CMD_NONE;
}

static void home_sd_context(void)
{
    /* Options may be over an image browser. Unwind that underlying context. */
    const MENU *base = menu == &options_menu ? options_state.prev_menu : menu;
    if (base == &d64_menu)
    {
        cfg_file.img.element = ELEMENT_NOT_SELECTED;
        d64_close(&d64_state.image);
    }
    else if (base == &t64_menu)
    {
        cfg_file.img.element = ELEMENT_NOT_SELECTED;
        t64_close(&t64_state.image);
    }
    menu = &sd_menu;
}

static u8 home_browse(void)
{
    if (menu == &sd_menu) return CMD_NONE; /* Retain cached page and selection. */
    u8 cmd = home_crt_guard();
    if (cmd != CMD_NONE) return cmd;
    home_sd_context();
    return sd_handle_dir(&sd_state);
}

static u8 home_utilities(void)
{
    u8 cmd = home_crt_guard();
    if (cmd != CMD_NONE) return cmd;
    home_sd_context();
    return handle_utilities();
}

static u8 home_folder(u8 index)
{
    static const char *const paths[] = {"/Games", "/Tools", "/Utilities", "/Favourites"};
    if (index >= 4) return CMD_NONE;
    u8 cmd = home_crt_guard();
    if (cmd != CMD_NONE) return cmd;
    home_sd_context();
    sd_state.search[0] = 0;
    cfg_file.file[0] = 0;
    if (!dir_change(paths[index]))
    {
        if (!dir_change("/")) fail_to_read_sd();
        return handle_unsupported_ex("Folder not found",
            "Create this folder on the SD card", paths[index]);
    }
    return sd_handle_dir(&sd_state);
}

static u8 home_random(u8 flags)
{
    history_random_origin=true;
    u8 cmd = home_crt_guard();
    if (cmd != CMD_NONE) return cmd;
    home_sd_context();
    if (!random_pick(DWT->CYCCNT))
        return handle_unsupported_ex("Random game",
            "Cannot scan Games. Check the SD card, folder paths and nesting depth.", "/Games");
    if (!random_count)
        return handle_unsupported_ex("Random game", "No supported game files found", "/Games");
    if (!dir_change(random_folder)) { fail_to_read_sd(); return CMD_NONE; }
    if (!dir_current(cfg_file.path, sizeof(cfg_file.path)))
    { fail_to_read_sd(); return CMD_NONE; }
    strcpy(cfg_file.file, random_file);
    cfg_file.boot_type = CFG_NONE;
    cfg_file.img.element = ELEMENT_NOT_SELECTED;
    sd_state.search[0] = 0;
    flags &= SELECT_FLAG_C128;
    if (random_type == FILE_CRT)
    {
        /* The normal C128 warning's Continue callback selects a page index.
         * A random file has no page index, so reject that mismatch explicitly.
         */
        FIL file;
        CRT_HEADER header;
        sd_file_open(&file, random_file);
        bool valid = crt_load_header(&file, &header);
        file_close(&file);
        if (!valid) return handle_unsupported(random_file);
        if ((header.cartridge_type & CRT_C128_CARTRIDGE) && !(flags & SELECT_FLAG_C128))
            return handle_unsupported_ex("Random game", "This cartridge needs a C128", random_file);
    }
    if (random_type == FILE_PRG)
    {
        /* Keep filesystem mounting, including support for auxiliary PRG loads. */
        cfg_file.img.mode = DISK_MODE_FS;
        cfg_file.boot_type = CFG_DISK;
        return CMD_WAIT_SYNC;
    }
    if (random_type == FILE_D64)
    {
        u8 result=sd_handle_load(&sd_state,random_file,random_type,flags|SELECT_FLAG_MOUNT,0);
        /* Force LOAD"*" for Random even if ordinary image autostart is off. */
        if(result==CMD_WAIT_SYNC) cfg_file.img.element=0;
        return result;
    }
    if (random_type == FILE_T64) return t64_load_first(random_file);
    return sd_handle_load(&sd_state, random_file, random_type, flags, 0);
}
