# Standalone folder design preview. Native firmware uses the integration builder.
.PHONY: all clean
all:
	$(MAKE) -C ../../experiments/folder-home
	mkdir -p ../build/preview
	cp ../build/folder-home/kff2-folder-home-preview.prg ../build/preview/kff2-menu-preview.prg
clean:
	$(MAKE) -C ../../experiments/folder-home clean
	rm -rf ../build/preview
