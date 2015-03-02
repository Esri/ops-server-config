@echo off

:: **IMPORTANT** 
::     You may need to edit Python Path Below to change to the Python 2.X Path on your machine (requires Python 2.X)
::
:: Instructions:
::     To use this script/batch to check the arcgis-solutions-website pages
::
::     1. Copy the following files to arcgis-solutions-website\source
::        a. UrlChecker.py 
::        b. UrlCheckerWithErrorCodeReturn.bat 
::     2. Edit the python below path if necessary
::     3. Run UrlCheckerWithErrorCodeReturn.bat 
::        a. Open a command prompt
::        b. Change directory to arcgis-solutions-website\source
::           > cd {local location}\arcgis-solutions-website\source folder
::        c. Run UrlCheckerWithErrorCodeReturn.bat 

:: This script calls a link checker and exits with an error code if a failure (error code) returned from script

:: TODO: Edit this if necessary to point to the local install of python
SET MY_PYTHON_PATH="C:\Python27\ArcGIS10.3"

if not exist %MY_PYTHON_PATH%\python.exe goto no_python

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
