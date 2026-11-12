# G8 scope and implementation plan

Planning baseline: G7.03, based on official v2.07 plus documentation commit `9c84d99`.
Updated 12 November 2026. **This is a plan, not an implemented G8 build.** Features
can be simplified, deferred or dropped because of coding complexity, available
skills/time, hardware limits or insufficient test evidence.

## Goal

Make everyday game selection and multi-disk play easier while retaining G7's
graphical interface, original loader behaviour outside the new modes, and existing
configuration/history/Favourites compatibility.

| Priority | Deliverable | Boundary |
| --- | --- | --- |
| 1 | Special-button D64 swapping | Explicit, bounded, same-folder disk sets only |
| 2 | GMod2 loading and EEPROM saves (conditional) | Standard 512 KB images; release only after memory, save and hardware checks |
| 3 | Optional Random preview | Existing immediate launch remains the default |

Implement and test **multi-disk swapping first**, as requested on 12 November.
Then assess and port GMod2 as a **conditional G8 target**, followed by optional
Random preview. Keep the features independent. Neither unfinished GMod2 nor preview
should delay a usable disk-swapping candidate. If GMod2 misses its size, reliability
or hardware gates, keep it on a separate branch and carry it into G9.

## Before a combined G8 candidate

- Complete the remaining [G7 release checks](../firmware/experimental/HARDWARE-TESTS.md):
  Favourites file/folder copies and no-overwrite behaviour; actual REU operation
  at 256 KB, 512 KB and 1 MB.
- Keep the G7 source, firmware and checksum available as the regression baseline.
- Measure each feature's C64 ROM, ARM flash, BSS and stack cost before combining.

G8 design and isolated development can proceed while G7 testing continues.
G7 bug fixes take priority if those tests expose failures. Neither a public release
nor a firmware flash is part of approving this scope document.

## Feature A: D64 disk sets and Special-button swapping

### Initial disk-set format

Use a read-only companion file named **`disks.lst`**, alongside the D64 images in
one game folder. Open a listed D64 normally; the firmware activates its set and
index when mounting that image. No additional Home tile or list-editing UI is needed.

Example contents:

```text
Game Disk 1.d64
Game Disk 2.d64
Game Disk 3.d64
```

Proposed initial limits and rules:

- At most 16 entries, at most 255 bytes per filename, and an 8 KiB list file limit.
- Same-folder D64 basenames only. Reject absolute paths, directory separators,
  drive prefixes, dot/dot-dot traversal, duplicates and non-D64 entries.
- Accept LF/CRLF, blank lines, a final line without a newline and an optional UTF-8
  BOM for files made with Windows tools. No comment syntax in the first version.
- Keep spaces inside filenames. Validate entries using the filesystem's naming rules.
- Reject an oversized/malformed set as a whole; never silently use a truncated list.
- No automatic list generation or modification during gameplay.

Without `disks.lst`, normal D64 operation is unchanged. A disk not listed in an
existing set also mounts normally without enabling swapping. An invalid set gets
a clear pre-launch warning and the choice to continue without swapping or cancel.

Ordinary D64 opening, file options and disk autostart preferences remain unchanged.
The companion list is activated at the actual disk mount, including an autobooted
image. Reconstruct its current index from the mounted filename instead of writing
a G8-only disk mode into the existing configuration.

### Controls and feedback

| Action | Proposed result |
| --- | --- |
| Short press/release of Special | Next listed disk, wrapping at the end |
| Hold about 0.75 seconds, then release | Return to the first listed disk |
| Special without an active set | Existing behaviour |
| Special in CRT/freezer/other modes | Existing cartridge behaviour, no disk-swap interception |

Act once per press/release, with debounce. Use distinct success/error LED feedback;
do not overlay graphics on a running game. Perform swaps only at a safe disk-service
boundary. Never force one through an active write or discard unsynchronised data.
If the safe handover cannot be completed, leave the old disk selected and report
busy/failure rather than silently changing media. Final pulse/hold timings should
be documented from hardware tests before publishing the candidate.

### Safe handover and lifetime rules

The reviewed community code closes the current image before opening its successor.
G8 must validate/open the candidate separately and keep the old image/state until
the replacement is ready. Audit references to image/channel state and handle
ownership before choosing the implementation. Do not copy live FatFs file objects
without a proven ownership/lifetime scheme.

- Preserve the current index and mount on missing, malformed or unreadable next media
  when the original SD/media remains usable. Card removal can make both unavailable.
- Finish or reject pending writes safely; propagate a failed sync rather than losing
  buffered data. Preserve per-image read-only status.
- Reinitialise channels only after a successful handover. No swapping mid-transfer.
- On Menu/reset, close handles and reconstruct any set from the mounted filename as
  appropriate. Test both G7 autoboot settings and the absence/removal of the list.
- Copying an entire game folder to Favourites must copy `disks.lst` too; its relative
  names must resolve to the Favourite's images, not the original Games folder.

Source for review: [r107sl enhanced branch](https://codeberg.org/r107sl/KungFuFlash2/src/branch/enhanced).
Port the relevant code with attribution and targeted fixes; do not import its
different configuration and memory layout wholesale.

## Feature B: GMod2 and EEPROM save persistence (conditional)

Scope: standard GMod2 CRT type 60, up to 512 KB ROM, plus its 2 KB M93C86 save
memory. Reuse the existing cartridge buffer rather than introducing SD bank
paging, compressed banks or larger-cartridge support.

The inspected candidate is [lroby74's magicdesk16-gmod2 branch](https://codeberg.org/lroby74/KungFuFlash2/src/branch/magicdesk16-gmod2),
commit `653e03d779220841acd31c22ad46403c2696b402` (1 November 2026). It shares our
upstream base, but its complete diff is about 2,500 added lines spanning cartridge
caching, DMA and SD writes. The GMod2 module itself is about 490 lines. Isolate
that feature and its genuinely required hooks; preserve licensing and attribution.
Do not import the whole branch to obtain one cartridge type.

### Implementation and acceptance gates

- Add CRT recognition, ROM banking and the serial EEPROM protocol. Cover both
  default erased saves and supported EEPROM CHIP packets embedded at $DE00.
- Store per-game EEPROM data in a documented companion save file. Define save
  timing across Menu, reset and power-off; do not promise instant persistence
  before the actual write/sync lifecycle is verified.
- Review SD-write concurrency and C64 hold/release. The donor can write from a
  live EEPROM buffer or hold the C64; these paths require review, stable save
  snapshots or equivalent protection, and fault tests in our build.
- Bound paths and validate missing, short, corrupt, read-only and unwritable save
  files. Preserve the original CRT and handle errors without hanging the C64.
- Reconcile open save handles with launching another cartridge, Menu, reset,
  Favourites copies and disk-set state cleanup. No simultaneous CRT+REU support.
- Compare banking/protocol traces with reference behaviour; test real FatFs
  persistence and injected failures, then representative GMod2 games on hardware.
- Measure ARM flash, BSS, stack and any C64 growth after isolation and again after
  integration. No claim of fit until the combined candidate is compiled.

The source candidate does not implement actual flash-chip programming. Physical
GMod2 flashing utilities are outside this game-loading feature. Larger cartridges,
compressed/paged bank caches and automatic conversion of other cartridge formats
remain separate work.

GMod2 is not a mandatory dependency of the first G8 disk-swapping candidate.
Keep G7.03 unchanged as the released regression baseline while testing.

## Feature C: Random preview

### User behaviour

Add **Random action: Launch / Preview** to Settings, stored by the existing Save
action. Default to Launch for an existing card or invalid/unrecognised preference.

| Mode/action | Result |
| --- | --- |
| Launch, F4 | Existing immediate random launch |
| Preview, F4 | Pick an eligible Games file, open its containing folder and highlight it |
| Return on that pending candidate | Launch that same file using Random's existing loader policy |
| F4 again | Pick again; avoid the previous preview where another candidate in the same eligible pool exists |
| Select a different file | Normal manual launch and manual history origin |
| Open options, change search/context or return through Home | Clear the pending Random intent; preserve normal controls |

Preview does not start a loader, set a game to autoboot, append launch history or
change the recent-game window. Only an actual loader-prepared launch is counted.
A single-candidate pool may repeat. Previewed-but-unplayed files are not marked
as played merely to prevent repeats.

Keep the existing recursive `/Games` scope, filtering, recent avoidance and C128
checks. Random remains file-based: helpers and secondary disks can still be picked.
Do not claim that the presence of a disk-set list makes Random choose disk one.

### Implementation decisions

- Reuse the existing directory selection path: `cfg_file.file` plus `sd_handle_dir`
  can locate the selected filename across normal 23-entry packets. The C64 renderer
  already keeps that selection visible in its twelve-row viewport.
- Refactor selection from execution in `home_random`; accepting a preview must not
  call the sampler again and launch a different file.
- Preserve Random's current PRG filesystem mounting and D64/T64 autostart policy
  when accepting the pending candidate, even if ordinary disk autostart is disabled.
  Unrelated manual selections keep their existing behaviour.
- Track the pending full path and platform context, not just a global random-origin
  boolean. Apply random history origin only to the matching accepted launch; clear
  it on cancellation, errors or unrelated selections.
- Cursor movement is local to the C64. Do not assume the ARM receives every cursor
  move: leaving and returning to the same row need not cancel the pending candidate.
- Proposed storage: unused bit `0x04` of the original `cfg_file.flags`, after an
  audit of all flag users. G7 ignores/preserves that bit in its current code.
  **Do not add a new bit to G7's tagged reserved word:** G7 rejects unknown bits
  there and would fall back to defaults for its REU-size/autoboot preferences.
- Keep the 1,024-byte configuration layout, signature and existing offsets. Test
  G7-to-G8-to-G7 settings saves and Save/Cancel/failure behaviour explicitly.

## Explicitly out of scope

Larger-cartridge bank caching and flash-chip programming tools, REU image loading/saving, exFAT,
simultaneous CRT+REU, KERNAL/freezer extensions, move/rename, recent-games/statistics
screens, automatic disk-set inference, in-cart list editing and D71/D81 swapping.
Normal loading of existing supported formats must remain available.

## Work breakdown

| Step | Output | Exit condition |
| --- | --- | --- |
| 1. Compatibility and size audit | Disk-image/handle ownership and memory budget first; audit preview configuration/state before that later feature | No unplanned layout/protocol change; fit is plausible |
| 2. Disk-set parsing | Bounded read-only parser and mount-time activation | Real FatFs tests cover valid/invalid sets, paths and resource cleanup |
| 3. Safe swapping | Button state machine, handover, write/read-only/error handling and LED feedback | Host disk-service tests pass, old-media preservation demonstrated |
| 4. Isolate GMod2 | Bounded CRT/EEPROM port and reviewed SD-write hooks | Standalone size/protocol/FatFs tests pass |
| 5. GMod2 integration gate | Combined-memory measurements, save/reset/error handling and cartridge regressions | Retain only if safe fit and targeted hardware tests pass; otherwise defer to G9 |
| 6. Optional Random preview | Settings callback, selection/launch separation, pending-origin handling and tests | Host/VICE checks pass; immediate mode unchanged |
| 7. Integration | Disk-first candidate or combined build, updated guides and exact checksum | All G7 regression suites and new tests pass; measured limits satisfied |
| 8. Hardware candidate | Targeted test firmware with known limits | Tester results cover enabled G8 features and retained G7.03 functionality |

Prefer ARM-side changes and existing commands/rendering. G7.03 starts with 627 bytes
free in the C64 ROM allocation and 20,684 bytes in its existing ARM flash allocation.
Account for list storage, pending paths, temporary image state, BSS and stack too.
If any feature needs substantial C64 growth, stop and review the design/fit
before expanding the scope or using the reserved flash gap.

## Required validation

### Automated

- Preview counts/origin, rerolls, one-file pools, scan failures and moved/missing files.
- Correct selected page/row beyond both viewport and packet boundaries; Home/search/
  options transitions; unsaved CRT prompts and C128 rejection.
- Accepted PRG/CRT/P00/D64/T64 paths, including disk autostart disabled in Settings.
- Configuration defaults, Save/Cancel, unknown bits and G7 downgrade round trips.
- List encoding/limits, duplicate/traversal rejection and missing/invalid media.
- Repeated swaps, wrap/first action, debounce/hold, busy writes, read-only images,
  injected open/read/sync failures, handle cleanup and copied Favourite disk sets.
- Existing VICE, Home/random/history, real FatFs, G7 copy/REU and package-layout checks.

### Hardware before calling G8 tested

- Preview from Home and browser; accept/reroll/cancel; verify launch-history origin.
- A real multi-disk D64 game through next/wrap/first, including a saved-game workflow.
- A controlled missing-next-image case with the current disk retained.
- Joystick/menu/reset/autoboot paths, REU-enabled disk mode and Special in a freezer CRT.
- Recheck G7 Favourites and settings. Record tested board/video setups and leave
  untested USB/C128/CRT-display combinations explicitly unverified.

Do not deliberately remove power/card during live writes; use injected failures
and a disposable test volume for destructive storage tests. A test build is not a
public release until its feature-specific checks and regression results are recorded.
