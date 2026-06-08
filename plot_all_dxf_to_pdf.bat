@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Folder that contains exported DXF files.
set "DXF_DIR=%~dp0output"

rem Folder where PDF files will be written.
set "PDF_DIR=%DXF_DIR%\pdf"

rem Folder for temporary AutoCAD script files.
set "SCRIPT_DIR=%DXF_DIR%\plot_scripts"

rem Folder for temporary DXF copies used only for plotting.
set "WORK_DIR=%TEMP%\SectionDrawingGeneratorPlot"

rem AutoCAD page setup name saved inside the template/DXF.
set "PAGE_SETUP=Setup1"

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

if not exist "%PDF_DIR%" mkdir "%PDF_DIR%"
if not exist "%SCRIPT_DIR%" mkdir "%SCRIPT_DIR%"
if not exist "%WORK_DIR%" mkdir "%WORK_DIR%"

echo Plotting DXF files from:
echo %DXF_DIR%
echo.
echo PDF output folder:
echo %PDF_DIR%
echo.

for %%F in ("%DXF_DIR%\*.dxf") do (
    set "DXF_FILE=%%~fF"
    set "BASE_NAME=%%~nF"
    set "PLOT_DXF_FILE=%WORK_DIR%\%%~nF_plotcopy.dxf"
    set "PDF_FILE=%PDF_DIR%\%%~nF.pdf"
    set "SCRIPT_FILE=%SCRIPT_DIR%\%%~nF_plot.scr"

    echo Creating plot script for %%~nxF

    copy /y "!DXF_FILE!" "!PLOT_DXF_FILE!" >nul
    if errorlevel 1 (
        echo ERROR: Could not copy %%~nxF to temporary plot folder.
        echo Close the DXF if it is open in AutoCAD/TrueView and try again.
        echo.
    ) else (
        > "!SCRIPT_FILE!" echo _.-PLOT
        >>"!SCRIPT_FILE!" echo N
        >>"!SCRIPT_FILE!" echo.
        >>"!SCRIPT_FILE!" echo %PAGE_SETUP%
        >>"!SCRIPT_FILE!" echo.
        >>"!SCRIPT_FILE!" echo "!PDF_FILE!"
        rem Save changes to page setup: press Enter to accept default N.
        >>"!SCRIPT_FILE!" echo.
        rem Proceed with plot: press Enter to accept default Y.
        >>"!SCRIPT_FILE!" echo.
        >>"!SCRIPT_FILE!" echo _.QUIT
        rem Really discard changes: must answer Y, otherwise AutoCAD asks save-as questions.
        >>"!SCRIPT_FILE!" echo Y
        >>"!SCRIPT_FILE!" echo.

        if exist "!PDF_FILE!" del /q "!PDF_FILE!"

        echo Plotting %%~nxF to PDF...
        "%ACCORE%" /i "!PLOT_DXF_FILE!" /s "!SCRIPT_FILE!"

        if exist "!PDF_FILE!" (
            echo OK: !PDF_FILE!
        ) else (
            echo ERROR: PDF was not created for %%~nxF
        )
    )
    echo.
)

echo Done.
pause
