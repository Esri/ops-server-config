REM =====================================================================
REM Create ArcGIS Data
REM =====================================================================
set ops_ChkErrLevelFile=%~dp0..\..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

REM ---------------------------------------------------------------------
REM Create ArcGIS Data Store
REM ---------------------------------------------------------------------
echo.
echo %sectionBreak%
echo Create ArcGIS Data Store
echo.
echo --Create ArcGIS Data Store...
echo.
set execute="%AGSDATASTORE%tools\configuredatastore.bat" https://%ops_FQDN%:6443/arcgis/admin %ops_userName% %ops_passWord% %ops_agsDataStoreDIR%

echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%

echo Waiting 3 minutes before continuing...
PING 127.0.0.1 -n 180 > nul


 