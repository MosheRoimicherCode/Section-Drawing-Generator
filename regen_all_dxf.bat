@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Folder that contains exported DXF files.
set "DXF_DIR=%~dp0output"

rem Folder for temporary AutoCAD script files.
set "SCRIPT_DIR=%DXF_DIR%\regen_scripts"

rem AutoCAD Core Console executable.
set "ACCORE=C:\Program Files\Autodesk\AutoCAD 2025\accoreconsole.exe"

if not exist "%ACCORE%" (
    echo ERROR: accoreconsole.exe was not found:
    echo %ACCORE%
    echo Edit this BAT file and update the ACCORE path.
    exit /b 1
)

if not exist "%DXF_DIR%" (
    echo ERROR: DXF folder was not found:
    echo %DXF_DIR%
    exit /b 1
)

if not exist "%SCRIPT_DIR%" mkdir "%SCRIPT_DIR%"

echo Running REGENALL on DXF files from:
echo %DXF_DIR%
echo.

for %%F in ("%DXF_DIR%\*.dxf") do (
    set "DXF_FILE=%%~fF"
    set "SCRIPT_FILE=%SCRIPT_DIR%\%%~nF_regen.scr"

    echo Creating regen script for %%~nxF

    > "!SCRIPT_FILE!" echo _.REGENALL
    >>"!SCRIPT_FILE!" echo _.QSAVE
    >>"!SCRIPT_FILE!" echo _.QUIT
    rem If AutoCAD asks whether to discard changes, use Enter/default after QSAVE.
    >>"!SCRIPT_FILE!" echo.

    echo Regenerating %%~nxF...
    "%ACCORE%" /i "!DXF_FILE!" /s "!SCRIPT_FILE!"
    echo.
)

echo Done.
pause
