REM =====================================================================
REM Install ArcGIS Server and Authorize Software
REM =====================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat
SET FQDN=%ops_FQDN%

echo.
echo %sectionBreak%
echo Install ArcGIS Server

REM ---------------------------------------------------------------------
REM Install ArcGIS Server
REM ---------------------------------------------------------------------
echo.
echo --Installing ArcGIS Server...
echo.
set execute=msiexec /I %ops_softwareRoot%\ArcGISServer\setup.msi /qb ^
USER_NAME=%ops_agsServiceAccount% PASSWORD=%ops_passWord% INSTALLDIR1=C:\Python27

echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%

REM ---------------------------------------------------------------------
REM "Install" PostgreSQL client libraries to ArcGIS Server bin folder
REM ---------------------------------------------------------------------
echo.
echo --Copying PostgreSQL client libraries to ArcGIS Server bin folder...
echo.
set execute=START /WAIT robocopy %ops_softwareRoot%\Database\PostgreSQL_9.2.2\Windows\64bit\ ^
"C:\Program Files\ArcGIS\Server\bin" *.*

echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL% ROBOCOPY

REM ---------------------------------------------------------------------
REM "Install" geometry library to PostgreSQL lib folder
REM ---------------------------------------------------------------------
echo.
echo --Copying geometry library to PostgreSQL lib folder...
echo.
set execute=START /WAIT robocopy "C:\Program Files\ArcGIS\Server\DatabaseSupport\PostgreSQL\9.2\Windows64" ^
%ops_postgresqlInstallDIR%\lib"

echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL% ROBOCOPY

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
echo.
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 15 > nul