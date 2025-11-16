@echo on
setlocal

REM 1) Always run from the app folder
cd /d "C:\Users\Lenovo\Desktop\Projects\onsd-ultrasound-system\ultra_app"

REM 2) Make sure the package root (EyeUIEnterFace) is importable
set "PYTHONPATH=C:\Users\Lenovo\Desktop\Projects\onsd-ultrasound-system"

REM 3) Extra diagnostics (Qt issues, crashes, etc.)
set QT_DEBUG_PLUGINS=1
set PYTHONUTF8=1

REM 4) Use the REAL Python (not the WindowsApps alias)
"C:\Users\Lenovo\AppData\Local\Programs\Python\Python313\python.exe" -X faulthandler -u main.py

echo.
echo === Process finished. If there were errors, they are shown above. ===
echo Press any key to close...
pause >nul
