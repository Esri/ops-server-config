REM =====================================================================
REM Install Message Simulator
REM =====================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

echo.
echo %sectionBreak%
echo Install Message Simulator

REM ---------------------------------------------------------------------
REM Copy Message Simulator files
REM ---------------------------------------------------------------------
set ops_destPath="C:\MessageSimulator"
echo.
echo.
echo --Copying Message Simulator folders/files...
echo.
set execute=START /WAIT robocopy %ops_softwareRoot%\MessageSimulator\ %ops_destPath% *.* /S
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL% ROBOCOPY
PING 127.0.0.1 -n 3 > nul

REM ---------------------------------------------------------------------
REM Create Windows Scheduled Task
REM ---------------------------------------------------------------------
set ops_taskName=MessageSimulator
echo.
echo.
echo --Create Windows Scheduled Task for Message Simulator...
echo.
REM /F switch will create the task even if it already exists.
REM
set execute=SCHTASKS /Create /XML %~dp0SupportFiles\MessageSimulatorTask.xml /TN %ops_taskName% /F
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 3 > nul

echo.
echo.
echo --Disable the Message Simulator task...
echo.
set execute=SCHTASKS /Change /TN %ops_taskName% /DISABLE
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 3 > nul