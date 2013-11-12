REM =====================================================================
REM Check if .NET Framework 3.5 is installed
REM =====================================================================
REM See the following web page:
REM http://msdn.microsoft.com/en-us/library/hh925568(v=vs.110).aspx
set serviceName=W3SVC
sc query %serviceName% | find "RUNNING"
set ops_CheckErrLvl=%ERRORLEVEL%

if "%ops_CheckErrLvl%"=="1" (
    echo.
    echo **********************************************************
    echo **  ERROR: Installation dependency has not been met.
    echo **         IIS is not enabled or the IIS service
    echo **         "World Wide Web Publishing Service" ^(%serviceName%^)
    echo **         is not running.
    echo **
    echo **  Solution:
    echo **         - If IIS is not installed run the InstallIIS.bat
    echo **           which will "enable" this OS "role".
    echo **         - If IIS is installed, but the windows service is
    echo **           not running, start the windows service.
    echo **********************************************************
    echo.
)

