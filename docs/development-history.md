# Development history

The current candidate is **G7**. Use [Getting started](getting-started.md) and
[the current build report](../firmware/experimental/build-report.json) for current
instructions and measurements. Version labels here describe this custom project.

| Milestone | Main change |
| --- | --- |
| Early prototypes | Graphical launcher concepts, high-kick artwork and initial size experiments |
| G1–G2 | Native Home integration and early loader/menu-context fixes |
| G3 | Persistent launch history and recent-game avoidance for F4 |
| G4 | Initial styled text-browser layout |
| G5 | Live bitmap browser with Home's patterned frame; ARM-supplied graphics/font bank |
| G6 | Shared frame across built-in menus, Help/search, messages and text reading |
| G7 | Favourites file/folder copies, selectable REU size and autoboot setting |

G5 Home and SD-browser rendering were photographed on real KFF2 hardware using
an LCD. G6/G7 have software checks; their added functionality remains unverified
on physical hardware. Physical CRT readability is untested.

## Historical experiments

- [Folder Home prototype](../experiments/folder-home/README.md): static design
  PRG and bitmap renders, separate from the integrated firmware.
- [Border prototype](../experiments/browser-border/README.md): early static
  layout; example play counts and library totals were mock-up data.
- [Launcher size experiments](../experiments/launcher-size/README.md): original
  bounded-formatting/buffer measurements, not current ROM usage.
- [ROM investigation](rom-space-investigation.md): alternative layouts considered
  before the ARM-supplied bank. G7 leaves the reserved 16 KB flash gap blank.
- [UI reduction](ui-size-reduction.md): earlier payload and packing measurements.
- [G5 test plan](g5-testing.md): original checks, with later LCD display evidence noted.

Old update files remain available for comparison or rollback. G1 has known early
menu/loader-context bugs and should not be used as a new test baseline.

## Not in G7

REU image loading/saving, Special-button disk swapping, GMod2/larger-cartridge
support and random preview were reviewed as possible later work. They are not
part of G7 or a promised release. exFAT, simultaneous CRT+REU and on-cart launch
statistics are also not implemented in this build.
