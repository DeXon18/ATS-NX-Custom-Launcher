# ==============================================================================
# RegistryScanner.psm1
# ==============================================================================

function Get-NxExecutablePath {
    param (
        [string]$VersionName,
        [string]$OverridePath
    )
    
    # Si el config tiene un override explícito y el archivo existe, lo usamos.
    if (-not [string]::IsNullOrWhiteSpace($OverridePath) -and (Test-Path $OverridePath)) {
        return $OverridePath
    }

    # Extraer el número de la versión. Ej "NX2027" -> "2027" o "2007" (Siemens a veces usa la serie base)
    # Buscaremos iterativamente en el registro HKLM:\SOFTWARE\Siemens\NX
    $RegPath = "HKLM:\SOFTWARE\Siemens\NX"
    
    if (Test-Path $RegPath) {
        # Buscar subclaves (ej. 2007, 2412)
        $Subkeys = Get-ChildItem -Path $RegPath
        foreach ($Key in $Subkeys) {
            # Extraemos el valor del directorio de instalación (generalmente 'WNT_DIR' o similar, o la misma clave tiene un valor)
            # En nuevas versiones suele estar bajo $Key\WNT_DIR o similar.
            # Dependiendo de la estructura exacta, ajustaremos.
            
            # Buscando si la ruta existe:
            $InstallDir = (Get-ItemProperty -Path $Key.PSPath -Name "WNT_DIR" -ErrorAction SilentlyContinue).WNT_DIR
            if (-not $InstallDir) {
                # Alternativa en versiones viejas (Unigraphics Solutions)
                $InstallDir = (Get-ItemProperty -Path $Key.PSPath -Name "(default)" -ErrorAction SilentlyContinue)."(default)"
            }

            if ($InstallDir) {
                $ExePath = Join-Path $InstallDir "nxbin\ugraf.exe"
                # Si la versión dada coincide en el string o la ruta:
                if ($ExePath -match $VersionName -and (Test-Path $ExePath)) {
                    return $ExePath
                }
            }
        }
    }

    # Si no lo encontramos en el registro, probamos la ruta por defecto típica
    $DefaultPath = "C:\Program Files\Siemens\$VersionName\nxbin\ugraf.exe"
    if (Test-Path $DefaultPath) {
        return $DefaultPath
    }
    
    # Serie base (ej: NX2027 está dentro de la carpeta NX2007 a veces)
    $BaseSeries = $VersionName.Substring(0, 4) + "0" * ($VersionName.Length - 4) # fallback básico
    if ($BaseSeries -ne $VersionName) {
        $DefaultPathBase = "C:\Program Files\Siemens\$BaseSeries\nxbin\ugraf.exe"
        if (Test-Path $DefaultPathBase) {
            return $DefaultPathBase
        }
    }

    return $null
}

Export-ModuleMember -Function *
