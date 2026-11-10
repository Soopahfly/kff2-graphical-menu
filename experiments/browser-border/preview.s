; Static layout preview, altered project work, 2026. See root LICENSE.
; PAL/NTSC, ca65, documented NMOS 6510. BASIC SYS 2061. Space returns to BASIC.
; Screen $5c00-$5fe7, bitmap $6000-$7f3f. No zero page or custom IRQ used.
.export preview_poll, preview_done
.segment "LOADADDR"
.word $0801
.segment "STARTUP"
.word basic_end
.word 10
.byte $9e,"2061",0
basic_end: .word 0
start:
    php
    sei
    lda $d011
    and #$7f
    sta saved
    and #$6f
    sta $d011
    lda $d016
    sta saved+1
    lda $d018
    sta saved+2
    lda $dd00
    sta saved+3
    and #$fc
    ora #2
    sta $dd00
    lda $dd02
    sta saved+4
    ora #3
    sta $dd02
    lda $d020
    sta saved+5
    lda $d015
    sta saved+6
    lda $0291
    sta saved+7
    lda #0
    sta $d020
    sta $d015
    lda #$80
    sta $0291
    lda #$78
    sta $d018
    lda saved+1
    and #$e0
    ora #8
    sta $d016
    lda saved
    and #7
    ora #$38
    sta $d011
    plp
preview_poll:
    jsr $ffe4
    cmp #32
    bne preview_poll
    php
    sei
    lda $d011
    and #$6f
    sta $d011
    lda saved+1
    sta $d016
    lda saved+2
    sta $d018
    lda saved+3
    sta $dd00
    lda saved+4
    sta $dd02
    lda saved+5
    sta $d020
    lda saved+6
    sta $d015
    lda saved+7
    sta $0291
    lda saved
    sta $d011
    plp
preview_done:
    rts
saved: .res 8
.segment "MATRIX"
.incbin "matrix.bin"
.segment "BITMAP"
.incbin "bitmap.bin"
