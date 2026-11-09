CL65 ?= cl65
PYTHON ?= python3
BUILD := ../../launcher/build/folder-home

.PHONY: all clean check
all: $(BUILD)/kff2-folder-home-preview.prg

check: all
	$(PYTHON) ../../tools/check_folder_home.py

$(BUILD):
	mkdir -p $@

assets.h: design.json ../../tools/design_folder_home.py ../../launcher/ui/charset.sed ../../launcher/ui/kicker.h
	$(PYTHON) ../../tools/design_folder_home.py

$(BUILD)/main.o: main.c assets.h | $(BUILD)
	$(CL65) -t c64 -O -g -c -o $@ $<

$(BUILD)/base.o: ../../launcher/base.c ../../launcher/base.h | $(BUILD)
	$(CL65) -t c64 -O -g -c -o $@ $<

$(BUILD)/kff2-folder-home-preview.prg: $(BUILD)/main.o $(BUILD)/base.o
	$(CL65) -t c64 -Wl -D,__HIMEM__=0x4000 -m $(BUILD)/preview.map -Ln $(BUILD)/preview.lbl -o $@ $^

clean:
	rm -rf $(BUILD)
