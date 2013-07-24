REM =====================================================================
REM Stop/Restart the portal service
REM =====================================================================

set winServicename="Portal for ArcGIS"

echo.
echo %sectionBreak%
echo Restarting windows service %winServicename%...
echo.
net stop %winServicename%
PING 127.0.0.1 -n 10 > nul
net start %winServicename%
PING 127.0.0.1 -n 20 > nul
