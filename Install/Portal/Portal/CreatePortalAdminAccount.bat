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
rem # Name:          CreatePortalAdminAccount.bat
rem #
rem # Purpose:       Creates the Portal for ArcGIS Admin Account. 
rem #
rem # Prerequisites: Portal for ArcGIS must be installed.
rem #
rem #==============================================================================
set ops_ChkErrLevelFile=%~dp0..\..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat
echo.
echo.
echo %sectionBreak%
echo Create the Portal for ArcGIS initial administrator account...
echo.
echo ^- When the web browser opens the "Initial Administrator Account Required" page...
echo    ^(about a 2.5 minute delay has been added)
echo.
echo    NOTEs:
echo       - The web browser will open in about two minutes; a delay has been
echo         added to give the portal service time to restart.
echo.
echo       - If the web browser opens, but the page does not display, refresh
echo         the web page.
echo.
echo.
echo    1. Enter the required information to create the admin user.
echo.
echo       ***************          WARNING         ***************
echo       *** User/password for portal administrator account must be the
echo       *** same as that used for the ArcGIS Server site.
echo       ***
echo       *** User must be set as: %ops_userName%
echo       *** Password must be set as: %ops_passWord%
echo       ***
echo       ********************************************************            
echo.
echo.
echo    2. Click "Create".
echo.
echo.
echo    3. If creation of the admin account is successful,
echo       the "Account Created" dialog will be displayed.
echo       Click "OK" on this dialog.
echo.
echo.
echo    4. When the "Web Adaptor Required" web page is displayed,
echo       you can ignore the instructions on this web page instructing
echo       you to install and config the web adaptor. The web adaptor has
echo       already been installed and it will be configured for portal
echo       automatically in subsequent steps.
echo.
echo.
echo    5. Test if you can sign in by clicking on the "Sign In" link located
echo       in the upper-right of the web page.
echo.
echo.
echo    6. Sign Out of the portal.
echo.
echo.
echo    7. Close the web browser.
echo.
echo.
PING 127.0.0.1 -n 160 > nul
set execute=%ops_webBrowserExePath% https://%ops_FQDN%:7443/arcgis/home/signin.html?
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
