echo.
echo --Adding new MIME types...
echo.
echo JSON - .json, application/json
echo.
%windir%\system32\inetsrv\appcmd set config /section:staticContent /+"[fileExtension='.json',mimeType='application/json']"




    
