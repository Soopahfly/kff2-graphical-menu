# G5 hardware test candidate

This build integrates the approved Home border into the live browser. It is
software-checked and has not yet been tested on a physical KFF2 or CRT.
Use a FAT32 SD card. The existing /Games, /Tools, /Utilities and /Favourites
folders are unchanged. No graphics files need copying to the SD card.

Keep an official firmware update and the previous working build available.
Read [the documented recovery methods](../firmware/experimental/RECOVERY.md)
before installing custom firmware. G5 adds a graphics request between the C64
launcher and ARM, so first-boot and screen transitions are useful first checks.

Copy KungFuFlash_v2.G5.upd to SD and select it with a working KFF2 browser to
open the normal upgrade flow. F1 Help shows the v2.G5 identifier after updating.

| Check | Expected result |
|---|---|
| Start and open Games | Home border/title retained; actual SD entries and icons |
| Up/down past 12 entries, then past 23 | Selection stays visible; no missing or duplicated files |
| F2, Browse, other collections | Correct folder/selection; no stuck or blank display |
| DEL, search, Shift+Return, Settings | Native screens work and return to the patterned browser |
| Launch a PRG, CRT, D64/T64 | Same loading/options behavior as the original cart |
| Open disk/tape contents | Filenames/types and locked/unclosed flags remain readable |
| F4, then reset and repeat | Random runs from /Games; recent-game avoidance persists |
| REU in Settings, Save | Existing REU setting remains available |
| Joystick port 2 | Movement, Fire and held-Fire options still work |
| CRT at normal viewing distance | Names, selection and footer readable; border/text not cropped |

Useful report details: C64 model/video standard, CRT/connection (RF, composite
or S-video), last key/action before a failure, file type involved, whether reset
returns to Home, and a photo of any display corruption. Keyboard/joystick
responsiveness and time taken to switch screens are also useful.

The details band shows filename/type and Help/options hints. Play-count and
library-total displays from the design mock-up are not implemented. The history
journal and PC CSV exporter still record launches as described in launch-history.md.
