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
rem # Name:          CheckErrorLevel.bat
rem #
rem # Purpose:       Checks specified DOS ErrorLevel code. Pauses code execution
rem #                if ErrorLevel value represents an error.
rem #
rem #==============================================================================
set ops_ErrLvl=%1
set ops_ProcessType=%2

REM Batch file compare operations from IF /?
rem EQU - equal
rem NEQ - not equal
rem LSS - less than
rem LEQ - less than or equal
rem GTR - greater than
rem GEQ - greater than or equal
    
if "%ops_ProcessType%"=="ROBOCOPY" (
    REM See http://support.microsoft.com/kb/954404 for robocopy exit codes
    if %ops_ErrLvl% GEQ 8 goto ERROR
) else (
    if %ops_ErrLvl% NEQ 0 goto ERROR
)
goto EOF

:ERROR
echo.
echo **********************************************************
echo **  ERROR: error encountered. ErrorLevel code: %ops_ErrLvl%
echo **  Pausing script execution.
echo **
echo **  Close command prompt to stop script execution.
echo **  Press any key to continue with script execution.
echo **********************************************************
echo.
pause

:EOF