REM =====================================================================
REM Register Portal for ArcGIS with the Web Adpator for IIS
REM =====================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

echo.
echo %sectionBreak%
echo Register Portal for ArcGIS with the Web Adpator for IIS...
echo.

set execute=%ops_ConfWebAdaptorExePath% /m portal /w https://%ops_FQDN%/arcgis/webadaptor /g http://%ops_FQDN%:7080 ^
/u %ops_userName% /p %ops_passWord%

if exist %ops_ConfWebAdaptorExePath% (
    echo %execute%
    %execute%
    Call %ops_ChkErrLevelFile% %ERRORLEVEL%
    PING 127.0.0.1 -n 3 > nul
) else (
    echo **********************************************************
    echo **  ERROR:
    echo **  Could not register Portal for ArcGIS with the WebAdaptor.
    echo **  The executable '%ops_ConfWebAdaptorExePath%'
    echo **  does not exist.
    echo **  Exiting RegisteringAGSwithWebAdaptor.bat.
    echo **********************************************************
    echo.
)