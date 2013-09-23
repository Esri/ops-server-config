REM =====================================================================
REM Check DOS Error Level code
REM =====================================================================
set ops_PassedErrorLevel=%1

if "%ops_PassedErrorLevel%"=="1" (
    echo.
    echo **********************************************************
    echo **  ERROR: error encountered. Pausing script execution.
    echo **
    echo **  Close command prompt to stop script execution.
    echo **  Press any key to continue with script execution.
    echo **********************************************************
    echo.
    pause
)
