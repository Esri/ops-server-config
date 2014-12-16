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
rem # Name:          CreateAGSDataStore.bat
rem #
rem # Purpose:       Creates the ArcGIS Data Store and registers the Data Store
rem #                with the ArcGIS Server site as the managed database.
rem #
rem # Prerequisites: ArcGIS Data Store must be installed (see InstallAGSDataStore.bat)
rem #
rem #==============================================================================
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


 