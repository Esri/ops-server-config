echo.
echo --Setting IIS default document...
echo.
%windir%\system32\inetsrv\appcmd set config /section:defaultDocument ^
    /+files.[value='default.ashx']




    
