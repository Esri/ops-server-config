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
rem # Name:          SetOverallErrorLevel.bat
rem #
rem # Purpose:       Sets overall Error Level variable
rem #
rem # Comments:      Used to set "Global" variable ops_OverallErrLvl storing error level.
rem #                Batch file should be called after running any of the batch files
rem #                in the SupportFiles\BatchFiles\Checks directory. If error code is
rem #                passed to batch file, set the "Global" variable = 1 indicating that
rem #                an error has occurred.
rem #==============================================================================
set ErrLvl=%1

REM Batch file compare operations from IF /?
rem EQU - equal
rem NEQ - not equal
rem LSS - less than
rem LEQ - less than or equal
rem GTR - greater than
rem GEQ - greater than or equal

if %ErrLvl% GTR 0 (
  set ops_OverallErrLvl=1
)