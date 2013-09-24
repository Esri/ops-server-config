REM =====================================================================
REM Install ArcGIS Server and Authorize Software
REM =====================================================================
SET FQDN=%ops_FQDN%

echo.
echo %sectionBreak%
echo Install ArcGIS Server

REM ---------------------------------------------------------------------
REM Install ArcGIS Server
REM ---------------------------------------------------------------------
echo.
echo --Installing ArcGIS Server...
msiexec /I %ops_softwareRoot%\ArcGISServer\setup.msi /qb ^
    USER_NAME=%ops_agsServiceAccount% PASSWORD=%ops_passWord% INSTALLDIR1=C:\Python27
    
REM ---------------------------------------------------------------------
REM "Install" PostgreSQL client libraries to ArcGIS Server bin folder
REM ---------------------------------------------------------------------
echo.
echo --Copying PostgreSQL client libraries to ArcGIS Server bin folder...
START /WAIT robocopy %ops_softwareRoot%\Database\PostgreSQL_9.2.2\Windows\64bit\ ^
    "C:\Program Files\ArcGIS\Server\bin" *.*


REM ---------------------------------------------------------------------
REM "Install" geometry library to PostgreSQL lib folder
REM ---------------------------------------------------------------------
echo.
echo --Copying geometry library to PostgreSQL lib folder...
START /WAIT robocopy "C:\Program Files\ArcGIS\Server\DatabaseSupport\PostgreSQL\9.2\Windows64" ^
    %ops_postgresqlInstallDIR%\lib"

REM ---------------------------------------------------------------------
REM Authorize ArcGIS Server Software
REM ---------------------------------------------------------------------
echo.
echo --Authorizing ArcGIS Server...
echo.
echo   Will use the following file to authorize. If no file found, 
echo   Software Authorization wizard will walk user through process:
echo   %ops_AGSAuthFile%
echo.
set execute=%ops_softwareAuthExePath% -S Ver %ops_AGSVersion%
if exist %ops_AGSAuthFile% (
    set execute=%execute% -LIF %ops_AGSAuthFile%
) else (
    echo   Prompting user for authorizing information...
)
%execute%
PING 127.0.0.1 -n 15 > nul