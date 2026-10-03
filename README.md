# Kalkulasi SPJ Perjalanan Dinas DPRD (Perpres 72/2025)

Aplikasi desktop Windows (Python + PySide6) untuk menyusun dokumen SPJ perjalanan dinas:
**DP RIIL**, **SP Tanggung Jawab**, dan **Kalkulasi** — ekspor ke Excel (.xlsx, rumus hidup) dan Word (.docx).

## Menjalankan
    pip install -r requirements.txt
    python main.py
Buat .exe: jalankan `build_exe.bat` (hasil: dist\KalkulasiSPJ\KalkulasiSPJ.exe).

## Aturan perhitungan
- Uang harian = hari x tarif provinsi (Tabel 1.2), per destinasi.
- Uang representasi pejabat negara Rp250.000/hari luar kota (Tabel 1.3), sekali per hari.
- Hotel: kolom Pimpinan DPRD (Ketua/Wakil) atau Anggota DPRD (Tabel 1.4). Pilihan 30% tarif x malam
  (lumpsum) atau sesuai kwitansi/bill. Malam = hari - 1 (bisa diubah manual).
- Tiket & transportasi diinput dari nota; Tabel 2.2 hanya pembanding plafon.
- Data pengguna tersimpan di %APPDATA%\KalkulasiSPJ\spj.db.

## Struktur
app/data_perpres.py (tarif) · app/calc.py (mesin hitung) · app/export_xlsx.py · app/export_docx.py · app/ui/
