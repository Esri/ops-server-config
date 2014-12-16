rem #------------------------------------------------------------------------------
rem # Copyright 2014 Esri
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
rem # Name:          InstallGeoEvent.bat
rem #
rem # Purpose:       Installs ArcGIS GeoEvent Processor Extension for ArcGIS Server 
rem #
rem # Prerequisites: ArcGIS Server must be installed, authorized and ArcGIS Server
rem #                site must exist.
rem #
rem #==============================================================================
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
