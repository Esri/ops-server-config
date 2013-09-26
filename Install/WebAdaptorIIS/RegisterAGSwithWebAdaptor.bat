REM =====================================================================
REM Register ArcGIS Server with the Web Adpator for IIS
REM =====================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

REM Register site with the Web Adaptor
REM As of 2/15/2013, setting /a switch to true to work around
REM a know issue with registering a server with a portal.
echo.
echo %sectionBreak%
echo Register ArcGIS Server with the Web Adaptor for IIS...
echo.

set execute=%ops_ConfWebAdaptorExePath% /m server /w http://localhost/arcgis/webadaptor /g http://%ops_FQDN%:6080 ^
/u %ops_userName% /p %ops_passWord% /a true

if exist %ops_ConfWebAdaptorExePath% (
    echo %execute%
    %execute%
    Call %ops_ChkErrLevelFile% %ERRORLEVEL%
    PING 127.0.0.1 -n 3 > nul
) else (
    echo **********************************************************
    echo **  ERROR:
    echo **  Could not register ArcGIS Server with the WebAdaptor.
    echo **  The executable '%ops_ConfWebAdaptorExePath%'
    echo **  does not exist.
    echo **  Exiting RegisteringAGSwithWebAdaptor.bat.
    echo **********************************************************
    echo.
)