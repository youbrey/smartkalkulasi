@echo off
REM Membuat KalkulasiSPJ.exe (Windows) - hasil di folder dist\KalkulasiSPJ
pip install -r requirements.txt
pyinstaller --noconfirm --windowed --name KalkulasiSPJ main.py
echo.
echo Selesai. Jalankan dist\KalkulasiSPJ\KalkulasiSPJ.exe
pause
