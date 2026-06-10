# ==============================================================================
# Módulo AtsUi.psm1
# Contiene la lógica visual de consola, constantes de colores y formateo.
# ==============================================================================

# --- PALETA DE COLORES ---
$global:colorFrame = "DarkYellow"
$global:colorBrand = "DarkGray"
$global:colorText = "White"
$global:colorHeader = "Gray"
$global:colorInfo = "DarkCyan"
$global:colorVersion = "Cyan"
$global:colorPath = "DarkGray"
$global:colorSuccess = "Green"
$global:colorWarning = "Yellow"
$global:colorError = "Red"
$global:colorProtected = "DarkGreen"

function Show-AtsHeader {
    param (
        [string]$Product = "ATS NX Custom Launcher"
    )
    Clear-Host
    Write-Host ""
    Write-Host ' █▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█' -ForegroundColor $global:colorFrame
    Write-Host ' █  ' -NoNewline -ForegroundColor $global:colorFrame
    Write-Host 'NX-CORE ' -NoNewline -ForegroundColor $global:colorText
    Write-Host ':: ' -NoNewline -ForegroundColor $global:colorFrame
    Write-Host "$Product" -NoNewline -ForegroundColor $global:colorFrame

    $pad = 62 - $Product.Length
    if ($pad -lt 0) { $pad = 0 }
    Write-Host (' ' * $pad) -NoNewline
    Write-Host '█' -ForegroundColor $global:colorFrame

    Write-Host ' █ ' -NoNewline -ForegroundColor $global:colorFrame
    Write-Host '▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀' -NoNewline -ForegroundColor $global:colorBrand
    Write-Host '                           ' -NoNewline
    Write-Host ' █' -ForegroundColor $global:colorFrame

    Write-Host ' █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█' -ForegroundColor $global:colorFrame
    Write-Host ''
    Write-Host '   ATS GLOBAL SPAIN' -ForegroundColor $global:colorHeader
    Write-Host '   --------------------------------------------------------------------------' -ForegroundColor $global:colorBrand
    Write-Host ''
}

function Wait-AtsKeyPress {
    if ($Host.Name -eq 'ConsoleHost') {
        Write-Host "`n   Presione cualquier tecla para continuar..." -ForegroundColor $global:colorInfo
        while ($Host.UI.RawUI.KeyAvailable) {
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown,IncludeKeyUp")
        }
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    } else {
        $null = Read-Host "`n   Presione ENTER para continuar"
    }
}

function Show-AtsSuccess {
    param ([string]$Message)
    Write-Host "   [+] $Message" -ForegroundColor $global:colorSuccess
}

function Show-AtsWarning {
    param ([string]$Message)
    Write-Host "   [!] $Message" -ForegroundColor $global:colorWarning
}

function Show-AtsError {
    param ([string]$Message)
    Write-Host "   [x] $Message" -ForegroundColor $global:colorError
}

function Show-AtsInfo {
    param ([string]$Message, [switch]$NoNewline)
    if ($NoNewline) {
        Write-Host "   [*] $Message" -NoNewline -ForegroundColor $global:colorInfo
    } else {
        Write-Host "   [*] $Message" -ForegroundColor $global:colorInfo
    }
}

Export-ModuleMember -Function * -Variable *
}

function Show-AtsInfo {
    param ([string]$Message, [switch]$NoNewline)
    if ($NoNewline) {
        Write-Host "   [*] $Message" -NoNewline -ForegroundColor $global:colorInfo
    } else {
        Write-Host "   [*] $Message" -ForegroundColor $global:colorInfo
    }
    Write-AtsTrace -Message $Message -Type "INFO"
}

Export-ModuleMember -Function * -Variable *
