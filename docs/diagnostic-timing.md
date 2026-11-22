# Diagnostic timing firmware plan

A future diagnostic build will measure game loading on the KFF2 and let a PC
collect the results over USB serial. Start each test from the normal launcher
with files on the SD card. The cartridge records timestamps as it loads. The PC
receives the completed report separately from the measured work.

## Measurements

| Test | Measure on the cartridge | Measure on the C64 |
| --- | --- | --- |
| Small and large PRGs | Open, SD reads, history lookup and save, time through handover setup | First instruction marker in a synthetic PRG |
| Large EasyFlash CRT | Open, header and bank payload reads, image preparation, history and handover setup | Optional start marker in a synthetic cartridge |
| D64 | Mount, history, handover setup and any disk-set discovery | Time for a test PRG to load a known file from the mounted image |

Record elapsed time from the cartridge accepting the selection. Label the
last firmware timestamp precisely, since finishing handover setup and executing
the first game instruction are distinct events. Use synthetic fixtures with
known sizes and no game ROMs. Start with manual selection so Random's directory
scan cannot influence the baseline.

## Capture and export

- Use a free-running hardware timer with a verified clock. Audit ownership first.
  D64 swapping already uses TIM2 and SD code uses SysTick. The C64 bus handler
  rewrites DWT CYCCNT, so it is unsuitable as the general elapsed timer.
- Capture a fixed number of timestamps and counters in RAM. Report SD bytes,
  read calls and retries, plus the time spent scanning, appending and syncing
  history. Report buffer overflow and mark failed loads as such.
- Prefer deferred export on return to the launcher, when USB is available.
  The current CRT/D64 paths can disable USB before handover. Audit which Menu
  and reset paths restart the MCU, then use a reserved retention area with
  validation if necessary. Prove that the record survives return to the launcher
  and cannot be mistaken for a new run. If retention is unavailable, export a
  partial snapshot before USB shutdown and label its endpoint.
- A Windows or Linux serial collector should accept versioned records and save
  one CSV row per run with build ID, fixture ID, timing units, stage times,
  history mode, outcome and any missing stages. Keep port discovery, retries
  and USB transmission outside the timed interval. Avoid switching on continuous
  USB logging simply to get a trace, as it can change bus timing.

## Test sequence and decisions

1. Use a spare FAT32 card with generated PRG, CRT and D64 fixtures and controlled
   empty and large history journals. Record the card, C64 model and firmware
   revision. Keep normal history semantics in the default diagnostic mode.
2. Compare history enabled with a diagnostic-only bypass on the same fixtures.
   Run each configuration repeatedly, distinguish first and repeat loads and
   report median and spread. Include tests with USB connected and disconnected
   to check that collection does not skew the timings.
3. If history dominates, test an index that preserves saved counts. If CRT reads
   dominate, measure a batched read candidate independently. Try the assessed
   aligned-copy change separately with the same workload. Evaluate each change
   by end-to-end load time as well as its individual stage.
4. Confirm successful and failed fixtures produce interpretable reports, and
   check timing overhead, record retention and normal loading on real hardware.

Status: planned. No diagnostic firmware or collector has been built.
