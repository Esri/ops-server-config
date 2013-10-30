REM =====================================================================
REM Install ArcGIS GeoEvent Processor Extension for ArcGIS Server
REM =====================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

set ops_winServicename=ArcGISGeoEventProcessor

echo.
echo %sectionBreak%
echo Install ArcGIS GeoEvent Processor Extension for ArcGIS Server

REM ---------------------------------------------------------------------
REM Install GeoEvent Processor Extension
REM ---------------------------------------------------------------------
echo.
echo.
echo --Installing GeoEvent Processor Extension...
echo.
set execute=msiexec /I %ops_softwareRoot%\GeoEvent\setup.msi PASSWORD=%ops_passWord% /qb
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
echo.
echo Giving GeoEvent about a minute to finish setting up all it's web services before
echo continuing with the Ops Server configuration...
PING 127.0.0.1 -n 50 > nul

REM ---------------------------------------------------------------------
REM Stopping GeoEvent service so we can continue configuration without any file locks
REM ---------------------------------------------------------------------
echo.
echo.
echo --Stopping the GeoEvent windows service so we can "install" OpsServer
echo   GeoEvent configuration ...
echo.
set execute=net stop %ops_winServicename%
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 10 > nul



REM ---------------------------------------------------------------------
REM Copy Ops Server set of folders/files 
REM ---------------------------------------------------------------------

REM -----------------------------------
REM Copy Data folder
REM -----------------------------------
set ops_destPathData="C:\Data"
echo.
echo.
echo --Copying Ops Server Data folder/files...
echo.
set execute=START /WAIT robocopy %ops_softwareRoot%\GeoEvent\OpsServerConfig\Data\ %ops_destPathData% *.* /S
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL% ROBOCOPY


REM -----------------------------------
REM Copy ProgramData folder
REM -----------------------------------
set ops_destPath="C:\ProgramData\Esri\GeoEventProcessor"
echo.
echo.
echo --Copying Ops Server set of %ops_destPath% folders/files...
echo.
set execute=START /WAIT robocopy %ops_softwareRoot%\GeoEvent\OpsServerConfig\ProgramData\GeoEventProcessor\ %ops_destPath% *.* /S
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL% ROBOCOPY


REM -----------------------------------
REM Copy Deploy folder
REM -----------------------------------
set ops_destPath="C:\Program Files\ArcGIS\Server\GeoEventProcessor\deploy"
echo.
echo.
echo --Copying Ops Server set of %ops_destPath% folders/files...
echo.
set execute=START /WAIT robocopy %ops_softwareRoot%\GeoEvent\OpsServerConfig\deploy\ %ops_destPath% *.* /S
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL% ROBOCOPY


REM -----------------------------------
REM Copy Security folder
REM -----------------------------------
set ops_destPath="C:\Program Files\ArcGIS\Server\GeoEventProcessor\jre\lib\security"
echo.
echo.
echo --Copying Esri CA cert to %ops_destPath% folder...
echo.
set execute=START /WAIT robocopy %ops_softwareRoot%\GeoEvent\OpsServerConfig\security\ %ops_destPath% *.* /S
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL% ROBOCOPY

PING 127.0.0.1 -n 5 > nul

REM ---------------------------------------------------------------------
REM Restart GeoEvent service
REM ---------------------------------------------------------------------
echo.
echo.
echo --Starting the GeoEvent windows service...
echo.
set execute=net start %ops_winServicename%
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 20 > nul

REM ---------------------------------------------------------------------
REM Unset variables
REM ---------------------------------------------------------------------
set ops_ChkErrLevelFile=
set ops_winServicename=
set ops_destPathData=
set ops_destPath=
set execute=


echo.
echo.
echo Finished installing GeoEvent Processor.
echo.
echo.
