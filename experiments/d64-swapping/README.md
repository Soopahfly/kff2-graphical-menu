# Standalone D64 disk swapping patch

[d64-swapping.patch](d64-swapping.patch) is based on official Kung Fu Flash 2
commit `9c84d999f4e2f5b2c7688cbc37a127069f5401b0` (v2.07 plus a documentation
commit). It includes the disk service changes and a FAT32 regression test. The
patch needs only official firmware and the original launcher. The separate
graphical build applies the same patch.

The r107sl enhanced branch informed the initial review of disk swapping.
This implementation uses bounded lists, keeps two independent FatFs handles,
and swaps only at an idle disk service boundary. See the candidate notes for
the list format, controls and test status.

Apply and test in a clean upstream checkout:

```sh
git switch -c upstream/d64-swapping 9c84d999f4e2f5b2c7688cbc37a127069f5401b0
git am /path/to/d64-swapping.patch
python3 tests/test_disk_set.py
```

Build the original v2.07 launcher and firmware using the upstream build
instructions. The patch was compiled with ARM GCC 12.2.1 and the original
launcher. Compared with the same stock build, the patch adds 1,272 bytes of ARM flash
(54,184 to 55,456) and 5,432 bytes of static RAM (5,936 to 11,368).
Hardware checks for Special-button timing, drive compatibility and
saved games are still open.
