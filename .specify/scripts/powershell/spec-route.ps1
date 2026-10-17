#!/usr/bin/env pwsh
# Resolve feature directories under the bounded specs taxonomy.

function Get-SpecRadixSegments {
    param(
        [Parameter(Mandatory = $true)][long]$Number,
        [int]$Width = 8
    )

    if ($Number -lt 0) {
        throw "Feature number must not be negative."
    }
    if ($Width -lt 1) {
        throw "Route width must be positive."
    }

    $base = 5
    $limit = [long][Math]::Pow($base, $Width)
    if ($Number -ge $limit) {
        throw "Feature number $Number exceeds the route width."
    }

    $remaining = $Number
    $digits = New-Object 'System.Collections.Generic.List[string]'
    for ($position = $Width - 1; $position -ge 0; $position--) {
        $place = [long][Math]::Pow($base, $position)
        $digit = [long][Math]::Floor($remaining / $place)
        $digits.Add([string]$digit)
        $remaining -= $digit * $place
    }
    return $digits.ToArray()
}

function Resolve-SpecFeaturePath {
    param(
        [Parameter(Mandatory = $true)][string]$SpecsDir,
        [Parameter(Mandatory = $true)][string]$BranchName,
        [Nullable[long]]$Number,
        [switch]$Timestamp
    )

    if ($Timestamp -or $null -eq $Number) {
        $seconds = Get-SpecTimestampSeconds -Name $BranchName
        $segments = Get-SpecRadixSegments -Number $seconds -Width 17
        $route = $segments -join [System.IO.Path]::DirectorySeparatorChar
        return Join-Path (Join-Path $SpecsDir 'live') (Join-Path $route $BranchName)
    }

    $segments = Get-SpecRadixSegments -Number $Number
    $route = $segments -join [System.IO.Path]::DirectorySeparatorChar
    return Join-Path (Join-Path $SpecsDir 'numbered') (Join-Path $route $BranchName)
}

function Get-SpecTimestampSeconds {
    <#
    .SYNOPSIS
    Validate a timestamp label before assigning its stable UTC grouping route.
    #>
    param([Parameter(Mandatory = $true)][string]$Name)
    if ($Name -cnotmatch '^[0-9]{8}-[0-9]{6}-[a-z0-9]+(?:-[a-z0-9]+)*$') {
        throw "Invalid timestamp feature name: $Name"
    }
    $label = $Name.Substring(0, 15)
    $styles = [Globalization.DateTimeStyles]::AssumeUniversal -bor [Globalization.DateTimeStyles]::AdjustToUniversal
    $instant = [DateTimeOffset]::ParseExact($label, 'yyyyMMdd-HHmmss', [Globalization.CultureInfo]::InvariantCulture, $styles)
    $seconds = $instant.ToUnixTimeSeconds()
    if ($seconds -lt 0) {
        throw "Timestamp feature must be dated 1970 or later: $Name"
    }
    return $seconds
}

function Assert-SpecFeatureDestination {
    <#
    .SYNOPSIS
    Check all parents before allocation so overflow cannot leave a partial record.
    #>
    param([string]$SpecsDir, [string]$FeatureDir)
    $root = [IO.Path]::GetFullPath($SpecsDir).TrimEnd([IO.Path]::DirectorySeparatorChar)
    $child = [IO.Path]::GetFullPath($FeatureDir)
    if (-not $child.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Feature destination is outside the specs root: $FeatureDir. Examined 0 parents."
    }
    $examined = 0
    while ($child -ne $root) {
        $parent = Split-Path -Parent $child
        $examined++
        $count = Get-SpecDirectoryCount -Path $parent
        if ($parent -ne $root -and -not (Test-Path -LiteralPath $child) -and $count -ge 5) {
            throw "Feature parent exceeds five children: $parent ($count existing). Examined $examined parents."
        }
        $child = $parent
    }
    Get-SpecDirectoryCount -Path $FeatureDir -AllowFeature | Out-Null
}

function Get-SpecDirectoryCount {
    <#
    .SYNOPSIS
    Count an existing directory only after validating its type and ownership boundary.
    #>
    param([string]$Path, [switch]$AllowFeature)
    if (-not (Test-Path -LiteralPath $Path)) {
        return 0
    }
    $entry = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    if (-not $entry.PSIsContainer -or ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Unsafe feature directory: $Path. Examined 1 directory."
    }
    if (-not $AllowFeature -and (Test-Path -LiteralPath (Join-Path $Path 'spec.md'))) {
        throw "Feature parent is another feature: $Path. Examined 1 directory."
    }
    return @(Get-ChildItem -LiteralPath $Path -Force -ErrorAction Stop).Count
}
