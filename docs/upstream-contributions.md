# Independent features for possible upstream contribution

Updated 17 November 2026. Core firmware enhancements should remain independently
reviewable and usable with the original Kung Fu Flash 2 menu. Their inclusion in
our graphical G8 build must not make the graphical launcher a prerequisite.

This is an implementation policy, not a claim that disk swapping or GMod2 is
already implemented. Offering a feature does not guarantee upstream acceptance.
Do not open issues, submit patches or contact the original developer until the
project owner asks.

## Feature boundaries

| Feature | Independent scope | Dependencies to avoid |
| --- | --- | --- |
| CRT parser rejection | Small loader fix with supported/unsupported bank regression tests | Graphical assets, Home commands, history and settings changes |
| D64 disk swapping | Bounded disk-list parser, safe mount handover, Special-button handling and feedback | Graphical browser, custom tiles, Favourites implementation and Random |
| GMod2 | Cartridge recognition/banking, EEPROM protocol and bounded save lifecycle | Disk swapping, larger-cartridge caching, compressed banks and graphical UI |
| Word-copy optimisation | Runtime function and focused correctness/performance checks | Cartridge-format changes, graphical assets and configuration changes |
| Random preview | Our menu integration first; assess an upstream UI adaptation separately | Do not present our custom UI implementation as a drop-in core patch |

Shared low-level prerequisites, if genuinely necessary, must be small, documented
and reviewable separately. Do not duplicate fragile SD/handle ownership logic just
to make a feature look independent.

## Branch and patch workflow

1. Pin the official upstream commit used for a feature. Use a clean feature branch
   such as `upstream/d64-swapping` or `upstream/gmod2`, rooted in official firmware,
   when implementation starts. Keep unrelated menu changes out of that branch.
2. Implement and test the core feature there. Keep configuration changes explicit
   and compatible; avoid importing a community fork's entire structure or memory map.
3. Bring the reviewed commits or equivalent isolated patches into our G8 integration
   branch. Add graphical-specific controls or presentation in separate commits.
   The integration build may combine features; the core patches remain separable.
4. Before offering a feature, refresh it against the then-current official source.
   Check that it applies cleanly and builds with the original launcher. If upstream
   has already implemented it, compare behavior rather than submitting a duplicate.
5. Prepare an individual patch series and evidence package. Submit only when asked.

Existing `experiments/g8-parser/loader.patch` already changes only the original
loader and has no graphical-menu dependency. Its current test harness lives in
this repository; bundle a minimal standalone harness before offering it upstream.
The G8 test update contains our full graphical firmware and is not itself the
upstream contribution.

Do not create empty feature branches as a substitute for implementation. Each
feature branch should appear when there is code and a defined testable scope.

## What each offer should contain

- One clear problem and feature boundary, with documented prerequisites.
- A small patch or reviewable commit series with original notices, attribution
  and licensing preserved, including community-derived code.
- Build instructions for official firmware and the original launcher, independent
  host tests, and exact flash/RAM measurements for the isolated change.
- User controls, configuration/save formats, error behavior and downgrade effects.
- An honest test record: automated checks, physical hardware results, exact source
  and firmware identity, and remaining limitations. Host tests are not bus-timing
  verification.
- A separate integration note for our graphical firmware, where needed.

For disk swapping, prove preservation of the current disk if the next image
cannot open and safe handling of pending writes. For GMod2, review EEPROM
snapshots, SD-write concurrency and persistence across Menu/reset before calling
save support complete. Neither feature should depend on the other.

## Current position

The parser fix is implemented in the isolated G8 test candidate. Disk swapping
remains the next major feature, with GMod2 conditional after that. The copy
optimisation is still a candidate awaiting physical timing checks. No submission
or upstream acceptance is recorded.
