$ErrorActionPreference='Stop'
$script=Join-Path (Split-Path -Parent $PSScriptRoot) 'tools/Copy-Kff2Games.ps1'
$base=Join-Path ([IO.Path]::GetTempPath()) ('kff-copy-test-'+[guid]::NewGuid().ToString('N'))
$card=Join-Path $base card
$plan=Join-Path $base plan.csv
[void][IO.Directory]::CreateDirectory($card)
function Put([string]$Relative,[byte[]]$Bytes) {
 $f=Join-Path $card $Relative;[void][IO.Directory]::CreateDirectory((Split-Path -Parent $f));[IO.File]::WriteAllBytes($f,$Bytes)
}
function Assert($Condition,$Message) {if(-not $Condition){throw $Message}}
try {
 Put 'Games/Existing.prg' ([byte[]](1,8,10,11))
 Put 'Games/Homebrew/Already.prg' ([byte[]](1,8,20,21))
 foreach($dir in 'Tools','Utilities','Favourites','Homebrew','!!Firmware') {Put "$dir/Excluded.prg" ([byte[]](1,8,100,101))}
 Put 'AlternativeFormats/dupe.prg' ([byte[]](1,8,10,11))
 Put 'AlternativeFormats/homebrew-dupe.prg' ([byte[]](1,8,20,21))
 Put 'AlternativeFormats/New.prg' ([byte[]](1,8,30,31))
 Put 'Extras/OtherName.prg' ([byte[]](1,8,30,31))
 Put 'Extras/Standalone [demo].prg' ([byte[]](1,8,40,41))
 Put 'Demos/NeedsReview.prg' ([byte[]](1,8,50,51))
 Put 'MultiLoad64/NeedsReview.prg' ([byte[]](1,8,60,61))
 Put 'Extras/Broken.d64' ([byte[]](1,2,3))
 Put 'Extras/NotAGame.txt' ([byte[]](1,8,70,71))
 Put 'Extras/Empty.prg' ([byte[]](1,2))
 Put 'Extras/UnknownFile' ([byte[]](1,8,80,81))
 # Format-header/mapper filters use G5's supported image families.
 $crt=New-Object byte[] 128
 [Array]::Copy([Text.Encoding]::ASCII.GetBytes('C64 CARTRIDGE   '),$crt,16)
 $crt[19]=64; $crt[20]=1; $crt[23]=32
 Put 'Extras/Valid.crt' $crt
 $crt[23]=255; Put 'Extras/Unsupported.crt' $crt
 $c128=New-Object byte[] 128
 [Array]::Copy([Text.Encoding]::ASCII.GetBytes('C128 CARTRIDGE  '),$c128,16)
 $c128[19]=64; $c128[20]=1; Put 'Extras/C128.crt' $c128
 Put 'Extras/Valid.d64' (New-Object byte[] 174848)
 $p00=New-Object byte[] 28
 [Array]::Copy([Text.Encoding]::ASCII.GetBytes("C64File`0"),$p00,8)
 $p00[26]=1; $p00[27]=8; Put 'Extras/Valid.p00' $p00
 $t64=New-Object byte[] 96; $t64[33]=1; Put 'Extras/Valid.t64' $t64
 # Existing different-content destination must remain intact and trigger a new name.
 Put 'Games/Extras/Standalone [demo].prg' ([byte[]](1,8,90,91))
 & $script -CardRoot $card -PlanPath $plan
 $rows=@(Import-Csv $plan)
 Assert ($rows.Count -eq 13) "Candidate count $($rows.Count), expected 13"
 Assert (@($rows|Where-Object Source -match '[\\/](Tools|Utilities|Favourites|Homebrew|!!Firmware)[\\/]').Count -eq 0) 'Excluded source was scanned'
 Assert (@($rows|Where-Object Action -eq Duplicate).Count -eq 3) 'Missing content duplicates'
 Assert (@($rows|Where-Object Include -eq True).Count -eq 6) 'Wrong automatic selections'
 Assert (-not (Test-Path (Join-Path $card 'Games/AlternativeFormats/New.prg'))) 'Plan mode copied a file'
 & $script -CardRoot $card -PlanPath $plan -Copy
 $result=@(Import-Csv ($plan+'.results.csv'))
 Assert (@($result|Where-Object Status -eq Copied).Count -eq 6) 'Copy count mismatch'
 Assert (([IO.File]::ReadAllBytes((Join-Path $card 'Games/Extras/Standalone [demo].prg')))[2] -eq 90) 'Existing destination overwritten'
 Assert (@(Get-ChildItem -LiteralPath (Join-Path $card 'Games/Extras') -File | Where-Object Name -like 'Standalone*').Count -eq 2) 'Filename collision not handled'
 Assert (Test-Path -LiteralPath (Join-Path $card 'Extras/Standalone [demo].prg')) 'Source removed'
 & $script -CardRoot $card -PlanPath $plan -Copy
 $result=@(Import-Csv ($plan+'.results.csv'))
 Assert (@($result|Where-Object Status -eq Duplicate).Count -eq 6) 'Second run created duplicates'
 Assert (@(Get-ChildItem $card -Recurse -Filter '*.tmp').Count -eq 0) 'Temporary files left behind'
 # Source mutation after planning is refused, and originals remain intact.
 Put 'AlternativeFormats/New.prg' ([byte[]](1,8,222,223))
 $blocked=$false
 try {& $script -CardRoot $card -PlanPath $plan -Copy} catch {$blocked=$true}
 Assert $blocked 'Changed source accepted'
 Write-Host 'PASS: format headers/mapper filters, exclusions, full Games duplicate index, cross-source hashes, review, mirrored folders, literal names, collision protection, repeat runs, changed-source refusal'
} finally {Remove-Item -LiteralPath $base -Recurse -Force}
