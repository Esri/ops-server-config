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
rem # Name:          InstallArcGISServer.bat
rem #
rem # Purpose:       Installs and authorizes ArcGIS Server 
rem #
rem #==============================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat
SET FQDN=%ops_FQDN%

echo.
echo %sectionBreak%
echo Install ArcGIS Server

REM ---------------------------------------------------------------------
REM Install ArcGIS Server
REM ---------------------------------------------------------------------
echo.
echo --Installing ArcGIS Server...
echo.
set execute=%ops_softwareRoot%\ArcGISServer\setup.exe /qb ^
USER_NAME=%ops_agsServiceAccount% PASSWORD=%ops_agsServiceAccountPassword% ^
INSTALLDIR1=C:\Python27

echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%

REM ---------------------------------------------------------------------
REM "Install" geometry library to PostgreSQL lib folder
REM ---------------------------------------------------------------------
echo.
echo --Copying geometry library to PostgreSQL lib folder...
echo.
set execute=START /WAIT robocopy "C:\Program Files\ArcGIS\Server\DatabaseSupport\PostgreSQL\9.3\Windows64" ^
%ops_postgresqlInstallDIR%\lib"

echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL% ROBOCOPY

REM ---------------------------------------------------------------------
REM Authorize ArcGIS Server Software
REM ---------------------------------------------------------------------
echo.
echo --Authorizing ArcGIS Server...
echo.
echo   Will use the following file to authorize. If no file found, 
echo   Software Authorization wizard will walk user through process:
echo   %ops_AGSAuthFile%
echo.
set execute=%ops_softwareAuthExePath% -S Ver %ops_AGSVersion%
if exist %ops_AGSAuthFile% (
    set execute=%execute% -LIF %ops_AGSAuthFile%
) else (
    echo   Prompting user for authorizing information...
)
echo.
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 15 > nul