/* Random game selection, altered version, 2026. See root LICENSE.
 * One-pass reservoir sampling: each eligible file has equal selection weight.
 * Scan absolute paths without changing the current directory or cart buffers.
 */
#define RANDOM_MAX_DEPTH 16
static char random_path[sizeof(cfg_file.path)];
static char random_folder[sizeof(cfg_file.path)];
static char random_file[sizeof(cfg_file.file)];
static u8 random_type;
static u32 random_count, random_state;

static u32 random_next(void)
{
    random_state ^= random_state << 13;
    random_state ^= random_state >> 17;
    random_state ^= random_state << 5;
    return random_state;
}

static u32 random_below(u32 bound)
{
    /* Rejection avoids modulo bias. This is game selection, not cryptography. */
    u32 threshold = (0u - bound) % bound;
    u32 value;
    do { value = random_next(); } while (value < threshold);
    return value % bound;
}

static bool random_eligible(u8 type)
{
    return type == FILE_CRT || type == FILE_PRG || type == FILE_P00 ||
           type == FILE_D64 || type == FILE_T64;
}

static bool random_walk(u8 depth)
{
    DIR_t dir;
    FILINFO info;
    if (f_opendir(&dir, random_path) != FR_OK) return false;
    dir.pat = "*";
    size_t length = strlen(random_path);
    bool ok = true;
    while (ok)
    {
        if (!dir_read(&dir, &info)) { ok = false; break; }
        if (!info.fname[0]) break;
        u8 type = get_file_type(&info);
        if (type == FILE_DIR)
        {
            size_t n = strlen(info.fname);
            if (depth >= RANDOM_MAX_DEPTH || length + n + 2 > sizeof(random_path))
            { ok = false; break; }
            random_path[length] = '/';
            memcpy(random_path + length + 1, info.fname, n + 1);
            ok = random_walk(depth + 1);
            random_path[length] = 0;
        }
        else if (random_eligible(type))
        {
            if (++random_count == 0) { ok = false; break; }
            if (random_below(random_count) == 0)
            {
                strcpy(random_folder, random_path);
                strcpy(random_file, info.fname);
                random_type = type;
            }
        }
    }
    if (!dir_close(&dir)) ok = false;
    return ok;
}

static bool random_pick(u32 seed)
{
    /* Human key timing and the running DWT counter vary each invocation. */
    random_state ^= seed;
    if (!random_state) random_state = 0x6d2b79f5u;
    random_count = 0;
    random_file[0] = 0;
    strcpy(random_path, "/Games");
    return random_walk(0);
}
