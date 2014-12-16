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
rem # Name:          RegisterPortalwithWebAdaptor.bat
rem #
rem # Purpose:       Register Portal for ArcGIS with the Web Adpator for IIS 
rem #
rem # Prerequisites: Portal for ArcGIS and Web Adaptor for IIS must be installed.
rem #
rem #==============================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

echo.
echo %sectionBreak%
echo Register Portal for ArcGIS with the Web Adpator for IIS...
echo.
echo    NOTE: a 4 minute delay has been added to give the portal service time to restart.
echo.
PING 127.0.0.1 -n 240 > nul
set execute=%ops_ConfWebAdaptorExePath% /m portal /w https://%ops_FQDN%/%ops_WebAdaptor_Portal%/webadaptor /g http://%ops_FQDN%:7080 ^
/u %ops_userName% /p %ops_passWord%

if exist %ops_ConfWebAdaptorExePath% (
    echo %execute%
    %execute%
    Call %ops_ChkErrLevelFile% %ERRORLEVEL%
    PING 127.0.0.1 -n 10 > nul
) else (
    echo **********************************************************
    echo **  ERROR:
    echo **  Could not register Portal for ArcGIS with the WebAdaptor.
    echo **  The executable '%ops_ConfWebAdaptorExePath%'
    echo **  does not exist.
    echo **  Exiting RegisteringAGSwithWebAdaptor.bat.
    echo **********************************************************
    echo.
    Call %ops_ChkErrLevelFile% 1
)