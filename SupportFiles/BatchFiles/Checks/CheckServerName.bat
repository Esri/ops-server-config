@setlocal enableextensions enabledelayedexpansion
@echo off
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
rem # Name:          CheckServerName.bat
rem #
rem # Purpose:       Check Server Name value for underscore "_"
rem #
rem # Comments:      ArcGIS Server and ArcGIS Data Store are not supported on machines
rem #                which have an underscore in the machine name.
rem #
rem #                Learned how to find str within a str in batch file from following
rem #                web post (25 Sept 2014)
rem #                http://stackoverflow.com/questions/7005951/batch-file-find-if-substring-is-in-string-not-in-a-file
rem #                user "paxdiablo" who answered the question Aug 10 '11 at 4:47
rem #==============================================================================
set ops_ChkErrLevelFile=%~dp0..\CheckErrorLevel.bat

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
