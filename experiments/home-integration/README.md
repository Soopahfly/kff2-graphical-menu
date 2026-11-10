# Native menu integration, v2.G7

The graphical Home, file browser and built-in menus share the original 16 KB
C64 launcher. G6 extends the frame to Settings, options, Help, search, messages
and text reading. See [screen map and limits](../../docs/uniform-ui.md).

Apply patches in the order used by `tools/build_integrated_launcher.py`: compact
launcher, Home, collection dispatch, text-browser predecessor, bitmap browser,
then uniform UI. ARM packaging applies the separate G7 features patch after the
existing Home/history/asset patches. Shared renderer sources are copied from `launcher/ui`.
The upstream checkout is never edited. Baseline:
`9c84d999f4e2f5b2c7688cbc37a127069f5401b0`.

## Build and check

```sh
python3 tools/build_integrated_launcher.py --upstream /path/to/KungFuFlash2
python3 tools/test_integrated_launcher.py --vice /path/to/x64sc --rom-dir /path/to/C64
python3 tools/test_uniform_ui.py --vice /path/to/x64sc --rom-dir /path/to/C64
python3 tools/build_firmware.py --upstream /path/to/KungFuFlash2
```

C64 ROMs are not distributed. The fixture supplies simulated cartridge packets,
not STM32/SD emulation. Use the firmware on hardware to check actual loading,
USB, REU, cartridge timing and display readability.

Ignored `launcher/build/integration` contains patched native source, the native
ROM, native measurements, interactive PRG, nine automated harness variants,
graphics bank, screenshots and both hash-linked VICE result files.
The final firmware report is under [firmware/experimental](../../firmware/experimental).

Scenarios 1-8 retain navigation, paging, selection flags, F4 and interrupted asset
requests. Scenario 9 checks twelve screen states including menu scrolling,
non-selectable information, warnings/progress without extra asset requests,
reader wrapping/forward/back and native startup fallback. Separate keyboard-buffer
and NTSC checks remain.

The VICE fixture places its compressed graphics and mock-only code in a separate
RAM segment at $9000, leaving the real graphics bank $4000-$7fff untouched.
Its BSS is $8000-$8fff and C stack below $c000. None of these fixture relocations
change the native cartridge memory layout.

Native C64 image: 16 KB, 630 bytes free in its main allocation. Graphics/font bank:
16 KB supplied by the existing ARM reply. Full update: 128 KB with the reserved
16 KB gap preserved. Asset bytes and loader/emulation implementations are unchanged.

G7 adds native options/settings entirely on the ARM side. See
[G7 features and compatibility](../../docs/g7-features.md). The base is v2.07
plus its documentation-only commit 9c84d99.
