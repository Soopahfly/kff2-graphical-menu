# Standalone C64 PRG. No ARM toolchain or physical KFF2 needed.
CL65 ?= cl65
CA65 ?= ca65
BUILD := ../build/preview
UI := ../ui
OBJECTS := $(BUILD)/main.o $(BUILD)/home.o $(BUILD)/base.o \
           $(BUILD)/text_plot.o $(BUILD)/text_plot_asm.o $(BUILD)/charset.o

.PHONY: all clean
all: $(BUILD)/kff2-menu-preview.prg
$(BUILD):
	mkdir -p $@
$(BUILD)/main.o: main.c $(UI)/home.h | $(BUILD)
	$(CL65) -t c64 -O -g -c -o $@ $<
$(BUILD)/home.o: $(UI)/home.c $(UI)/home.h $(UI)/memcfg.h $(UI)/kicker.h | $(BUILD)
	$(CL65) -t c64 -O -g -c -o $@ $<
$(BUILD)/base.o: ../base.c ../base.h | $(BUILD)
	$(CL65) -t c64 -O -g -c -o $@ $<
$(BUILD)/text_plot.o: $(UI)/text_plot.c $(UI)/text_plot.h $(UI)/memcfg.h | $(BUILD)
	$(CL65) -t c64 -O -g -c -o $@ $<
$(BUILD)/text_plot_asm.o: $(UI)/text_plot_asm.s $(UI)/memcfg.inc | $(BUILD)
	$(CA65) -t c64 -g -I $(UI) -o $@ $<
$(BUILD)/charset.s: $(UI)/charset.sed | $(BUILD)
	sed -e 's/\#/1/g; s/\-/0/g; s/^[01][01]/.byte %&/' $< > $@
$(BUILD)/charset.o: $(BUILD)/charset.s
	$(CA65) -t c64 -g -o $@ $<
$(BUILD)/kff2-menu-preview.prg: $(OBJECTS)
	$(CL65) -t c64 -Wl -D,__HIMEM__=0x4000 -m $(BUILD)/preview.map \
		-Ln $(BUILD)/preview.lbl -o $@ $(OBJECTS)
clean:
	rm -rf $(BUILD)
