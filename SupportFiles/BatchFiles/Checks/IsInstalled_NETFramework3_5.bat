REM =====================================================================
REM Check if .NET Framework 3.5 is installed
REM =====================================================================
REM See the following web page:
REM http://msdn.microsoft.com/en-us/library/hh925568(v=vs.110).aspx

reg query "HKLM\SOFTWARE\Microsoft\NET Framework Setup\NDP\v3.5" /v Version
set ops_CheckErrLvl=%ERRORLEVEL%

if "%ops_CheckErrLvl%"=="1" (
    echo.
    echo **********************************************************
    echo **  ERROR: Installation dependency has not been met.
    echo **         .NET Framework 3.5 is not installed.
    echo **
    echo **  Solution: Run the InstallIIS.bat which will "enable" this
    echo **         OS "feature".
    echo **********************************************************
    echo.
)

