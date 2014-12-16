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
rem # Name:          InstallWebAdaptor.bat
rem #
rem # Purpose:       Install ArcGIS Web Adpator for IIS (installs one web adaptor
rem #                for ArcGIS Server and one for Portal for ArcGIS)
rem #
rem # Prerequisites: Web Adaptor prerequisites and ArcGIS Server must be installed.
rem #
rem #==============================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

echo.
echo %sectionBreak%
echo Install ArcGIS Web Adaptor for IIS
echo.
echo --Installing Web Adaptor for ArcGIS Server ^(%ops_WebAdaptor_AGS%^)...
echo.
set execute=%ops_softwareRoot%\WebAdaptorIIS\setup.exe /qb ADDLOCAL=ALL VDIRNAME=%ops_WebAdaptor_AGS% WEBSITE_ID=1 PORT=80
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 6 > nul
echo.
echo.
echo --Installing Web Adaptor for Portal for ArcGIS ^(%ops_WebAdaptor_Portal%^)...
echo.
set execute=%ops_softwareRoot%\WebAdaptorIIS\setup.exe /qb ADDLOCAL=ALL VDIRNAME=%ops_WebAdaptor_Portal% WEBSITE_ID=1 PORT=80
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 6 > nul