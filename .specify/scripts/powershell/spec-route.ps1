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
        return Join-Path (Join-Path $SpecsDir 'live') $BranchName
    }

    $segments = Get-SpecRadixSegments -Number $Number.Value
    $route = $segments -join [System.IO.Path]::DirectorySeparatorChar
    return Join-Path (Join-Path $SpecsDir 'numbered') (Join-Path $route $BranchName)
}
