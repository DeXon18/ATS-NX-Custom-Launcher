# ==============================================================================
# EnvManager.psm1
# ==============================================================================

function Set-NxEnvironmentVars {
    param (
        [Parameter(Mandatory = $true)][string]$RootPath,
        [Parameter(Mandatory = $true)][string]$VersionName
    )

    $VersionPath = Join-Path $RootPath "versions\$VersionName"
    if (-not (Test-Path $VersionPath)) {
        throw "La carpeta de versión '$VersionPath' no existe."
    }

    # Definir mapeos (Ruta Relativa -> Variable NX)
    $Mappings = @{
        "cam"                     = "UGII_CAM_CONFIG"
        "apps"                    = "UGII_USER_DIR"
        "apps\startup"            = "UGII_TEMPLATE_DIR"
        "bitmaps"                 = "UGII_BITMAP_PATH"
        "templates\CAD"           = "NX_CLIENTE_CAD_TEMPLATE_PART_METRIC_DIR"
        "templates\CAM"           = "NX_CLIENTE_CAM_TEMPLATE_PART_METRIC_DIR"
        "libraries\machines"      = "UGII_CAM_LIBRARY_MACHINE_DATA_DIR"
        "libraries\postprocessor" = "NX_CLIENTE_CAM_POST_DIR"
        "libraries\tools"         = "UGII_CAM_LIBRARY_TOOL_DIR"
        "libraries\ug_library"    = "UGII_UG_LIBRARY_DIR"
        "libraries\feeds_speeds"  = "UGII_CAM_LIBRARY_FEEDS_SPEEDS_DIR"
        "libraries\device"        = "UGII_CAM_LIBRARY_DEVICE_DIR"
        "user_def_event"          = "UGII_CAM_USER_DEF_EVENT_DIR"
    }

    foreach ($Key in $Mappings.Keys) {
        $FullPath = Join-Path $VersionPath $Key
        if (Test-Path $FullPath) {
            # Verificar si hay archivos dentro (recursivo o no, por ahora comprobamos contenido)
            $HasFiles = $null -ne (Get-ChildItem -Path $FullPath -File -Recurse | Select-Object -First 1)
            if ($HasFiles) {
                # Mapear
                $VarName = $Mappings[$Key]

                # Excepciones
                if ($VarName -eq "UGII_CAM_CONFIG") {
                    $DatFile = Get-ChildItem -Path $FullPath -Filter "*.dat" | Select-Object -First 1
                    if ($DatFile) {
                        [Environment]::SetEnvironmentVariable($VarName, $DatFile.FullName, "Process")
                    }
                } else {
                    # Carpetas normales
                    $PathToSet = $FullPath + "\"
                    [Environment]::SetEnvironmentVariable($VarName, $PathToSet, "Process")
                }
            }
        }
    }
}

Export-ModuleMember -Function *
