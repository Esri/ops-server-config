REM =====================================================================
REM Check file/folder existence
REM =====================================================================
set ops_ChkErrLevelFile=%~dp0CheckErrorLevel.bat
set ops_ErrCode=0
set filelist=%*
echo.
for %%d in (%filelist%) do (
   if not exist %%d (
     set ops_ErrCode=1
     echo *** ERROR: The following file\folder does not exist: %%d
   )
)
Call %ops_ChkErrLevelFile% %ops_ErrCode%