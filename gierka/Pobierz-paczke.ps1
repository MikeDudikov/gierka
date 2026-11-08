param([string]$Katalog = (Join-Path (Get-Location) 'AncientConquest-paczka'))
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$expected = 'fa850d9df733e7ab8f0e295377ebbe2a255a0a25cbae1767e5372fdbc5a95060'
$manifestUrl = 'https://raw.githubusercontent.com/MikeDudikov/gierka/gierka/gierka/manifest.json'
$manifest = (Invoke-WebRequest -UseBasicParsing -Uri $manifestUrl).Content | ConvertFrom-Json
if ($manifest.sha256 -ne $expected) { throw 'Manifest nie dotyczy oczekiwanej paczki.' }
New-Item -ItemType Directory -Path $Katalog -Force | Out-Null
$Katalog = (Resolve-Path $Katalog).Path
$archive = Join-Path $Katalog $manifest.archive
if ([IO.Path]::GetFileName($manifest.archive) -ne $manifest.archive) { throw 'Nieprawidlowa nazwa archiwum.' }
if (Test-Path -LiteralPath $archive) {
    if ((Get-Item -LiteralPath $archive).Length -eq [long]$manifest.bytes -and (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -eq $expected) {
        Write-Host "Gotowa paczka juz istnieje: $archive"
        exit 0
    }
    throw 'Istniejace archiwum ma inna sume; przenies je przed ponowieniem.'
}
$parts = @()
foreach ($part in $manifest.parts) {
    if ([IO.Path]::GetFileName($part.name) -ne $part.name) { throw 'Nieprawidlowa nazwa czesci.' }
    $target = Join-Path $Katalog $part.name
    $valid = $false
    if (Test-Path -LiteralPath $target) {
        $valid = ((Get-Item -LiteralPath $target).Length -eq [long]$part.bytes -and (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -eq $part.sha256)
        if (-not $valid) { throw "Istniejacy plik ma inna sume: $target" }
    }
    if (-not $valid) {
        $temporary = $target + '.partial'
        Write-Host "Pobieranie: $($part.name)"
        if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
            & curl.exe --fail --location --retry 3 --continue-at - --output $temporary $part.url
            if ($LASTEXITCODE -ne 0) { throw 'Pobieranie przerwane; uruchom skrypt ponownie, aby wznowic.' }
        } else {
            Invoke-WebRequest -UseBasicParsing -Uri $part.url -OutFile $temporary
        }
        if ((Get-Item -LiteralPath $temporary).Length -ne [long]$part.bytes -or (Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash.ToLowerInvariant() -ne $part.sha256) {
            throw "Niezgodna suma czesci: $($part.name)"
        }
        Move-Item -LiteralPath $temporary -Destination $target
    } else { Write-Host "Juz pobrano: $($part.name)" }
    $parts += $target
}
Write-Host 'Scalanie paczki...'
$assembling = $archive + '.assembling'
$output = [IO.File]::Open($assembling, [IO.FileMode]::Create, [IO.FileAccess]::Write)
try {
    foreach ($part in $parts) {
        $inputFile = [IO.File]::OpenRead($part)
        try { $inputFile.CopyTo($output, 8388608) } finally { $inputFile.Dispose() }
    }
} finally { $output.Dispose() }
if ((Get-Item -LiteralPath $assembling).Length -ne [long]$manifest.bytes -or (Get-FileHash -LiteralPath $assembling -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
    throw 'Koncowa suma archiwum jest niezgodna.'
}
Move-Item -LiteralPath $assembling -Destination $archive
Set-Content -LiteralPath ($archive + '.sha256') -Encoding Ascii -Value ($expected + '  ' + $manifest.archive)
Write-Host "Gotowe - suma SHA256 zgodna: $archive"
