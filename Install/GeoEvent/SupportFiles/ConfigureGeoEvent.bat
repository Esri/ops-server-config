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
echo   ^-^-^-^-^- Export server certificate ^-^-^-^-^-^-
echo.
echo   The reason for exporting the server certificate and importing the certificate
echo   into the GeoEvent Processor (GEP) keystore (see next section) is to establish a
echo   "trust relationship" between the GEP and the ArcGIS Server. Without this
echo   "trust relationship", GEP will not be able to connect to the ArcGIS Server
echo   and therefore will not be able to write features to the feature services.
echo.
echo   NOTE: While these instructions show you how to export the server certificate for
echo         your Ops Server, you could also export your root CA certificate which would
echo         allow you to connect the GEP to an ArcGIS Server that resides on other servers
echo         within your domain. To export your root CA certificate, use the "Certificate"
echo         snap-in within the Microsoft Management Console.
echo.
echo.
echo   When the web browser opens to the portal home page, export the
echo   server certificate (the instructions differ by web browser)...
echo.
echo.
echo   For Chrome:
echo.
echo       1. Click on the "lock" icon to the left of the portal URL;
echo          within the context menu that is displayed, click on
echo          the "Connection" tab; click on the "Certificate information"
echo          hyperlink, which opens the "Certificate" dialog.
echo.
echo.
echo       2. On the "Certificate dialog", click on the "Details" tab, and
echo          click on the "Copy to File" button, which opens the
echo          "Certificate Export Wizard".
echo.
echo.
echo       3. On the "Certificate Export Wizard, click "Next"; make sure the
echo          export format "DER encoded binary X.509 (.CER)" option is
echo          selected; click "Next".
echo.
echo.
echo.      4. Specify the path and file name for the export file and click
echo          "Next".
echo.
echo.
echo       5. On the "Completing the Certificate Export Wizard" dialog,
echo          click "Finish" and close all export wizard dialogs.
echo.
echo.
echo       6. Close the web browser.
echo.
echo.
echo   For Internet Explorer:
echo.
echo       1. Click on the "lock" icon to the right of the portal URL;
echo          within the context menu that is displayed, click on
echo          the "View certificates" hyperlink, which opens the "Certificate" dialog.
echo.
echo.
echo       2. On the "Certificate dialog", click on the "Details" tab, and
echo          click on the "Copy to File" button, which opens the
echo          "Certificate Export Wizard".
echo.
echo.
echo       3. On the "Certificate Export Wizard, click "Next"; make sure the
echo          export format "DER encoded binary X.509 (.CER)" option is
echo          selected; click "Next".
echo.
echo.
echo.      4. Specify the path and file name for the export file and click
echo          "Next".
echo.
echo.
echo       5. On the "Completing the Certificate Export Wizard" dialog,
echo          click "Finish" and close all export wizard dialogs.
echo.
echo.
echo       6. Close the web browser.
echo.
echo.
echo   For Firefox:
echo.
echo       1. Click on the "lock" icon to the left of the portal URL;
echo          within the context menu that is displayed, click on
echo          the "More Information" button, which displays the
echo          "Security" tab on the "Page Info" dialog.
echo.
echo.
echo       2. On the "Certificate Viewer" dialog, click on the "Details" tab, and
echo          click on the "Export" button.
echo.
echo.
echo       3. On the "Save Certificate To File" dialog, specify the path
echo          and file name for the export file; make sure the
echo          "Save as type" value is set to "X.509 Certificate (DER) (*.der)", and
echo          click "Save".
echo.
echo.
echo       4. Close all certificate related dialogs.
echo.
echo.
echo       5. Close the web browser.
echo.
echo.
set execute=%ops_webBrowserExePath% https://%ops_FQDN%/%ops_WebAdaptor_Portal%/home
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%

echo.
echo.
echo    ^-^-^-^-^- Import certificate into the GeoEvent Processor Keystore ^-^-^-^-^-^-
echo.
echo.
echo    1. Create a backup copy of the "cacerts" file located in the following folder:
echo       C:\Program Files\ArcGIS\Server\GeoEventProcessor\jre\lib\security
echo.
echo.
echo    2. Open a command window (cmd.exe) with administrator privilege (i.e.
echo       "Run as administrator" context menu).
echo.
echo.
echo    3. In the command window change directory to the directory where the Java keytool.exe
echo       is located, i.e. C:\Program Files\ArcGIS\Server\GeoEventProcessor\jre\bin
echo.
echo.
echo    4. Import the certificate by executing the keytool.exe with the following parameters:
echo.
echo         keytool -import -keystore "C:\Program Files\ArcGIS\Server\GeoEventProcessor\jre\lib\security\cacerts"
echo         -alias agsca -file PATH_TO_CERTIFICATE -trustcacerts -storepass changeit
echo.
echo         NOTEs:
echo             - Replace "PATH_TO_CERTIFICATE" with the full path and file name of the
echo               certificate file you exported.
echo.
echo             - The "alias" parameter value can be anything value that you would like.
echo               In the tool usage above the alias is set to "agsca" (i.e. ArcGIS Server
echo               certificate authority) to denote that this certificate is for a specific
echo               server. If you are importing a certificate for your root CA, you would
echo               want to change the alias to something similiar to "rootCA".
echo.
echo             - When prompted with the question "Trust this certificate? [no]:" specify yes
echo               and hit return key.
echo.
echo.
echo   5. Stop and restart the "ArcGIS GeoEvent Processor" windows service.
echo.
echo.
echo   6. After restarting the windows service, press any key within this command window to continue with
echo      configuring GeoEvent Processor.
echo.
pause
echo   Giving GeoEvent Processor a minute to finish starting...
PING 127.0.0.1 -n 60 > nul
echo.
echo.
echo.
echo.
echo    ^-^-^-^-^- Sign into the GeoEvent Manager ^-^-^-^-^-^-
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
echo    5. For "Full Name" property specify: GeoEvent Server Administrator, Primary
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
echo       specify the URL to the ArcGIS Server ^(connect through port inorder
echo       to connect to ArcGIS Server primary site administrator^):
echo.
echo       https^://%ops_FQDN%:6443/arcgis/
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
