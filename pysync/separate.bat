@echo off

REM Conda environment name
set CONDA_ENV_NAME=separate39

REM Check if an audio file or folder is provided as a parameter
if "%~1"=="" (
    echo "Usage: separate.bat <audio file or folder path> <temporary folder> [task ID]"
    exit /b 1
)
REM Temporary folder
if "%~2"=="" (
    echo "Usage: separate.bat <audio file or folder path> <temporary folder> [task ID]"
    exit /b 1
)
REM Task ID
set task_id="%random%%random%"
if not "%~3"=="" (
    set task_id=%~3
)

set input=%1

echo --- Preparing to start audio separation task ---
echo Target environment: %CONDA_ENV_NAME%
echo Processing file/folder: %input%
echo Temporary directory: %~2
echo Task ID: %task_id%
echo ------------------------------------------

REM Use 'conda run' to execute commands in the specified environment
REM conda run -n %CONDA_ENV_NAME% python pysync\separate %input% %~2 --task-id %task_id%

REM Alternative way
call conda activate %CONDA_ENV_NAME%
python pysync\separate %input% %~2 --task-id %task_id%
call conda deactivate