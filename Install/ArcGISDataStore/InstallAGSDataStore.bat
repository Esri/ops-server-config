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
rem # Name:          InstallAGSDataStore.bat
rem #
rem # Purpose:       Installs ArcGIS Data Store software 
rem #
rem #==============================================================================
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
REM Issue with Data Store, running windows service by any other account
REM except for LOCALSYSTEM is not supported yet.
set execute=%ops_softwareRoot%\ArcGISDataStore\setup.exe /qb ^
USER_NAME=%ops_dsServiceAccount% PASSWORD=%ops_dsServiceAccountPassword%

echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%

set AGSDATASTORE=C:\Program Files\ArcGIS\DataStore\

echo Waiting 3 minutes before continuing...
PING 127.0.0.1 -n 180 > nul


 