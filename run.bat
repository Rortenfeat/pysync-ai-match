@echo off

REM set defaults
set input=input
set output=output
set temp=temp

REM generate Task ID
set task_id=%random%%random%

REM handle input parameters
if not "%~1"=="" set input=%~1
if not "%~2"=="" set output=%~2
if not "%~3"=="" set temp=%~3

echo --- Running PySync-Ai-Match ---
echo Input: %input%
echo Output: %output%
echo Temp Dir: %temp%
echo --------------------------

REM first: call separate.bat
echo Running separate.bat...
call pysync\separate.bat "%input%" "%temp%" "%task_id%"

REM second: call sync.bat
echo Running sync.bat...
call pysync\sync.bat "%temp%" "%output%" "%task_id%"

echo Done!