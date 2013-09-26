REM =====================================================================
REM Check DOS Error Level code
REM =====================================================================
set ops_ErrLvl=%1
set ops_ProcessType=%2

REM Batch file compare operations from IF /?
rem EQU - equal
rem NEQ - not equal
rem LSS - less than
rem LEQ - less than or equal
rem GTR - greater than
rem GEQ - greater than or equal
    
if "%ops_ProcessType%"=="ROBOCOPY" (
    REM See http://support.microsoft.com/kb/954404 for robocopy exit codes
    if %ops_ErrLvl% GEQ 8 goto ERROR
) else (
    if %ops_ErrLvl% NEQ 0 goto ERROR
)
goto EOF

:ERROR
echo.
echo **********************************************************
echo **  ERROR: error encountered. ErrorLevel code: %ops_ErrLvl%
echo **  Pausing script execution.
echo **
echo **  Close command prompt to stop script execution.
echo **  Press any key to continue with script execution.
echo **********************************************************
echo.
pause

:EOF