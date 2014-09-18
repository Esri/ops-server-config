@echo off
REM #===========================================================================
REM #
REM # Purpose: Perform Post Web App Deployment operations 
REM #
REM # Prerequisites: Ops Server wwwroot files/folder must already exist in the
REM #                C:\inetpub\wwwroot folder
REM #
REM #===========================================================================
set ops_ChkErrLevelFile=%~dp0\BatchFiles\CheckErrorLevel.bat
set ops_solutionsweb_path=C:\inetpub\wwwroot\SolutionsWeb

REM Check if SolutionsWeb folder exists
set ops_test_path=%ops_solutionsweb_path%
if not exist %ops_test_path% (goto NO_FOLDER)

set sectionBreak===================================================================================
set sectionBreak1=-------------------------------------------------------
echo.
echo.
echo %sectionBreak%
echo               Execute Post Web Application Deployment Operations
echo %sectionBreak%
echo.
echo.
REM ---------------------------------------------------------------------
REM Convert certain web folders to IIS web applications
REM ---------------------------------------------------------------------
echo %sectionBreak1%
echo  Convert web folders in IIS to web application
echo %sectionBreak1%
echo.
echo --Converting SolutionsWeb/Apps/Templates/ImageDiscovery to application...
echo.
set ops_test_path=%ops_solutionsweb_path%\Apps\Templates\ImageDiscovery
if not exist %ops_test_path% (goto NO_FOLDER)
set execute=%windir%\system32\inetsrv\appcmd add app /site.name:"Default Web Site" /path:/SolutionsWeb/Apps/Templates/ImageDiscovery /physicalPath:"%ops_test_path%"
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%

goto END

:NO_FOLDER
@echo.
@echo Error: Folder %ops_test_path% does not exist.
@echo.
@goto END

:END
@echo on