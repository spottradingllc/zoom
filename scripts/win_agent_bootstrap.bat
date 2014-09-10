@echo off

::---------------------------------------------
:: Purpose: Install python packages needed for
::          Zookeeper Agent on Windows Servers
:: Author:  Nick Moskwinski
::---------------------------------------------


SET OUTPUTFILE=%TMP%\bootstrap.log
SET BOOTSTRAPDIR=\\spotsms01\InstallSoftware\ZooKeeperAgent

REM Install Python
echo. > %OUTPUTFILE%
echo installing python >> %OUTPUTFILE%
msiexec.exe /q /i %BOOTSTRAPDIR%\python-2.7.6.msi >> %OUTPUTFILE%

REM Add Python to PATH variable
setx /m PATH "%PATH%;C:\Python27\"

REM run pywin by hand
%BOOTSTRAPDIR%\pywin\pywin32-218.win32-py2.7.exe"

REM Do python installs
call:pythonInstall setuptools
call:pythonInstall kazoo
call:pythonInstall backports
call:pythonInstall wmi
call:pythonInstall tornado
call:pythonInstall kazoo
call:pythonInstall requests

REM Do Xcopy Installs
call:xcopyInstall psutil
call:xcopyInstall zope

REM Install zkagent as a Windows Service
echo.
echo Installing agent as the "zkagent" Windows service.  >> %OUTPUTFILE%
C:\Python27\python.exe "C:\Program Files\Spot Trading LLC\zoom\server\spot\zoom\common\win_install.py" --username spottrading\svc.python --password Pyth0n --startup auto install  >> %OUTPUTFILE%

exit

::-----------------------------------------
::   Function section starts below here
::-----------------------------------------

:pythonInstall
REM call:pythonInstall <packagename>
echo. >> %OUTPUTFILE%
echo installing %~1 >> %OUTPUTFILE%
xcopy /c /y /s /e /i %BOOTSTRAPDIR%\%~1 %TMP%\%~1
pushd %TMP%\%~1
C:\Python27\python.exe %TMP%\%~1\setup.py install >> %OUTPUTFILE%
echo done installing %~1 >> %OUTPUTFILE%
goto:eof

:xcopyInstall
REM  call:xcopyInstall <packagename>
echo. >> %OUTPUTFILE%
echo installing %~1 >> %OUTPUTFILE%
xcopy /c /y /s /e %BOOTSTRAPDIR%\%~1 C:\Python27\Lib\site-packages >> %OUTPUTFILE%
echo done installing %~1 >> %OUTPUTFILE%
goto:eof

