/* VICE-only checks of the actual launcher functions, not a second renderer. */
#pragma code-name (push, "MOCK_CODE")
#pragma rodata-name (push, "MOCK_CODE")
void ui_uniform_stop(void) { }
void ui_uniform_checkpoint(void) {
    volatile uint16_t delay;
    for (delay=0;delay<5000;++delay);
    ui_uniform_stop();
}
static void ui_uniform_menu(const char *title,uint8_t count,uint8_t selected)
{
    uint8_t i;
    memset(dir,0,sizeof(*dir));
    dir->name[0]=' ';strcpy(dir->name+1,title);
    dir->no_of_elements=count;dir->selected=selected;
    for (i=0;i<count;++i) {
        memset(dir->elements[i],' ',ELEMENT_LENGTH);
        dir->elements[i][ELEMENT_LENGTH]=0;
        memcpy(dir->elements[i]+1,"Menu entry",10);
    }
}
void ui_test_uniform(void)
{
    uint8_t before;
    ui_uniform_menu("Settings",6,1);
    strcpy(dir->elements[0]+1," Persist BASIC selection: yes");
    strcpy(dir->elements[1]+1,"     RAM expansion (REU): yes");
    strcpy(dir->elements[2]+1,"   Autostart disk image: yes");
    strcpy(dir->elements[3]+1,"     Disk device number: 8");
    strcpy(dir->elements[4]+1,"Save");strcpy(dir->elements[5]+1,"Cancel");
    showDir();test_seen=1;ui_uniform_checkpoint();
    ui_uniform_menu("Cartridge utilities",5,0);
    strcpy(dir->elements[0]+1,"Sort directory");
    strcpy(dir->elements[1]+1,"Create disk image");
    strcpy(dir->elements[2]+1,"Format EasyFlash");
    strcpy(dir->elements[3]+1,"Export EasyFlash");
    strcpy(dir->elements[4]+1,"Cancel");
    showDir();test_seen=2;ui_uniform_checkpoint();
    ui_uniform_menu("File options / long menu",23,2);
    dir->elements[0][0]=TEXT_ELEMENT;dir->elements[1][0]=TEXT_ELEMENT;dir->text_elements=2;
    strcpy(dir->elements[0]+1,"Read-only information");
    showDir();test_seen=3;ui_uniform_checkpoint();
    dir->selected=20;updateDir(2);test_seen=4;ui_uniform_checkpoint();
    test_seen=5;help();
    test_seen=6;if (search('a')!=REPLY_DIR) test_error=20;
    before=test_asset_count;
    showMessage("Missing folder: /Games\r\nThe SD card root will open instead.",WARNC);
    test_seen=7;ui_uniform_checkpoint();
    ui_mock_cancel();showKFFCancel();
    cputsxy(16,8,"123 / 456");browser_capture();
    if (test_asset_count!=before) test_error=21;
    test_seen=8;ui_uniform_checkpoint();
    ui_mock_text();pageBuffer[0]=DIR_NAME_LENGTH+2;
    showTextPage(0);test_seen=9;ui_uniform_checkpoint();
    showTextPage(1);test_seen=10;ui_uniform_checkpoint();
    showTextPage(0);test_seen=11;ui_uniform_checkpoint();
    if (test_asset_count!=before) test_error=22;
    browser_leave();home_ready=0;
    showMessage("Startup diagnostic before assets arrive",ERRORC);
    if (*(uint8_t*)0xd011&0x20) test_error=23;
    test_seen=12;ui_uniform_checkpoint();
    test_result=!test_error && test_key_index==2;
    ui_test_finished();while(1);
}
#pragma rodata-name (pop)
#pragma code-name (pop)
