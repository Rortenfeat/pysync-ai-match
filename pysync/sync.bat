@echo off

REM Conda environment name
set CONDA_ENV_NAME=speech39

REM Temporary folder
if "%~1"=="" (
    echo "Usage: sync.bat <Temp folder> <Output folder> <Task ID>"
    exit /b 1
)
REM Check output folder
if "%~2"=="" (
    echo "Usage: sync.bat <Temp folder> <Output folder> <Task ID>"
    exit /b 1
)

REM Task ID
if "%~3"=="" (
    echo "Usage: sync.bat <Temp folder> <Output folder> <Task ID>"
    exit /b 1
)

set input=%1
set output=%2
set task_id=%3

echo --- Preparing to start speech recognition and synchronization task ---
echo Target environment: %CONDA_ENV_NAME%
echo Processing folder: %input%
echo Output folder: %output%
echo Task ID: %task_id%
echo ------------------------------------------

REM Use 'conda run' to execute commands in the specified environment
conda run -n %CONDA_ENV_NAME% --no-capture-output python pysync\sync %input% %output% %task_id%

REM Alternative way
REM call conda activate %CONDA_ENV_NAME%
REM python pysync\sync %input% %output% %task_id%
REM call conda deactivate