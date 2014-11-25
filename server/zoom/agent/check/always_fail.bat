@echo off

if "%1" == "--succeed" goto succeed
if NOT "%1" == "--succeed" goto fail

:succeed
EXIT /B 0

:fail
EXIT /B 1