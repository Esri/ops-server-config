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
rem # Name:          InstallPortal.bat
rem #
rem # Purpose:       Installs/authorizes Portal for ArcGIS; Configure ArcGIS Server
rem #                Services Directory properties to point to locally hosted ArcGIS
rem #                for JavaScript API
rem #
rem # Prerequisites: ArcGIS Server must be installed.
rem #
rem #==============================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat
SET FQDN=%ops_FQDN%

REM ---------------------------------------------------------------------
REM Install Portal for ArcGIS
REM ---------------------------------------------------------------------
echo.
echo %sectionBreak%
echo Install Portal for ArcGIS
echo.
echo --Installing Portal for ArcGIS...
echo.
set execute=%ops_softwareRoot%\PortalForArcGIS\setup.exe /qb CONTENTDIR=C:\arcgisportal

echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
echo Adding a 2 minute delay before moving on to authorize portal...
PING 127.0.0.1 -n 120 > nul

REM ---------------------------------------------------------------------
REM Authorize Portal for ArcGIS
REM ---------------------------------------------------------------------
echo.
echo --Authorizing Portal for ArcGIS...
echo.
echo   Will use the following file to authorize. If no file found, 
echo   Software Authorization wizard will walk user through process:
echo   %ops_PortalAuthFile%
echo.
set execute=%ops_softwareAuthExePath% -S Ver %ops_PortalVersion%
if exist %ops_PortalAuthFile% (
    set execute=%execute% -LIF %ops_PortalAuthFile%
) else (
    echo   Prompting user for authorizing information...
)
echo.
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 25 > nul

REM ---------------------------------------------------------------------
REM Configure ArcGIS Server Services Directory properties to point to
REM locally hosted ArcGIS for JavaScript API
REM ---------------------------------------------------------------------
echo.
echo %sectionBreak%
echo Configure ArcGIS Server Services Directory to point to
echo locally hosted ArcGIS for JavaScript API...
echo.
Call "%~dp0..\..\SupportFiles\SetServicesDirectoryProps.py" ^
 %FQDN% 6443 %ops_userName% %ops_passWord% Yes
echo.
 