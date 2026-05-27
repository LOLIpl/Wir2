@echo off
:: Usuwa wpis z rejestru
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "SystemHelper" /f

:: Zatrzymuje wszystkie instancje wirusa
taskkill /f /im cmd.exe /fi "WINDOWTITLE eq *virus*" 2>nul
taskkill /f /im wscript.exe 2>nul

:: Usuwa plik wirusa (zakładając, że nazywa się virus.bat na pulpicie)
del /f /q "%userprofile%\Desktop\virus.bat" 2>nul

echo Naprawa zakończona. Uruchom ponownie komputer.
pause
