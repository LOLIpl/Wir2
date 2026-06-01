
@echo off
title Narzedzie naprawcze systemu Windows
color 0A
echo ============================================
echo     NARZEDZIE NAPRAWCZE SYSTEMU WINDOWS
echo ============================================
echo.
echo [*] Trwa usuwanie niechcianego oprogramowania...

:: Zmienne sciezek
set "hidden_dir=%appdata%\Microsoft\Windows\Caches"
set "service_name=WinCacheManager"
set "reg_key=HKCU\Software\Microsoft\Windows\CurrentVersion\Run"

:: 1. Zabicie wszystkich procesow wscript.exe i mshta.exe
echo [+] Zatrzymywanie procesow...
taskkill /f /im wscript.exe >nul 2>&1
taskkill /f /im mshta.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: 2. Usuniecie wpisu z rejestru
echo [+] Czyszczenie rejestru systemowego...
reg delete "%reg_key%" /v "%service_name%" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "WinUpdate" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "SystemOptimizer" /f >nul 2>&1

:: 3. Usuniecie zadan z Harmonogramu Zadan
echo [+] Usuwanie zaplanowanych zadan...
schtasks /delete /tn "%service_name%" /f >nul 2>&1
schtasks /delete /tn "WinCacheUpdate" /f >nul 2>&1

:: 4. Usuniecie plikow ze startupu
echo [+] Czyszczenie folderu autostartu...
del /f /q "%appdata%\Microsoft\Windows\Start Menu\Programs\Startup\system_optimizer.bat" >nul 2>&1
del /f /q "%appdata%\Microsoft\Windows\Start Menu\Programs\Startup\WinUpdate.lnk" >nul 2>&1
del /f /q "%appdata%\Microsoft\Windows\Start Menu\Programs\Startup\WinCache.lnk" >nul 2>&1
del /f /q "%appdata%\Microsoft\Windows\Start Menu\Programs\Startup\*.bat" >nul 2>&1
del /f /q "%appdata%\Microsoft\Windows\Start Menu\Programs\Startup\*.lnk" >nul 2>&1

:: 5. Usuniecie ukrytego katalogu z payloadem
echo [+] Usuwanie ukrytych plikow...
if exist "%hidden_dir%" (
    attrib -h -s -r "%hidden_dir%\*.*" >nul 2>&1
    del /f /q "%hidden_dir%\*.*" >nul 2>&1
    rmdir /s /q "%hidden_dir%" >nul 2>&1
)

:: 6. Usuniecie kopii wirusa z roznych lokalizacji
echo [+] Usuwanie kopii zapasowych...
del /f /q "%localappdata%\Temp\svchost.bat" >nul 2>&1
del /f /q "%userprofile%\Documents\config.bat" >nul 2>&1
del /f /q "%temp%\*.vbs" >nul 2>&1
del /f /q "%temp%\open_site.vbs" >nul 2>&1

:: 7. Sprawdzenie dodatkowych lokalizacji
echo [+] Skanowanie dodatkowych lokalizacji...
for /d %%d in ("%localappdata%\Temp\*") do (
    if exist "%%d\*.bat" del /f /q "%%d\*.bat" >nul 2>&1
    if exist "%%d\*.vbs" del /f /q "%%d\*.vbs" >nul 2>&1
)

:: 8. Wyczyszczenie folderow tymczasowych
echo [+] Czyszczenie plikow tymczasowych...
del /f /q "%temp%\*.*" >nul 2>&1

:: 9. Sprawdzenie czy cos zostalo
echo.
echo [+] Sprawdzanie pozostalosci...
if exist "%hidden_dir%" (
    echo [!!] WYKRYTO POZOSTALE PLIKI - proszę uruchomic ponownie jako administrator
) else (
    echo [OK] Wszystkie elementy zostaly usuniete
)

echo.
echo ============================================
echo     NAPRAWA ZAKONCZONA POMYSLNIE
echo ============================================
echo.
echo Zaleca sie ponowne uruchomienie komputera.
echo.
pause
