REM =====================================================================
REM Install PostgreSQL Database Server
REM =====================================================================

echo.
echo %sectionBreak%
echo Install PostrgreSQL Database Server

REM ---------------------------------------------------------------------
REM Install PostgreSQL server
REM ---------------------------------------------------------------------
echo.
echo --Installing PostgreSQL...
%ops_softwareRoot%\Database\PostgreSQL_9.2.2\Postgres_Installation\postgresql-9.2.2-1-windows-x64.exe ^
    --unattendedmodeui minimal --mode unattended --superaccount postgres ^
    --servicename postgreSQL --serviceaccount postgres --servicepassword %ops_passWord% ^
    --superpassword %ops_passWord% --serverport 5432 ^
    --prefix %ops_postgresqlInstallDIR% --datadir %ops_postgresqlDataDIR%

REM ---------------------------------------------------------------------
REM Replace postgreSQL configuration file
REM ---------------------------------------------------------------------
echo.
echo --Replacing originally installed PostgreSQL config. file (postgresql.conf)
echo   with file modified so that replacation will work
echo   on PostgreSQL databases
echo.
move %ops_postgresqlDataDIR%\postgresql.conf %ops_postgresqlDataDIR%\postgresql.conf_bak
copy /Y %~dp0SupportFiles\postgresql.conf %ops_postgresqlDataDIR%\postgresql.conf

REM ---------------------------------------------------------------------
REM Restart the PostgreSQL service because we switched out the config file
REM ---------------------------------------------------------------------
set winServicename=postgreSQL
echo.
echo --Restarting %winServicename% service...
echo.
net stop %winServicename%
net start %winServicename%


PING 127.0.0.1 -n 3 > nul
