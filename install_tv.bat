@echo off
REM ─────────────────────────────────────────────────────
REM  Sports TV - Install to Android TV via ADB WiFi
REM ─────────────────────────────────────────────────────
set ADB=C:\Users\Acer\AppData\Local\Android\Sdk\platform-tools\adb.exe
set APK=D:\projects\sports_tv\SportsTv.apk

if "%1"=="" (
    echo.
    echo  Usage: install_tv.bat ^<TV_IP_ADDRESS^>
    echo  Example: install_tv.bat 192.168.100.75
    echo.
    echo  How to find your TV IP:
    echo    Settings ^> Network ^> About / Status ^> IP Address
    echo.
    pause
    exit /b 1
)

set TV_IP=%1
echo.
echo [1/3] Connecting to TV at %TV_IP%:5555 ...
"%ADB%" connect %TV_IP%:5555

echo.
echo [2/3] Installing Sports TV app ...
"%ADB%" -s %TV_IP%:5555 install -r "%APK%"

echo.
echo [3/3] Launching app ...
"%ADB%" -s %TV_IP%:5555 shell am start -n com.sportstv.app/.MainActivity

echo.
echo  Done! Sports TV should now be open on your TV.
pause
