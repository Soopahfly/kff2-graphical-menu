#requires -Version 5.1
<#
Build a reviewable game-file copy plan, then execute it with -Copy.
Originals are never moved or deleted. Firmware-owned folders are not sources.
#>
[CmdletBinding()]
param(
    [string]$CardRoot = 'F:\',
    [string]$PlanPath = (Join-Path ([Environment]::GetFolderPath('Desktop')) 'KFF2-GameCopy.csv'),
    [switch]$Copy
)
Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'
$sep = [IO.Path]::DirectorySeparatorChar
$root = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $CardRoot).ProviderPath).TrimEnd([char[]]'\/') + $sep
$games = Join-Path $root 'Games'
$gamesPrefix = $games.TrimEnd([char[]]'\/') + $sep
$warnings = New-Object 'System.Collections.Generic.List[string]'

function Test-InPath([string]$Path, [string]$Parent) {
    $prefix = $Parent.TrimEnd([char[]]'\/') + $sep
    return $Path.Equals($Parent.TrimEnd([char[]]'\/'), [StringComparison]::OrdinalIgnoreCase) -or
        $Path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)
}
function Test-Excluded([string]$Path) {
    $relative = $Path.Substring($root.Length)
    $parts = @($relative -split '[\\/]')
    if ($parts[0] -in @('Games','Tools','Utilities','Favourites','Homebrew','!!Firmware')) { return $true }
    return @($parts | Where-Object { $_ -in @('Homebrew','Favourites') }).Count -gt 0
}
function Get-CardFiles([string]$Start, [bool]$Sources) {
    if (-not (Test-Path -LiteralPath $Start -PathType Container)) { return }
    $stack = New-Object 'System.Collections.Generic.Stack[string]'
    $stack.Push($Start)
    while ($stack.Count) {
        $folder = $stack.Pop()
        try { $children = @(Get-ChildItem -LiteralPath $folder -Force -ErrorAction Stop) }
        catch { $warnings.Add("Cannot read $folder : $($_.Exception.Message)"); continue }
        foreach ($item in $children) {
            if ($item.Attributes -band ([IO.FileAttributes]::ReparsePoint -bor [IO.FileAttributes]::Hidden -bor [IO.FileAttributes]::System)) { continue }
            if ($Sources -and (Test-Excluded $item.FullName)) { continue }
            if ($Sources -and (Test-InPath $item.FullName $games)) { continue }
            if ($item.PSIsContainer) { $stack.Push($item.FullName) } else { $item }
        }
    }
}
function Get-Format([IO.FileInfo]$File) {
    $ext = $File.Extension.ToLowerInvariant(); $size = $File.Length
    switch ($ext) {
        '.prg' { if ($size -gt 2 -and $size -lt 65536) { return 'PRG' }; return $null }
        '' { if ($size -gt 2 -and $size -lt 65536) { return 'Extensionless, review' }; return $null }
        { $_ -in '.rom','.bin' } { if ($size -gt 0 -and $size -le 65536) { return 'Raw ROM, review' }; return $null }
        { $_ -in '.d64','.d71','.d81' } {
            if ($size -in @(174848,175531,196608,197376,205312,206114,349696,351062,819200,822400)) { return $ext.Substring(1).ToUpperInvariant() }
            return $null
        }
        { $_ -in '.crt','.p00','.t64' } {
            $header = New-Object byte[] 64
            $stream = [IO.File]::OpenRead($File.FullName)
            try { $count = $stream.Read($header,0,64) } finally { $stream.Dispose() }
            if ($ext -eq '.p00' -and $size -gt 26 -and $count -ge 8 -and
                [Text.Encoding]::ASCII.GetString($header,0,8) -eq "C64File`0") { return 'P00' }
            if ($ext -eq '.t64' -and $size -gt 64 -and $count -eq 64) {
                $version = [int]$header[32] + ([int]$header[33] * 256)
                if ($version -ge 256 -and $version -le 512) { return 'T64' }
            }
            if ($ext -eq '.crt' -and $size -gt 64 -and $count -eq 64) {
                $signature = [Text.Encoding]::ASCII.GetString($header,0,16)
                $length = ([int64]$header[16]*16777216)+([int]$header[17]*65536)+([int]$header[18]*256)+$header[19]
                $version = ([int]$header[20]*256)+$header[21]
                if ($signature -in @('C64 CARTRIDGE   ','C128 CARTRIDGE  ') -and $length -in @(32,64) -and $version -ge 256 -and $version -le 512) {
                    $mapper = ([int]$header[22]*256)+$header[23]
                    if ($signature.StartsWith('C128')) {
                        if ($mapper -in @(0,1)) { return 'C128 CRT, review' }; return $null
                    }
                    # G5 upstream crt_get_handler table (9c84d999).
                    if ($mapper -in @(0,1,2,3,4,5,7,8,10,15,16,17,18,19,20,21,23,32,43,45,46,51,53,57,74)) { return 'CRT' }
                    return $null
                }
            }
            return $null
        }
        default { return $null }
    }
}
function Get-ExistingHashes {
    $index = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($f in @(Get-CardFiles $games $false)) {
        try { $index[(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash] = $f.FullName }
        catch { throw "Cannot check existing Games file $($f.FullName). Copying stopped to avoid duplicate mistakes. $($_.Exception.Message)" }
    }
    if ($warnings.Count) { throw ($warnings -join "`n") }
    return ,$index
}
function Get-SafeDestination([string]$Relative, [string]$Hash) {
    $target = [IO.Path]::GetFullPath((Join-Path $games $Relative))
    if (-not (Test-InPath $target $games)) { throw 'Destination escaped Games.' }
    if (Test-Path -LiteralPath $target) {
        $folder = Split-Path -Parent $target
        $stem = [IO.Path]::GetFileNameWithoutExtension($target)
        $ext = [IO.Path]::GetExtension($target)
        $number = 0
        do {
            $suffix = if ($number) { " [$($Hash.Substring(0,12))-$number]" } else { " [$($Hash.Substring(0,12))]" }
            $target = Join-Path $folder ($stem + $suffix + $ext); $number++
        } while (Test-Path -LiteralPath $target)
    }
    return $target
}

if (-not $Copy) {
    if (Test-Path -LiteralPath $PlanPath) { throw "Plan already exists: $PlanPath. Choose another -PlanPath or rename the existing plan." }
    Write-Host 'Indexing existing Games files for duplicate checks...'
    $seen = Get-ExistingHashes
    $rows = New-Object 'System.Collections.Generic.List[object]'
    $candidates = @(Get-CardFiles $root $true | Sort-Object FullName)
    $n = 0
    foreach ($f in $candidates) {
        $n++; if (($n % 100) -eq 0) { Write-Progress -Activity 'Scanning SD card' -Status "$n / $($candidates.Count) files" -PercentComplete (100*$n/$candidates.Count) }
        $relative = $f.FullName.Substring($root.Length)
        try {
            $format = Get-Format $f
            if (-not $format) { continue }
            $hash = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
            $review = ($relative -split '[\\/]')[0] -in @('Demos','Docs','MultiLoad64') -or $format -like '*review*'
            $include = -not $review; $action = if ($review) { 'Review' } else { 'Copy' }; $duplicateOf = ''
            if ($seen.ContainsKey($hash)) { $include=$false; $action='Duplicate'; $duplicateOf=$seen[$hash] }
            elseif ($include) { $seen[$hash]=$f.FullName }
            $rows.Add([pscustomobject]@{Include=$include; Action=$action; Format=$format; RelativePath=$relative; Bytes=$f.Length; SHA256=$hash; Source=$f.FullName; DuplicateOf=$duplicateOf})
        } catch { $warnings.Add("Cannot inspect $($f.FullName): $($_.Exception.Message)") }
    }
    Write-Progress -Activity 'Scanning SD card' -Completed
    if (-not $rows.Count) { throw 'No candidates found. No SD card files were changed.' }
    $rows | Export-Csv -LiteralPath $PlanPath -NoTypeInformation -Encoding UTF8
    if ($warnings.Count) { $warnings | Set-Content -LiteralPath ($PlanPath+'.warnings.txt') -Encoding UTF8; Write-Warning 'Some paths could not be scanned. See the warnings file.' }
    $rows | Group-Object Action | Select-Object Name,Count | Format-Table | Out-Host
    Write-Host "Plan: $PlanPath"
    Write-Host 'Review Include TRUE/FALSE in the CSV. No SD files have been copied.'
    Write-Host 'Run this script again with -Copy and the same -CardRoot and -PlanPath to apply the plan.'
    return
}

if (-not (Test-Path -LiteralPath $PlanPath -PathType Leaf)) { throw "Missing plan: $PlanPath" }
$chosen = @(Import-Csv -LiteralPath $PlanPath | Where-Object { $_.Include -match '^(?i:true|1|yes)$' })
if (-not $chosen.Count) { throw 'No rows have Include=True.' }
$seen = Get-ExistingHashes
$results = New-Object 'System.Collections.Generic.List[object]'
foreach ($row in $chosen) {
    $target=''; $status='Error'; $message=''; $temp=''; $tempCreated=$false
    try {
        $source = [IO.Path]::GetFullPath($row.Source)
        if (-not (Test-InPath $source $root) -or (Test-InPath $source $games) -or (Test-Excluded $source)) { throw 'Source is outside the allowed scan area.' }
        $relative = $source.Substring($root.Length)
        if ($relative -ne $row.RelativePath) { throw 'Source/relative path mismatch.' }
        if (-not (Get-Format (Get-Item -LiteralPath $source))) { throw 'Source no longer passes format checks.' }
        $hash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
        if ($hash -ne $row.SHA256) { throw 'Source changed since the plan was created.' }
        if ($seen.ContainsKey($hash)) { $status='Duplicate'; $target=$seen[$hash] }
        else {
            $target = Get-SafeDestination $relative $hash
            $parent = Split-Path -Parent $target
            [void][IO.Directory]::CreateDirectory($parent)
            $temp = Join-Path $parent ('.kff-copy-'+[guid]::NewGuid().ToString('N')+'.tmp')
            $inputStream = [IO.File]::Open($source,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
            $outputStream=$null
            try {
                $outputStream=[IO.File]::Open($temp,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None); $tempCreated=$true
                $inputStream.CopyTo($outputStream)
            } finally { if ($outputStream) { $outputStream.Dispose() }; $inputStream.Dispose() }
            if ((Get-FileHash -LiteralPath $temp -Algorithm SHA256).Hash -ne $hash) { throw 'Copied content failed SHA256 verification.' }
            [IO.File]::Move($temp,$target) # No overwrite, even if a destination appeared during copying.
            $seen[$hash]=$target; $status='Copied'
        }
    } catch { $message=$_.Exception.Message; Write-Warning "$($row.Source): $message" }
    finally { if ($tempCreated -and (Test-Path -LiteralPath $temp)) { Remove-Item -LiteralPath $temp -Force } }
    $results.Add([pscustomobject]@{Status=$status; Source=$row.Source; Destination=$target; Message=$message})
}
$results | Export-Csv -LiteralPath ($PlanPath+'.results.csv') -NoTypeInformation -Encoding UTF8
$results | Group-Object Status | Select-Object Name,Count | Format-Table | Out-Host
Write-Host "Copy log: $PlanPath.results.csv"
if (@($results | Where-Object Status -eq 'Error').Count) { throw 'Some files were not copied. See the copy log. Existing files and originals were not overwritten or deleted.' }
