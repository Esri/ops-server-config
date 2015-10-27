rem #------------------------------------------------------------------------------
rem # Copyright 2015 Esri
rem # Licensed under the Apache License, Version 2.0 (the "License");
rem # you may not use this file except in compliance with the License.
rem # You may obtain a copy of the License at
rem #
rem #   http://www.apache.org/licenses/LICENSE-2.0
rem #
rem # Unless required by applicable law or agreed to in writing, software
rem # distributed under the License is distributed on an "AS IS" BASIS,
rem # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
rem # See the License for the specific language governing permissions and
rem # limitations under the License.
rem #==============================================================================
rem # Name:          InstallGeoEventPatches.bat
rem #
rem # Purpose:       Installs any ArcGIS GeoEvent Processor Extension for
rem #                ArcGIS Server patches
rem #
rem # Prerequisites: ArcGIS GeoEvent Processor Extension for ArcGIS Server
rem #                must be installed, authorized and ArcGIS Server
rem #
rem #==============================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

set winServicename=ArcGISGeoEvent

REM ---------------------------------------------------------------------
REM Stop Geoevent Windows Service
REM ---------------------------------------------------------------------
echo.
echo %sectionBreak%
echo Install ArcGIS GeoEvent Extension for ArcGIS Server Group Layer Patch
echo.
echo --Stopping the windows service %winServicename%...
net stop %winServicename%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 3 > nul

REM ---------------------------------------------------------------------
REM Install GeoEvent Processor Extension Group Layer Patch
REM ---------------------------------------------------------------------
set replacement_file=webapp-10.3.1.war
set geoevent_install_root=C:\Program Files\ArcGIS\Server\GeoEvent
echo.
echo --Replacing originally installed Geoevent %replacement_file% file.
echo.
set execute=move "%geoevent_install_root%\system\com\esri\geoevent\manager\webapp\10.3.1\%replacement_file%" "%geoevent_install_root%\%replacement_file%_backup"
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 3 > nul

set execute=copy /Y "%ops_softwareRoot%\ArcGISGeoEventPatches\GroupLayerPatch\%replacement_file%" "%geoevent_install_root%\system\com\esri\geoevent\manager\webapp\10.3.1\%replacement_file%"
echo.
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 3 > nul


REM ---------------------------------------------------------------------
REM Start Geoevent Windows Service
REM ---------------------------------------------------------------------
echo.
echo --Starting the windows service %winServicename%...
net start %winServicename%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%

echo.
echo Waiting 2 minutes before continuing with the Ops Server configuration...
PING 127.0.0.1 -n 120 > nul


REM ---------------------------------------------------------------------
REM Unset variables
REM ---------------------------------------------------------------------
set ops_ChkErrLevelFile=
set execute=
set winServicename=
set replacement_file=
set geoevent_install_root=

echo.
echo.
echo Finished installing ArcGIS GeoEvent Extension for ArcGIS Server Group Layer Patch
echo.
echo.
