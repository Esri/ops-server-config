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
rem # Name:          CreateOneClickInstaller.bat
rem #
rem # Purpose:       Creates the Operations Dashboard One-click Installer and copies
rem #                the Operations Dashboard installer and the help files to the
rem #                appropriate portal deployment folder.
rem #
rem # Prerequisites:
rem #                - .NET framework 4.5 must be installed.
rem #                - Portal for ArcGIS must be installed.
rem #
rem #==============================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

echo.
echo.
echo %sectionBreak%
echo Create the Operations Dashboard One-click Installer...
echo.
echo.

REM ---------------------------------------------------------------------
REM Create the folder to store the deployment files created by the 
REM Ops Dashboard Deployment Utility
REM ---------------------------------------------------------------------
set ops_outputFolder=%ops_tempInstallDir%\OpsDashboardUtilityOutput

echo --Creating the output folder %ops_outputFolder%...
echo.

set execute=mkdir %ops_outputFolder%

if not exist %ops_outputFolder% (
  echo %execute%
  echo.
  %execute%
  Call %ops_ChkErrLevelFile% %ERRORLEVEL%
)


REM ---------------------------------------------------------------------
REM Run the Operations Dashboard Deployment Utility
REM ---------------------------------------------------------------------
echo.
echo.
echo --Running the Operations Dashboard Deployment Utility...
echo.
echo.
echo   NOTE: When the "Importing a new private signature key" dialog is
echo         displayed, click "OK".
echo.
echo.
set execute=START /WAIT %ops_softwareRoot%\OpsDashboardUtility\OperationsDashboardUtility.exe ^
/outPut %ops_outputFolder% /url https://%ops_FQDN%/%ops_WebAdaptor_Portal% ^
/certpath %ops_softwareRoot%\OpsDashboardUtility\Certificate\DefenseSolutions.pfx ^
/password esripassword /CertType selfsigned
echo %execute%
echo.
echo It will take a couple of minutes for the OperationsDashboardUtility.exe to complete.
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 20 > nul


REM -----------------------------------
REM Copy One-click installer
REM -----------------------------------
set ops_destPath="C:\Program Files\ArcGIS\Portal\apps\dashboard-win"
echo.
echo.
echo --Copying Ops Dashboard One-click installer files to %ops_destPath%...
echo.
set execute=START /WAIT robocopy %ops_outputFolder%\dashboard-win %ops_destPath% *.* /S
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL% ROBOCOPY


REM -----------------------------------
REM Copy help files
REM -----------------------------------
set ops_destPath="C:\Program Files\ArcGIS\Portal\webapps\docroot\help\en\operations-dashboard"
echo.
echo.
echo --Copying Ops Dashboard help files to %ops_destPath%...
echo.
set execute=START /WAIT robocopy %ops_outputFolder%\operations-dashboard %ops_destPath% *.* /S
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL% ROBOCOPY
