# ==============================================================================
# ConfigLoader.psm1
# ==============================================================================

function Get-GlobalConfig {
    param (
        [Parameter(Mandatory = $true)][string]$RootPath
    )
    $ConfigPath = Join-Path $RootPath "config\global.config"
    if (Test-Path $ConfigPath) {
        $Json = Get-Content $ConfigPath -Raw | ConvertFrom-Json
        return $Json
    }
    return $null
}

function Get-NxVersions {
    param (
        [Parameter(Mandatory = $true)][string]$RootPath
    )
    $VersionsDir = Join-Path $RootPath "config\versions"
    $Versions = @()
    if (Test-Path $VersionsDir) {
        $Files = Get-ChildItem -Path $VersionsDir -Filter "*.json" | Where-Object { $_.Name -ne "TEMPLATE.json" }
        foreach ($File in $Files) {
            $Versions += Get-Content $File.FullName -Raw | ConvertFrom-Json
        }
    }
    return $Versions
}

Export-ModuleMember -Function *
