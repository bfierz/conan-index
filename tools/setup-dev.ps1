<#
.SYNOPSIS
    Sets up an isolated environment for developing the recipes in this repository.

.DESCRIPTION
    - Creates a Python virtual environment in .venv and installs the Conan version
      pinned in requirements.txt (plus requirements-dev.txt).
    - Uses the Conan home in .conan2 (selected by .conanrc), so packages, profiles
      and remotes stay inside the repository and the user-wide ~/.conan2 is untouched.
    - Detects a default profile on first run.
    - Activates the environment in the current shell when dot-sourced.

    Run it again after changing requirements.txt; it is safe to rerun.

.EXAMPLE
    . .\tools\setup-dev.ps1           # set up and activate
.EXAMPLE
    . .\tools\setup-dev.ps1 -Reset    # wipe .venv and .conan2 first
#>
param(
    # Delete the virtual environment and the local Conan home before setting up
    [switch]$Reset,
    # Python interpreter used to create the virtual environment
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".venv"
$conanHome = Join-Path $root ".conan2"

if ($Reset) {
    foreach ($dir in @($venv, $conanHome)) {
        if (Test-Path $dir) {
            Write-Host "Removing $dir"
            Remove-Item -Recurse -Force $dir
        }
    }
}

if ($IsLinux -or $IsMacOS) {
    $venvPython = Join-Path $venv "bin/python"
    $activate = Join-Path $venv "bin/Activate.ps1"
} else {
    $venvPython = Join-Path $venv "Scripts\python.exe"
    $activate = Join-Path $venv "Scripts\Activate.ps1"
}

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment in $venv"
    & $Python -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw "Creating the virtual environment failed" }
}

& $venvPython -m pip install --quiet --disable-pip-version-check --upgrade pip
& $venvPython -m pip install --quiet --disable-pip-version-check -r (Join-Path $root "requirements-dev.txt")
if ($LASTEXITCODE -ne 0) { throw "Installing the requirements failed" }

# Activate before running conan, so the venv's conan is used and not one on PATH.
# CONAN_HOME is set explicitly as well, so conan uses the local home even when
# it is run from outside the repository while this shell is active.
. $activate
$env:CONAN_HOME = $conanHome

$defaultProfile = Join-Path $conanHome "profiles/default"
if (-not (Test-Path $defaultProfile)) {
    Write-Host "Detecting default Conan profile"
    conan profile detect
    if ($LASTEXITCODE -ne 0) { throw "Detecting the Conan profile failed" }
    # Match the C++ standard the CI builds with by default
    (Get-Content $defaultProfile) -replace '^compiler\.cppstd=.*', 'compiler.cppstd=20' |
        Set-Content -Encoding ascii $defaultProfile
}

# Make any other Conan (e.g. a user-wide install on PATH) refuse to work on this
# Conan home, instead of silently migrating it to its own version.
$pinned = (Select-String -Path (Join-Path $root "requirements.txt") -Pattern '^conan==(\S+)').Matches[0].Groups[1].Value
$globalConf = Join-Path $conanHome "global.conf"
$guard = "core:required_conan_version=$pinned"
$lines = @(Get-Content $globalConf | Where-Object { $_ -notmatch '^core:required_conan_version' }) + $guard
Set-Content -Encoding ascii -Path $globalConf -Value $lines

Write-Host ""
Write-Host "$(conan --version) with home $(conan config home)"
if ($MyInvocation.InvocationName -ne ".") {
    Write-Host "Run '. .\tools\setup-dev.ps1' (dot-sourced) to keep the environment active in this shell." -ForegroundColor Yellow
}
