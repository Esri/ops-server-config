REM =====================================================================
REM Set Overall Error Level Variable
REM =====================================================================
REM Used to set "Global" variable ops_OverallErrLvl storing error level.
REM Batch file should be called after running any of the batch files
REM in the SupportFiles\BatchFiles\Checks directory. If error code is
REM passed to batch file, set the "Global" variable = 1 indicating that
REM an error has occurred.
set ErrLvl=%1

REM Batch file compare operations from IF /?
rem EQU - equal
rem NEQ - not equal
rem LSS - less than
rem LEQ - less than or equal
rem GTR - greater than
rem GEQ - greater than or equal

if %ErrLvl% GTR 0 (
  set ops_OverallErrLvl=1
)