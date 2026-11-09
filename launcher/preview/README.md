# Standalone C64 design preview

The Makefile now delegates to the four-folder design preview in
`experiments/folder-home`. Run `make -C launcher/preview`; the output is copied to
`launcher/build/preview/kff2-menu-preview.prg` for compatibility with the old path.
It requires cc65 and the generated design assets. This standalone preview has no
real SD or cartridge interface. `main.c` here is retained as the historical
four-action prototype source, and is no longer the Makefile's entry point.

For the firmware's actual native-menu harness and tests, see
`experiments/home-integration/README.md` and `preview/kff2-integration-test.prg`.
