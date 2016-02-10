rem #------------------------------------------------------------------------------
rem # Copyright 2014 Esri
rem # Licensed under the Apache License, Version 2.0 (the "License");
rem # you may not use this file except in compliance with the License.
rem # You may obtain a copy of the License at
rem #
rem #   http://www.apache.org/licenses/LICENSE-2.0
rem #
rem # Unless required by applicable law or agreed to in writing, software
rem # distributed under the License is distributed on an "AS IS" BASIS,
rem # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
rem # See the License for the specific language governing permissions and
rem # limitations under the License.
rem #==============================================================================
rem # Name:          InstallPostgreSQL.bat
rem #
rem # Purpose:       Installs PostgreSQL Database Server
rem #
rem #==============================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

echo.
echo %sectionBreak%
echo Install PostrgreSQL Database Server

REM ---------------------------------------------------------------------
REM Install PostgreSQL server
REM ---------------------------------------------------------------------
echo.
echo --Installing PostgreSQL...
echo.

set execute=%ops_softwareRoot%\Database\PostgreSQL_9.3.5\Postgres_Installation\postgresql-9.3.5-1-windows-x64.exe ^
--unattendedmodeui minimal --mode unattended --superaccount postgres ^
--servicename postgreSQL --serviceaccount %ops_rdbmsServiceAccount% ^
--servicepassword %ops_rdbmsServiceAccountPassword% ^
--superpassword %ops_passWord% --serverport 5432 ^
--prefix %ops_postgresqlInstallDIR% --datadir %ops_postgresqlDataDIR%

echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%

REM ---------------------------------------------------------------------
REM Replace postgreSQL configuration file
REM ---------------------------------------------------------------------
echo.
echo --Replacing originally installed PostgreSQL configuration file (postgresql.conf)
echo   with custom file modified to disable database logging and with
echo   increased number of allowed connections.
echo.
set execute=move %ops_postgresqlDataDIR%\postgresql.conf %ops_postgresqlDataDIR%\postgresql.conf_bak
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%

set execute=copy /Y %~dp0SupportFiles\postgresql.conf %ops_postgresqlDataDIR%\postgresql.conf
echo.
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%


REM ---------------------------------------------------------------------
REM Restart the PostgreSQL service because we switched out the config file
REM ---------------------------------------------------------------------
set winServicename=postgreSQL
echo.
echo --Restarting %winServicename% service...
echo.

net stop %winServicename%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%

net start %winServicename%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%

PING 127.0.0.1 -n 3 > nul
