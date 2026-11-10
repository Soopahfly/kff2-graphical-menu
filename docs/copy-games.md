# Copy game candidates from an SD card into Games

[Download Copy-Kff2Games.ps1](../tools/Copy-Kff2Games.ps1) and save it in Downloads.
The script runs locally on your PC. It does not give ChatGPT access to the drive.
Windows PowerShell 5.1 or newer is required. No extra modules are needed.

## Scope

The source scan skips the root Games, Tools, Utilities, Favourites, Homebrew and
!!Firmware folders. Homebrew/Favourites subfolders elsewhere are also excluded.
Hidden/system files and reparse points are skipped. Configuration, history and
firmware update files are not copy candidates. Original files are never moved
or deleted.

Duplicate checks read files throughout the existing Games tree, including its
Homebrew subfolder. SHA-256 checks skip byte-identical files already there, and
copies from other source folders during this run. Different versions/formats of
the same title are not treated as duplicates. Existing duplicates are not removed.

The script considers PRG, P00, T64, CRT, D64, D71 and D81 files. It checks PRG/disk
sizes and P00/T64/CRT header information, including the supported CRT mapper IDs
from the G5 upstream cartridge handler. These are format candidates, not proof
that every game boots or that every PRG is a game. Archives are not unpacked.
TAP/G64/snapshot formats are not included.

Raw ROM/BIN, extensionless potential PRGs and C128 cartridges are listed for
review and not automatically selected. Demos, Docs and MultiLoad64 candidates
are also listed for review. Set Include to True only for items you want copied.

**MultiLoad64 and other multi-file games need care.** A game can need data files
outside the supported game extensions. Globally removing an identical loader
from one game's folder can also break that set. Keep those games together and
review them separately; this tool does not establish their dependencies.

## 1. Generate the plan

In PowerShell, with the SD card still F:

```powershell
$script = "$HOME\Downloads\Copy-Kff2Games.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File $script -CardRoot 'F:\'
```

This creates KFF2-GameCopy.csv on your Desktop and changes no SD file contents.
If a plan already exists, the script stops rather than overwrite your edits.
Choose another -PlanPath or rename the old plan before creating a fresh one.

Open the CSV in a text editor and review Include=True/False. Keep its other
columns unchanged. Review rows and duplicate rows start with Include=False.
Any scan warnings are written beside it as KFF2-GameCopy.csv.warnings.txt.

## 2. Apply the reviewed plan

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $script -CardRoot 'F:\' -Copy
```

Only rows with Include=True are considered. Sources are checked again for
format, allowed location and unchanged SHA-256. Existing Games hashes are
rebuilt before copying. Results are saved beside the plan as .results.csv.

The original relative folder layout is kept under Games, for example:
F:\AlternativeFormats\CRT\Game.crt becomes
F:\Games\AlternativeFormats\CRT\Game.crt.
This also keeps nested disk-image collections together.

Existing destinations are not overwritten. Different content at the same path
gets a hash suffix in its filename. Every copied file is hash-verified before
its temporary file is renamed into place. A source change, read error, full
card or filename/path problem is reported; other selected files can still copy.
Temporary partial files are removed. Keep enough free space for the copies.

For a different plan location, pass the same -PlanPath to both commands.
After copying, safely eject the card. G5's F4 runner scans the new subfolders.
The separate firmware Sort directory command sorts each folder if desired.

## Verification

The fixture tests run the actual script on temporary folders and check:
format/mapper filters, excluded source folders, Games/Homebrew duplicate indexing,
cross-source duplicates, review defaults, preserved paths, literal bracketed
filenames, name collisions, repeated copying and changed-source rejection.
They were run with PowerShell 7.7 on Linux. Windows PowerShell 5.1 compatibility
is intended and syntax-reviewed, but has not been exercised on the user's F drive.

Run locally without Pester:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tests\Copy-Kff2Games.Tests.ps1
```
