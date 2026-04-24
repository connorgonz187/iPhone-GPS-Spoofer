@echo off
title Location Sim - Control Window
echo ============================================
echo  Location Simulator
echo  Press any key to stop and close everything.
echo ============================================
echo.

:: Launch Apple Devices (required for USB detection)
echo Starting Apple Devices...
start "" "explorer.exe" shell:AppsFolder\AppleInc.AppleDevices_nzyj5cx40ttqa!App
timeout /t 3 /nobreak >nul

:: Launch the GUI
echo Starting GUI...
start "" pythonw "%~dp0gui_sim.py"

:: Launch tunneld in a minimized window
echo Starting tunneld...
start "tunneld" /min python -m pymobiledevice3 remote tunneld

echo.
echo All services running. Press any key to stop...
pause >nul

:: Cleanup: kill everything
echo Shutting down...
taskkill /FI "WINDOWTITLE eq tunneld*" /F >nul 2>&1
taskkill /IM "AppleDevices.exe" /F >nul 2>&1
taskkill /IM "pythonw.exe" /F >nul 2>&1
echo Done.