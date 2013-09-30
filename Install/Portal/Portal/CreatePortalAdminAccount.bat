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
echo    1. Enter the required information to create the admin user.
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
set execute=%ops_webBrowserExePath% https://%ops_FQDN%:7443/arcgis/home/signin.html?
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 3 > nul
