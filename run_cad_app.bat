@echo off
SETLOCAL EnableDelayedExpansion

:: --- CONFIGURATION ---
:: Replace 'forvia_env' with your actual conda environment name if different
set ENV_NAME=forvia_env
:: --- END CONFIGURATION ---

echo ============================================================
echo        FORVIA CAD AUTOMATED PIPELINE - LAUNCHER
echo ============================================================
echo.

:: 1. Find Anaconda/Miniconda path
:: We check common locations for the conda initialization script
set CONDA_ACTIVATE_PATH=

if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
    set CONDA_ACTIVATE_PATH=%USERPROFILE%\anaconda3\Scripts\activate.bat
) else if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
    set CONDA_ACTIVATE_PATH=%USERPROFILE%\miniconda3\Scripts\activate.bat
) else if exist "C:\ProgramData\anaconda3\Scripts\activate.bat" (
    set CONDA_ACTIVATE_PATH=C:\ProgramData\anaconda3\Scripts\activate.bat
) else if exist "C:\ProgramData\miniconda3\Scripts\activate.bat" (
    set CONDA_ACTIVATE_PATH=C:\ProgramData\miniconda3\Scripts\activate.bat
)

if "%CONDA_ACTIVATE_PATH%"=="" (
    echo [ERROR] Could not find Anaconda or Miniconda installation.
    echo Please make sure Anaconda is installed and try again.
    pause
    exit /b
)

:: 2. Change directory to the project folder
cd /d "c:\Forvia11"

:: 3. Initialize Conda and Activate Environment
echo [STATUS] Initializing environment: %ENV_NAME%...
call "%CONDA_ACTIVATE_PATH%" %ENV_NAME%

:: 4. Run Streamlit in Headless mode (no extra terminal output)
echo [STATUS] Launching UI... 
echo.
echo Please wait, a browser tab will open automatically.
echo Close this window to stop the application.
echo.

streamlit run streamlit_app.py --server.headless false

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to start Streamlit. 
    echo Ensure 'forvia_env' is created and 'streamlit' is installed.
    pause
)

ENDLOCAL
