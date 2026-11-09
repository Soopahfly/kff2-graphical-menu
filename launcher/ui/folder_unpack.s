; Raw LZ4 block decoder for the checked 16KB Home VIC bank.
; NMOS 6510 / ca65. cc65 scratch ZP only, no persistent IRQ state.
; Input in cartridge ROM, output $4000-$7fff. Not used for external data.
.import _home_packed
.importzp ptr1, ptr2, ptr3, tmp1, tmp2, tmp3, tmp4
.export _unpack_home
.code
.proc _unpack_home
    lda #<_home_packed
    sta ptr1
    lda #>_home_packed
    sta ptr1+1
    lda #0
    sta ptr2
    lda #$40
    sta ptr2+1
    ldy #0
sequence:
    jsr read
    sta tmp1
    lsr
    lsr
    lsr
    lsr
    jsr length
literals:
    lda tmp2
    ora tmp3
    beq literals_done
    jsr read
    jsr write
    jsr count
    jmp literals
literals_done:
    lda ptr2+1
    cmp #$80
    beq finished
    jsr read
    sta tmp4
    jsr read
    sta ptr3+1
    sec
    lda ptr2
    sbc tmp4
    sta ptr3
    lda ptr2+1
    sbc ptr3+1
    sta ptr3+1
    lda tmp1
    and #15
    jsr length
    clc
    lda tmp2
    adc #4
    sta tmp2
    bcc match
    inc tmp3
match:
    lda (ptr3),y
    inc ptr3
    bne :+
    inc ptr3+1
:
    jsr write
    jsr count
    lda tmp2
    ora tmp3
    bne match
    jmp sequence
finished:
    rts
read:
    lda (ptr1),y
    inc ptr1
    bne :+
    inc ptr1+1
:
    rts
write:
    sta (ptr2),y
    inc ptr2
    bne :+
    inc ptr2+1
:
    rts
count:
    lda tmp2
    bne :+
    dec tmp3
:
    dec tmp2
    rts
length:
    sta tmp2
    lda #0
    sta tmp3
    lda tmp2
    cmp #15
    bne length_done
extension:
    jsr read
    sta tmp4
    clc
    adc tmp2
    sta tmp2
    bcc :+
    inc tmp3
:
    lda tmp4
    cmp #255
    beq extension
length_done:
    rts
.endproc
