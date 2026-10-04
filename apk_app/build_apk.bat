@echo off
REM Build APK from a path WITHOUT an apostrophe.
REM Folder "study's" breaks flet/flutter packaging on Windows.

set "SRC=%~dp0"
set "SAFE=C:\Users\ABHIJITH\apk_app_build"

if not exist "%SAFE%" (
  echo Creating junction %SAFE% ...
  mklink /J "%SAFE%" "%SRC%"
  if errorlevel 1 (
    echo Failed to create junction. Run this .bat as Administrator once.
    pause
    exit /b 1
  )
)

cd /d "%SAFE%"
echo Building from: %CD%
echo.

REM arm64-only avoids armeabi-v7a gen_snapshot blocks on some Windows PCs
flet build apk --arch arm64

echo.
echo If build succeeded, APK is under:
echo   %SAFE%\build\apk\
echo   (same as apk_app\build\apk\ — look for codeai-receptionist.apk)
pause
