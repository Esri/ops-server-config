@setlocal enableextensions enabledelayedexpansion
@echo off
set ops_ChkErrLevelFile=%~dp0..\CheckErrorLevel.bat
REM =====================================================================
REM Check Server Name value for underscore "_"
REM =====================================================================
REM ArcGIS Server and ArcGIS Data Store are not supported on machines
REM which have an underscore in the machine name.
REM
REM Learned how to find str within a str in batch file from following web post (25 Sept 2014)
REM http://stackoverflow.com/questions/7005951/batch-file-find-if-substring-is-in-string-not-in-a-file
REM user "paxdiablo" who answered the question Aug 10 '11 at 4:47
REM
set input_str=%1
set ops_ErrCode=0
if not x%input_str:_=%==x%input_str% (
    set ops_ErrCode=1
    echo.
    echo **********************************************************
    echo **  ERROR: Server name contains an underscore ^("_"^).
    echo **
    echo **  ArcGIS Server and ArcGIS Data Store are not supported
    echo **  on machines with underscores in the machine name.
    echo **********************************************************
    echo.
)
Call %ops_ChkErrLevelFile% %ops_ErrCode%
endlocal
