# Read-only game hash inventory

Run this before copying when you want to compare the card against a game catalogue.
Keep `KFF2-GameCopy.csv` from the copy planner on your Desktop. Then run:

```powershell
$script = "$HOME\Downloads\Get-Kff2Hashes.ps1"
Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/Soopahfly/kff2-graphical-menu/main/tools/Get-Kff2Hashes.ps1' -OutFile $script
powershell -NoProfile -ExecutionPolicy Bypass -File $script -CardRoot 'F:\'
```

Upload `KFF2-Hashes.csv` from your Desktop for matching. This reads the card and
writes the inventory to your Desktop. It does not copy, rename or delete games.
If the output already exists, rename it before rerunning. If the copy plan is
elsewhere, supply `-PlanPath 'C:\path\KFF2-GameCopy.csv'`.

The inventory contains SHA-1 for catalogue matching and SHA-256 for exact duplicate
checks. It scans supported file extensions inside Games, including Games/Homebrew
for duplicate checks. It also scans candidate paths in the original plan, including
MultiLoad64 CRTs and both crunched and uncrunched PRGs. A candidate's inclusion in
this inventory does not approve it for copying or prove it is compatible.

Candidate sources exclude Games, Tools, Utilities, Favourites, Homebrew,
!!Firmware, Demos and Docs at the card root, and Homebrew/Favourites subfolders.
Raw BIN/ROM collections are excluded. Hidden/system files, junctions and symbolic
links are skipped. Keep the card idle while scanning. Missing candidate paths stop
the scan; regenerate the copy plan if files have moved. Individual hashing errors
are recorded in the CSV and must be resolved before relying on those rows.

## Catalogue

The official [TOSEC DAT pack](https://www.tosecdev.org/downloads/category/59-2025-03-13)
contains metadata, not game downloads. Its C64 game DATs record SHA-1, MD5 and CRC32.
Use matching whole-file formats, for example a CRT DAT against a CRT file.
SHA-256 cannot be converted into SHA-1; both must be calculated from the file.

An exact hash match identifies a particular dump or release. Different versions of
the same game can have different hashes. Custom OneLoad64/EasyFlash conversions
may have no TOSEC match. An unmatched file is not necessarily broken or unsafe.
Title matches should remain review suggestions, particularly for different games
sharing a title and multi-disk sets. Do not delete or consolidate solely on a
loosely normalised filename.

Validation: executed on PowerShell 7.7 with a temporary card fixture. Verified both
hash algorithms, bracketed filenames, Games/Homebrew indexing, source exclusions
and MultiLoad64 inclusion. Intended to support Windows PowerShell 5.1, but Windows
execution still needs confirmation on the user's PC.
