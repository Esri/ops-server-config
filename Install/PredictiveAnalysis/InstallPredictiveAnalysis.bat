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
rem # Name:          InstallPredictiveAnalysis.bat
rem #
rem # Purpose:       Installs the Predictive Analysis Web Services 
rem #
rem # Prerequisites: ArcGIS Server must be installed, authorized and ArcGIS Server
rem #                site must exist.
rem #
rem #==============================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

echo.
echo %sectionBreak%
echo Install Predictive Analysis Web Services
echo.
echo.
echo --Installing Predictive Analysis Web Services...
echo.

set execute=%ops_softwareRoot%\PredictiveAnalysis\setup.exe /qb
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
echo.
PING 127.0.0.1 -n 3 > nul

REM ---------------------------------------------------------------------
REM Unset variables
REM ---------------------------------------------------------------------
set ops_ChkErrLevelFile=
set execute=

echo.
echo Finished installing Predictive Analysis Web Services.
echo.
echo.
