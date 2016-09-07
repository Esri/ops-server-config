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
rem # Name:          InstallEM4OWebContent.bat
rem #
rem # Purpose:       Installs Esri Maps for Office Web Content
rem #
rem #==============================================================================
set ops_ChkErrLevelFile=%~dp0..\..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

echo.
echo %sectionBreak%
echo Install Esri Maps for Office Web Content

REM ---------------------------------------------------------------------
REM Install Esri Maps for Office Web Content
REM ---------------------------------------------------------------------
echo.
echo --Installing Esri Maps for Office Web Content...
echo.
set execute=%ops_softwareRoot%\EsriMapsForOffice\WebContent\Portal_Resources_for_AM4O_4.1_Beta_en.exe /passive

echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%

PING 127.0.0.1 -n 15 > nul