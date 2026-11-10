# Read-only SD inventory for catalogue matching and exact duplicate checks.
[CmdletBinding()]
param(
    [string]$CardRoot = 'F:\',
    [string]$PlanPath = (Join-Path ([Environment]::GetFolderPath('Desktop')) 'KFF2-GameCopy.csv'),
    [string]$OutPath = (Join-Path ([Environment]::GetFolderPath('Desktop')) 'KFF2-Hashes.csv')
)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $OutPath) { throw "Output already exists: $OutPath. Rename it first." }
$root = (Get-Item -LiteralPath $CardRoot).FullName.TrimEnd('\', '/')
$prefix = $root + [IO.Path]::DirectorySeparatorChar
$extensions = @('.crt', '.prg', '.p00', '.t64', '.d64', '.d71', '.d81')
$excluded = @('Games', 'Tools', 'Utilities', 'Favourites', 'Homebrew', '!!Firmware', 'Demos', 'Docs')
$paths = @{}
$blocked = [IO.FileAttributes]::Hidden -bor [IO.FileAttributes]::System -bor [IO.FileAttributes]::ReparsePoint

function Add-GameFile($file, [string]$scope) {
    if (($file.Attributes -band $blocked) -ne 0) { return }
    if ($extensions -notcontains $file.Extension) { return }
    $paths[$file.FullName] = $scope
}

# Walk directories explicitly so junctions and symbolic links are never followed.
$games = Join-Path $root 'Games'
if (Test-Path -LiteralPath $games -PathType Container) {
    $pending = New-Object 'System.Collections.Generic.Stack[string]'
    $pending.Push($games)
    while ($pending.Count -gt 0) {
        $directory = Get-Item -LiteralPath $pending.Pop()
        if (($directory.Attributes -band $blocked) -ne 0) { continue }
        foreach ($item in Get-ChildItem -LiteralPath $directory.FullName) {
            if (($item.Attributes -band $blocked) -ne 0) { continue }
            if ($item.PSIsContainer) { $pending.Push($item.FullName) }
            else { Add-GameFile $item 'ExistingGames' }
        }
    }
}

# The original plan supplies candidate paths, including reviewed MultiLoad64 CRTs.
# Raw BINs/ROMs and excluded folders are not scanned.
foreach ($row in Import-Csv -LiteralPath $PlanPath) {
    $path = [IO.Path]::GetFullPath($row.Source)
    if (-not $path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { continue }
    $relative = $path.Substring($prefix.Length)
    $parts = $relative -split '[\\/]'
    if ($excluded -contains $parts[0]) { continue }
    if (($parts -contains 'Homebrew') -or ($parts -contains 'Favourites')) { continue }
    if ($extensions -notcontains [IO.Path]::GetExtension($path)) { continue }
    # Check ancestor attributes as well as the file itself.
    $parent = [IO.Path]::GetDirectoryName($path)
    $skip = $false
    while ($parent -and $parent.Length -gt $root.Length) {
        if (((Get-Item -LiteralPath $parent).Attributes -band $blocked) -ne 0) { $skip = $true; break }
        $parent = [IO.Path]::GetDirectoryName($parent)
    }
    if (-not $skip) { Add-GameFile (Get-Item -LiteralPath $path) 'Candidate' }
}

$index = 0
$results = foreach ($path in ($paths.Keys | Sort-Object)) {
    $index++
    Write-Progress -Activity 'Reading game hashes (no SD changes)' -Status "$index / $($paths.Count)" -PercentComplete (100 * $index / $paths.Count)
    $sha1 = ''; $sha256 = ''; $bytes = ''; $status = 'OK'; $message = ''
    try {
        $before = Get-Item -LiteralPath $path
        $bytes = $before.Length
        $sha1 = (Get-FileHash -LiteralPath $path -Algorithm SHA1).Hash
        $sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
        $after = Get-Item -LiteralPath $path
        if ($after.Length -ne $before.Length -or $after.LastWriteTimeUtc -ne $before.LastWriteTimeUtc) {
            throw 'File changed during hashing. Run again while the card is idle.'
        }
    } catch { $sha1 = ''; $sha256 = ''; $status = 'Error'; $message = $_.Exception.Message }
    [pscustomobject]@{ Scope = $paths[$path]; Path = $path; Name = [IO.Path]::GetFileName($path); Bytes = $bytes; SHA1 = $sha1; SHA256 = $sha256; Status = $status; Error = $message }
}
if ($paths.Count -eq 0) { throw 'No game files found. Check CardRoot and PlanPath.' }
$results | Export-Csv -LiteralPath $OutPath -NoTypeInformation -Encoding UTF8 -NoClobber
Write-Progress -Activity 'Reading game hashes (no SD changes)' -Completed
Write-Host "Saved $($paths.Count) records to $OutPath"
Write-Host 'Upload this CSV for catalogue matching. Nothing on the SD card was changed.'
