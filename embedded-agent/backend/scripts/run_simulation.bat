@echo off
REM Batch script to run Proteus simulation and capture results
REM Usage: run_simulation.bat [proteus_path] [dsn_file] [output_json]

setlocal enabledelayedexpansion

REM Check arguments
if "%~1"=="" (
    echo Error: Missing Proteus path
    exit /b 1
)
if "%~2"=="" (
    echo Error: Missing DSN file path
    exit /b 1
)
if "%~3"=="" (
    echo Error: Missing output JSON path
    exit /b 1
)

set PROTEUS_PATH=%~1
set DSN_FILE=%~2
set OUTPUT_JSON=%~3

REM Check if Proteus executable exists
if not exist "%PROTEUS_PATH%" (
    echo Error: Proteus executable not found at %PROTEUS_PATH%
    exit /b 1
)

REM Check if DSN file exists
if not exist "%DSN_FILE%" (
    echo Error: DSN file not found at %DSN_FILE%
    exit /b 1
)

REM Create directory for output JSON if it doesn't exist
set OUTPUT_DIR=%~dp3
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM Run Proteus simulation
echo Running Proteus simulation...
start /wait "" "%PROTEUS_PATH%" /s "%DSN_FILE%" /d 10000 /exportresults "%OUTPUT_JSON%.raw"

REM Check if simulation completed successfully
if %ERRORLEVEL% neq 0 (
    echo Error: Proteus simulation failed with code %ERRORLEVEL%
    
    REM Create error JSON
    echo { > "%OUTPUT_JSON%"
    echo   "success": false, >> "%OUTPUT_JSON%"
    echo   "error": "Proteus simulation failed with code %ERRORLEVEL%", >> "%OUTPUT_JSON%"
    echo   "timestamp": "%date% %time%" >> "%OUTPUT_JSON%"
    echo } >> "%OUTPUT_JSON%"
    
    exit /b %ERRORLEVEL%
)

REM Convert raw results to JSON using helper script
python "%~dp0\parse_proteus_results.py" "%OUTPUT_JSON%.raw" "%OUTPUT_JSON%"

REM Check if conversion was successful
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to parse simulation results
    
    REM Create error JSON
    echo { > "%OUTPUT_JSON%"
    echo   "success": false, >> "%OUTPUT_JSON%"
    echo   "error": "Failed to parse simulation results", >> "%OUTPUT_JSON%"
    echo   "timestamp": "%date% %time%" >> "%OUTPUT_JSON%"
    echo } >> "%OUTPUT_JSON%"
    
    exit /b %ERRORLEVEL%
)

echo Simulation completed successfully.
exit /b 0
