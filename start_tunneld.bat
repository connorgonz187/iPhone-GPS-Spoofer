@echo off
title tunneld - Keep This Window Open
echo ============================================
echo  Keep this window open while simulating.
echo  Close it to stop location simulation.
echo ============================================
echo.
python -m pymobiledevice3 remote tunneld
echo.
echo tunneld stopped.
pause