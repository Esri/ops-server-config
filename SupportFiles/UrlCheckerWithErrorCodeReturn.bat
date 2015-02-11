@echo off

:: **IMPORTANT** Add Python to Path or SET Below to Python Path on your machine

:: This script calls a link checker and exits with an error code if a failure (error code) returned from script

SET MY_PYTHON_PATH="C:\Python27\ArcGIS10.1"

if not exist %MY_PYTHON_PATH% goto no_python

%MY_PYTHON_PATH%\python UrlChecker.py Results-military.csv military 
if %errorlevel% NEQ 0 goto failure

%MY_PYTHON_PATH%\python UrlChecker.py Results-intel.csv intelligence
if %errorlevel% NEQ 0 goto failure

:: Custom example if you just want to check a single subfolder, edit & uncomment
::%MY_PYTHON_PATH%\python UrlChecker.py Results-Example.csv military\land-operations\operational-environment
::if %errorlevel% NEQ 0 goto failure


echo No Bad Links Detected
exit /b 0

:failure
echo ********** BAD LINKS DETECTED **********
exit /b 1

:no_python
echo **********  PYTHON NOT FOUND  **********
echo Python not found at: %MY_PYTHON_PATH%
exit /b 1
