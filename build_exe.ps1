$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$cmd = "py"
$has_py = Get-Command py -ErrorAction SilentlyContinue
if (-not $has_py) {
    $cmd = "python"
    $has_python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $has_python) {
        Write-Error 'Neither Python launcher (py) nor python command was found.'
        exit 1
    }
}

& $cmd -m pip install --upgrade pyinstaller
& $cmd -m PyInstaller "SmartChess.spec" --distpath . --workpath .build
Write-Host 'Executable build complete. Look for SmartChess.exe in the project folder.'
