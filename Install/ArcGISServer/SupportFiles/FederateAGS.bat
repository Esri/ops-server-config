REM =====================================================================
REM Federate ArcGIS Server site with Portal
REM =====================================================================
set ops_ChkErrLevelFile=%~dp0..\..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat
echo.
echo.
echo %sectionBreak%
echo Federate ArcGIS Server site with Portal and set the hosted server...
echo (also set some othe properties: SSL properties, Geometry service)
echo.
echo.
echo ^- When the web browser opens the "Sign In" page...
echo.
echo    ^-^-^-^-^-^- Federated/Hosted Server ^-^-^-^-^-^-
echo.
echo    1. Sign in with the primary portal admin user.
echo.
echo    2. Click on "My Organization" link ^(if not
echo       already on the page^).
echo.
echo    3. Click "Edit Settings".
echo.
echo    4. Click "Servers" tab on side panel.
echo.
echo    5. Click "Add Server".
echo.
echo    6. For "Server URL" property specify^:
echo.
echo       https^://%ops_FQDN%/arcgis
echo.
echo    7. For "Administration URL" property specify^:
echo.
echo       https^://%ops_FQDN%^:6443/arcgis
echo.
echo    8. For "Username/Password" properties specify the
echo       name and password of the primary site administrator
echo       account that was used to initially log in to Manager
echo       and administer ArcGIS Server.
echo.
echo    9. Click "Add".
echo.
echo   10. In the "Hosting Server" dropdown select^:
echo.
echo       %ops_FQDN%^:6443
echo.
echo.
echo    ^-^-^-^-^-^- SSL Property ^-^-^-^-^-^-
echo.
echo    1. Click "Security" tab on side panel.
echo.
echo    2. Check the "Allow access to the portal through SSL only" option.
echo.
echo.
echo    ^-^-^-^-^-^- Utility Services ^-^-^-^-^-^-
echo.
echo    1. Click "Utility Services" tab on side panel.
echo.
echo.   2. Change the "Geometry" service URL to:
echo.
echo       https^://%ops_FQDN%/arcgis/rest/services/Utilities/Geometry/GeometryServer
echo.
echo.
echo    ^-^-^-^-^-^- Save Changes to Portal Configuration ^-^-^-^-^-^-
echo.
echo    1. Click "Save" to save all the settings you have modified.
echo.
echo    2. Sign out of portal.
echo.
echo    3. Close web browser.
echo.
set execute=%ops_webBrowserExePath% https://%ops_FQDN%/arcgis/home/signin.html?
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 3 > nul
