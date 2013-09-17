REM =====================================================================
REM Install ArcGIS Web Adpator for IIS
REM =====================================================================
REM NOTE: Web Adaptor prerequisites and ArcGIS Server must be installed
REM       before install Web Adaptor.

REM ---------------------------------------------------------------------
REM Install ArcGIS Web Adaptor for IIS
REM ---------------------------------------------------------------------
echo.
echo %sectionBreak%
echo Install ArcGIS Web Adaptor for IIS
echo.
echo --Installing...
%ops_softwareRoot%\WebAdaptorIIS\setup.exe /qb ADDLOCAL=ALL
PING 127.0.0.1 -n 3 > nul