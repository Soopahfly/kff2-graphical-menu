;
; EasyFlash - text_plot_asm.s - Text Plotter
;
; (c) 2011 Thomas 'skoe' Giesel
;
; This software is provided 'as-is', without any express or implied
; warranty.  In no event will the authors be held liable for any damages
; arising from the use of this software.
;
; Permission is granted to anyone to use this software for any purpose,
; including commercial applications, and to alter it and redistribute it
; freely, subject to the following restrictions:
;
; 1. The origin of this software must not be misrepresented; you must not
;    claim that you wrote the original software. If you use this software
;    in a product, an acknowledgment in the product documentation would be
;    appreciated but is not required.
; 2. Altered source versions must be plainly marked as such, and must not be
;    misrepresented as being the original software.
; 3. This notice may not be removed or altered from any source distribution.

.include "c64.inc"

.include "memcfg.inc"

.importzp   ptr1, ptr2, ptr3, ptr4
.importzp   tmp1, tmp2, tmp3, tmp4

; Data import
.import _text_plot_x
.import _text_plot_addr
; Altered version: packed font pointers, compact pixel loop, unused fill removed.

; Altered G5: ARM-supplied font in unused Home bank RAM.
charset_offset_lo = $5900
charset_offset_hi = $5a00
charset_data = $5500

; usage of tmp space in this module
ptr1_char_addr          = ptr1
ptr2_pixel_addr         = ptr2
ptr3_str_addr           = ptr3
tmp1_pixel_col          = tmp1
tmp2_current_col        = tmp2
tmp3_mask               = tmp3
tmp4_str_offset         = tmp4

; =============================================================================
; X coordinate => mask
.rodata
x_pos_to_mask:
        .byte $80, $40, $20, $10, $08, $04, $02, $01

; =============================================================================
;
; void __fastcall__ text_plot_str(const char* ch);
;
; Plot the character ch to the bitmap at _text_plot_addr.
; The parameter _text_plot_x must be consistent with _text_plot_addr.
; No clipping here. The string must be 0-terminated and shorter then 255 chars.
;
; in:
;       AX => str
;
; out:
;   -
;
; =============================================================================
.code
.export _text_plot_str
_text_plot_str:
        sta ptr3_str_addr
        stx ptr3_str_addr + 1

        ; get pointer to bitmap target
        lda _text_plot_addr
        sta ptr2_pixel_addr
        lda _text_plot_addr + 1
        sta ptr2_pixel_addr + 1

        ; calculate bit mask for first pixel row
        lda _text_plot_x
        and #7
        tax
        lda x_pos_to_mask, x
        sta tmp3_mask

        ldy #0
        sty tmp4_str_offset
next_char:
        ldy tmp4_str_offset
        lda (ptr3_str_addr), y          ; load next char
        bne :+
        rts
:
        inc tmp4_str_offset

        ; Altered layout: 256 low offsets and 64 packed high-offset bytes.
        ; Propagate the base+low carry before decoding the extra high bits.
        tay
        lda charset_offset_lo, y
        clc
        adc #<charset_data
        sta ptr1_char_addr
        lda #>charset_data
        adc #0
        sta ptr1_char_addr + 1
        tya
        and #3
        tax
        tya
        lsr
        lsr
        tay
        lda charset_offset_hi, y
        cpx #0
        beq @offset_ready
@offset_shift:
        lsr
        lsr
        dex
        bne @offset_shift
@offset_ready:
        and #3
        clc
        adc ptr1_char_addr + 1
        sta ptr1_char_addr + 1

        ldy #0
        sty tmp2_current_col            ; save index of column
        lda (ptr1_char_addr), y         ; get pixels for column
@next_column:
        sta tmp1_pixel_col              ; save pixels of column

        ldy #0                          ; relative Y, 0..7
        ldx tmp3_mask
@pixel_row:
        ror tmp1_pixel_col              ; next bit (pixel) into C
        bcc :+                          ; no pixel => skip
        txa
        ora (ptr2_pixel_addr), y          ; put pixel
        sta (ptr2_pixel_addr), y
:
        iny
        cpy #8
        bne @pixel_row
        lsr tmp3_mask                   ; update mask for next row
        bne :+
        jsr new_target_byte
:
        inc tmp2_current_col            ; index of next column
        ldy tmp2_current_col
        lda (ptr1_char_addr), y         ; get pixels for column
        bne @next_column

        ; end_of_char:
        lsr tmp3_mask                   ; update mask for next row
        bne :+                          ; (for space between chars)
        jsr new_target_byte
:
        jmp next_char

; update pointer to next byte in X-direction and reset mask
new_target_byte:
        lda #$80
        sta tmp3_mask
        lda ptr2_pixel_addr             ; advance to next byte
        clc
        adc #8
        sta ptr2_pixel_addr
        bcc :+
        inc ptr2_pixel_addr + 1
:
        rts
