REM =====================================================================
REM Check if .NET Framework 4.5 is installed
REM =====================================================================
REM According to the following web page:
REM http://msdn.microsoft.com/en-us/library/hh925568(v=vs.110).aspx
REM if the registery DWORD "Release" exists then .NET Framework 4.5 or
REM newer has been installed.

reg query "HKLM\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full" /v Release
set ops_CheckErrLvl=%ERRORLEVEL%

if "%ops_CheckErrLvl%"=="1" (
    echo.
    echo **********************************************************
    echo **  ERROR: Installation dependency has not been met.
    echo **         .NET Framework 4.5 is not installed.
    echo **
    echo **  Solution: Install .NET Framework 4.5; the installer can
    echo **         downloaded from http://microsoft.com
    echo **********************************************************
    echo.
)

