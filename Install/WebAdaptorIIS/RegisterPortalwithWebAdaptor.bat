REM =====================================================================
REM Register Portal for ArcGIS with the Web Adpator for IIS
REM =====================================================================

echo.
echo %sectionBreak%
echo Register Portal for ArcGIS with the Web Adpator for IIS...
echo.

if exist %ops_ConfWebAdaptorExePath% (
    %ops_ConfWebAdaptorExePath% /m portal /w https://%ops_FQDN%/arcgis/webadaptor/portal /g http://%ops_FQDN%:7080 ^
        /u %ops_userName% /p %ops_passWord%
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