/* VICE-only cartridge stand-in. Never include this in a native ROM build. */
#ifndef UI_MOCK_BACKEND_H
#define UI_MOCK_BACKEND_H
#include <stdint.h>
void ui_test_init(void);
uint8_t ui_test_menu(void);
uint8_t ui_test_row(void);
uint8_t ui_test_key(void);
void ui_test_checkpoint(void);
void ui_test_finished(void);
void ui_mock_send_byte(uint8_t value);
extern uint8_t test_key_index, test_error, test_result;
extern uint8_t test_reply_count, test_replies[48];
extern uint8_t test_selected, test_folder, test_page, test_select_count;
extern uint8_t test_seen;
extern uint8_t test_asset_count;
extern uint16_t ui_mock_read_ptr;
uint8_t ui_mock_read_byte(void);
void ui_mock_text(void);
void ui_mock_cancel(void);
void ui_test_uniform(void);
void ui_uniform_checkpoint(void);
#endif
