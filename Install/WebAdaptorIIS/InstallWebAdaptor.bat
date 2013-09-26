REM =====================================================================
REM Install ArcGIS Web Adpator for IIS
REM =====================================================================
REM NOTE: Web Adaptor prerequisites and ArcGIS Server must be installed
REM       before install Web Adaptor.
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

REM ---------------------------------------------------------------------
REM Install ArcGIS Web Adaptor for IIS
REM ---------------------------------------------------------------------
echo.
echo %sectionBreak%
echo Install ArcGIS Web Adaptor for IIS
echo.
echo --Installing...
echo.
set execute=%ops_softwareRoot%\WebAdaptorIIS\setup.exe /qb ADDLOCAL=ALL
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 3 > nul