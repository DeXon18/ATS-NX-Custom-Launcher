# ==============================================================================
# Start-NXLauncher.ps1
# Script principal del lanzador.
# ==============================================================================
$ErrorActionPreference = "Stop"

$CorePath = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ModulesPath = Join-Path $CorePath "modules"

Import-Module (Join-Path $ModulesPath "AtsUi.psm1") -Force
Import-Module (Join-Path $ModulesPath "ConfigLoader.psm1") -Force
Import-Module (Join-Path $ModulesPath "EnvManager.psm1") -Force
Import-Module (Join-Path $ModulesPath "RegistryScanner.psm1") -Force

try {
    Show-AtsHeader -Product "ATS NX Custom Launcher"

    $RootPath = Split-Path -Parent $CorePath
    $GlobalConfigPath = Join-Path $RootPath "config\global.config"

    # 1. Configuración de Red Base
    $GlobalConfig = Get-GlobalConfig -RootPath $RootPath
    if ($null -eq $GlobalConfig) {
        $GlobalConfig = [PSCustomObject]@{ IsNetworkSetup = $false; SelectedVersion = "" }
    }

    # 2. Cargar Versiones Disponibles
    $Versions = Get-NxVersions -RootPath $RootPath
    if ($Versions.Count -eq 0) {
        Show-AtsError "No se encontraron configuraciones en 'config\versions'."
        Wait-AtsKeyPress
        exit
    }

    # 3. Selección de Versión
    $SelectedConfig = $null

    if ($GlobalConfig.IsNetworkSetup -and -not [string]::IsNullOrWhiteSpace($GlobalConfig.SelectedVersion)) {
        # Si ya está configurado para red, tomar el por defecto
        $SelectedConfig = $Versions | Where-Object { $_.VersionName -eq $GlobalConfig.SelectedVersion }
        if ($null -eq $SelectedConfig) {
            Show-AtsWarning "La versión predeterminada '$($GlobalConfig.SelectedVersion)' no se encontró. Seleccione una manualmente."
            $GlobalConfig.IsNetworkSetup = $false
        }
    }

    if (-not $GlobalConfig.IsNetworkSetup) {
        if ($Versions.Count -eq 1) {
            $SelectedConfig = $Versions[0]
            Show-AtsInfo "Única versión detectada: $($SelectedConfig.VersionName)"
        } else {
            # Menú simple
            Write-Host "   Versiones Disponibles:" -ForegroundColor $global:colorHeader
            for ($i = 0; $i -lt $Versions.Count; $i++) {
                Write-Host "   [$($i + 1)] $($Versions[$i].VersionName) - $($Versions[$i].Description)" -ForegroundColor $global:colorText
            }
            Write-Host ""
            $Choice = Read-Host "   Seleccione una versión (1-$($Versions.Count))"
            $idx = [int]$Choice - 1
            if ($idx -ge 0 -and $idx -lt $Versions.Count) {
                $SelectedConfig = $Versions[$idx]
            } else {
                Show-AtsError "Selección no válida."
                Wait-AtsKeyPress
                exit
            }

            # Preguntar si guardar como predeterminado (Red)
            $Save = Read-Host "   ¿Desea guardar esta selección para todos los equipos en la red? (s/n)"
            if ($Save -eq 's' -or $Save -eq 'S') {
                $GlobalConfig.IsNetworkSetup = $true
                $GlobalConfig.SelectedVersion = $SelectedConfig.VersionName
                $GlobalConfig | ConvertTo-Json -Depth 3 | Set-Content $GlobalConfigPath
                Show-AtsSuccess "Configuración global guardada en $GlobalConfigPath"
            }
        }
    }

    # 4. Detectar NX
    Show-AtsInfo "Buscando ejecutable de NX para $($SelectedConfig.VersionName)..."
    $OverridePath = $SelectedConfig.NX_Exe_Path_Override
    $NxExe = Get-NxExecutablePath -VersionName $SelectedConfig.VersionName -OverridePath $OverridePath

    if (-not $NxExe -or -not (Test-Path $NxExe)) {
        Show-AtsError "No se encontró ugraf.exe para la versión $($SelectedConfig.VersionName)."
        Show-AtsInfo "Revise el Registro de Windows o especifique 'NX_Exe_Path_Override' en el archivo config."
        Wait-AtsKeyPress
        exit
    }
    Show-AtsSuccess "Encontrado: $NxExe"

    # 5. Mapear Variables de Entorno
    Show-AtsInfo "Inyectando variables de entorno desde la plantilla local..."
    Set-NxEnvironmentVars -RootPath $RootPath -VersionName $SelectedConfig.VersionName
    Show-AtsSuccess "Variables inyectadas en memoria."

    # 6. Ejecutar NX
    Show-AtsInfo "Iniciando Siemens NX..."
    Start-Process -FilePath $NxExe -WorkingDirectory $RootPath
    
    Show-AtsSuccess "NX iniciado correctamente."
    Start-Sleep -Seconds 3
}
catch {
    Show-AtsError "Error fatal: $_"
    Wait-AtsKeyPress
}
