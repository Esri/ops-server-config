REM =====================================================================
REM Install ArcGIS Data Store Software
REM =====================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

REM ---------------------------------------------------------------------
REM Install ArcGIS Data Store
REM ---------------------------------------------------------------------
echo.
echo %sectionBreak%
echo Install ArcGIS Data Store
echo.
echo --Installing ArcGIS Data Store...
echo.
REM Issue with Data Store, running windows service by any other account except for LOCALSYSTEM is not supported yet.
REM set execute=%ops_softwareRoot%\ArcGISDataStore\setup.exe /qb USER_NAME=%ops_agsServiceAccount% PASSWORD=%ops_passWord%
set execute=%ops_softwareRoot%\ArcGISDataStore\setup.exe /qb

echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%

set AGSDATASTORE=C:\Program Files\ArcGIS\DataStore\

echo Waiting 3 minutes before continuing...
PING 127.0.0.1 -n 180 > nul


 