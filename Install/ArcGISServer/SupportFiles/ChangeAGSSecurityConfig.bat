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
rem # Name:          ChangeAGSSecurityConfig.bat
rem #
rem # Purpose:       Change the ArcGIS Server Security Configuration 
rem #
rem # Prerequisites: ArcGIS Server must be installed and the ArcGIS Server site
rem #                must exist.
rem #
rem #==============================================================================
set ops_ChkErrLevelFile=%~dp0..\..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat
echo.
echo.
echo %sectionBreak%
echo Change the ArcGIS Server security configuration to "HTTPS Only"...
echo.
echo ^- When the web browser opens ^(a 2 minute delay has been added^)...
echo.
echo    1. Sign in to the "ArcGIS Server Administrator Directory"
echo       site as the ArcGIS Server site administrator.
echo.
echo       Username: %ops_userName%
echo       Password: %ops_passWord%
echo.
echo       NOTE: You will be redirected to the "Security/Config"  page.
echo.
echo.
echo    2. On the "Security/Config" page, click the "update" link.
echo.
echo.
echo    4. In the "Protocol" dropdown, select "HTTPS Only".
echo.
echo.
echo    5. Click "Update".
echo.
echo       NOTE: this may take a minute or two to complete
echo             because the web server has to be restarted.
echo.
echo.
echo    6. Sign out from the "ArcGIS Server Administrator Directory".
echo.
echo.      NOTE: if the sign out results in an error or does not sign out,
echo             just close the web browser.
echo.
echo.
echo    7. Close the web browser.
echo.
echo.
set execute=%ops_webBrowserExePath% http://%ops_FQDN%:6080/arcgis/admin/security/config
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%

PING 127.0.0.1 -n 120 > nul
