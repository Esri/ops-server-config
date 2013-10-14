REM =====================================================================
REM Create the Portal primary administrator account
REM =====================================================================
set ops_ChkErrLevelFile=%~dp0..\..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat
echo.
echo.
echo %sectionBreak%
echo Create the Portal for ArcGIS primary administrator account...
echo.
echo ^- When the web browser opens the "Initial Administrator Account Required" page...
echo.
echo    NOTE: The web browser will open in a minute or two; a delay has been
echo          added to give the portal service time to restart.
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
echo    2. Click "Create".
echo.
echo    3. If creation of the admin account is successful,
echo       you will be directed to the "Sign In" page.
echo.
echo    4. Test if you can sign in.
echo.
echo    5. Sign Out of the portal.
echo.
echo    6. Close the web browser.
echo.
PING 127.0.0.1 -n 80 > nul
set execute=%ops_webBrowserExePath% https://%ops_FQDN%:7443/arcgis/home/signin.html?
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
