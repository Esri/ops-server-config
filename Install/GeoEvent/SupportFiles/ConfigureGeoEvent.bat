REM =====================================================================
REM Configure GeoEvent Processor Extension for ArcGIS Server
REM =====================================================================
set ops_ChkErrLevelFile=%~dp0..\..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

echo.
echo.
echo %sectionBreak%
echo Configure GeoEvent Processor
echo.
echo.
echo.
echo   ***********  WARNING  **********  WARNING  ********  WARNING  ************
echo.  **
echo   ** If you have problems re-registering ArcGIS Server with the GeoEvent
echo   ** processor Data Store (see steps below) you may need to modify the
echo   ** GeoEvent Processor keystore with your certificate information.
echo   **
echo   ** See the help topic "Optional: Replacing ArcGIS GeoEvent Processor for
echo   ** Server's self-signed certificate", which can be found on the Resource
echo   ** center at:
echo   **
echo   ** http://resources.arcgis.com/en/help/install-guides/
echo   ** arcgis-geoevent-processor-windows/10.2/index.html#/
echo   ** Optional_Replacing_ArcGIS_GeoEvent_Processor_for_Server_s_self_signed_certificate/02wn00000004000000/
echo   **
echo   **************************************************************************
echo.
echo.
echo.
echo ^- When the web browser opens to the GeoEvent Processor Manager "Sign In" page...
echo.
echo.
echo    Sign in with the default GeoEvent administrator account:
echo.
echo      Username: arcgis
echo      Password: manager
echo.
echo.
echo    ^-^-^-^-^- Change password on GeoEvent Administrator account ^-^-^-^-^-^-
echo.
echo    1. Click the "Security" button at the top of the web page.
echo.
echo.
echo    2. Click the "Edit" button on the "arcgis" account entry.
echo.
echo.
echo    3. For the "Password" and "Repeat Password" property specify: %ops_passWord%
echo.
echo.
echo    4. Click "Save".
echo.
echo.
echo    5. You will be signed out of the GeoEvent Processor Manager; sign back in
echo       using the new password.
echo.
echo       Username: arcgis
echo       Password: %ops_passWord%
echo.
echo.
echo    ^-^-^-^-^- Add new GeoEvent Administrator account ^-^-^-^-^-^-
echo.
echo    This isn't absolutely neccessary to add a new administrator, but it does
echo    provide for a common administrator user and password across the Esri software
echo    on the Ops Server.
echo.
echo.
echo    1. Click the "Security" button at the top of the web page.
echo.
echo.
echo    2. Click the "Add New User" button.
echo.
echo.
echo    3. For "Username" property specify: %ops_userName%
echo.
echo.
echo    4. For "Password" and "Repeat Password" property specify: %ops_passWord%
echo.
echo.
echo    5. For "Full Name" property specify: GeoEvent Server Administrator, Secondary
echo.
echo.
echo    6. Select all "Roles Available" ^(i.e. Administrator, Publisher, and User^) and
echo       'move' them to the "Roles Selected" list by clicking the right arrow button.
echo.
echo.
echo    7. Click "Create".
echo.
echo.
echo    ^-^-^-^-^-^- Reset AGS connection for registered data store ^-^-^-^-^-^-
echo.
echo    1. Click the "Site" button at the top of the web page.
echo.
echo.
echo    2. Click "Data Stores" tab on side panel.
echo.
echo.
echo    3. Under the "Registered ArcGIS Server" list, click the "Edit" button
echo       for the "OpsServer" entry.
echo.
echo.
echo    4. On the "Edit ArcGIS Server" dialog, click in the "URL" text box and
echo       specify the URL to the ArcGIS Server:
echo.
echo       https^://%ops_FQDN%/arcgis/
echo.
echo.
echo    5. Generate a token:
echo.
echo       Click in the "Token" text box. A link to the "generateToken" URL will
echo       be displayed under the "Token" text box in a blue box.
echo.
echo.
echo       Copy the "HTTP referer" URL shown in the blue box.
echo     ^(you will need this value for generating the token^).
echo.
echo.
echo       Click on the "generateToken" URL link.
echo.
echo.
echo       For the "Username" property specify^: %ops_userName%
echo.
echo.
echo       For the "Password" property specify^: %ops_passWord%
echo.
echo.
echo       Paste the "Client Webapp URL" property value you copied from the previous
echo         web page into the "Client Webapp URL" text box.
echo.
echo.
echo       **********  WARNING  **********  WARNING  **********
echo       **                                                **
echo       ** For the "Expiration" property, select "1 year" ** 
echo       **                                                **
echo       **********  WARNING  **********  WARNING  **********
echo.
echo.
echo       Click the "Generate Token" button.
echo.
echo.
echo       Copy the token.
echo.
echo.
echo    6. Click on the previous web browser tab.
echo.
echo.
echo    7. Paste the generated token into the "Token" property textbox.
echo.
echo.
echo    8. Click the "Register" button.
echo.
echo       The "Status" box for this entry should now have a green checkbox.
echo.
echo.
echo    9. Sign out of the GeoEvent Processor Manager.
echo.
echo.
echo   10. Close the web browser.
echo.
echo.
set execute=%ops_webBrowserExePath% https://%ops_FQDN%:6143/geoevent/manager/site.html
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 10 > nul
echo.
