REM =====================================================================
REM Create ArcGIS Server Site and other stuff
REM =====================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

REM ---------------------------------------------------------------------
REM Create ArcGIS Server site, create data stores, register data stores
REM ---------------------------------------------------------------------
echo.
echo %sectionBreak%
echo Create ArcGIS Server site, create data stores, and register data stores...
echo.
Call "%~dp0SupportFiles\CreateOpsServer.py" %ops_agsServiceAccount% ^
                %ops_userName% %ops_passWord% %ops_dataDrive% %ops_cacheDrive%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 6 > nul

REM ---------------------------------------------------------------------
REM Start geometry service
REM ---------------------------------------------------------------------
set ops_servicesList=Utilities//Geometry.GeometryServer,Utilities//PrintingTools.GPServer
echo.
echo %sectionBreak%
echo Start the following services^:
echo    %ops_servicesList%
echo.
Call "%~dp0..\..\Publish\Server\StartStopServices.py" %FQDN% ^
    6080 %ops_userName% %ops_passWord% no Start %ops_servicesList%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 3 > nul