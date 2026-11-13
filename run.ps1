# NEBULA ASCII STUDIO — PowerShell Launcher
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "NEBULA ASCII STUDIO — Advanced Image-to-ASCII Engine"

Set-Location $PSScriptRoot

if (Get-Command py -ErrorAction SilentlyContinue) {
    py main.py $args
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python main.py $args
} else {
    Write-Error "Python was not found. Please install Python 3.11+ and ensure it is in your PATH."
}
