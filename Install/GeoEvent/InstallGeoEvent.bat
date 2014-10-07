REM =====================================================================
REM Install ArcGIS GeoEvent Processor Extension for ArcGIS Server
REM =====================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

echo.
echo %sectionBreak%
echo Install ArcGIS GeoEvent Extension for ArcGIS Server

REM ---------------------------------------------------------------------
REM Install GeoEvent Processor Extension
REM ---------------------------------------------------------------------
echo.
echo.
echo --Installing GeoEvent Processor Extension...
echo.
echo Waiting 8 minutes before installing Geoevent...
PING 127.0.0.1 -n 480 > nul

set execute=msiexec /I %ops_softwareRoot%\ArcGISGeoEvent\SetupFiles\setup.msi PASSWORD=%ops_passWord% /qb
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
echo.
echo Giving GeoEvent 8 minutes to finish setting up all it's web services before
echo continuing with the Ops Server configuration...
PING 127.0.0.1 -n 480 > nul

REM ---------------------------------------------------------------------
REM Unset variables
REM ---------------------------------------------------------------------
set ops_ChkErrLevelFile=
set execute=

echo.
echo.
echo Finished installing GeoEvent Extension for ArcGIS Server.
echo.
echo.
