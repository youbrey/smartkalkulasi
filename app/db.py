"""Penyimpanan lokal (SQLite): data anggota DPRD dan pengaturan."""
import os
import sqlite3
from dataclasses import asdict

from .calc import Settings
from .data_anggota import ANGGOTA_AWAL


def data_dir() -> str:
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    d = os.path.join(base, "KalkulasiSPJ")
    os.makedirs(d, exist_ok=True)
    return d


class Database:
    def __init__(self, path: str | None = None):
        self.path = path or os.path.join(data_dir(), "spj.db")
        self.con = sqlite3.connect(self.path)
        self.con.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        c = self.con
        c.execute("""CREATE TABLE IF NOT EXISTS anggota(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL, jabatan TEXT NOT NULL DEFAULT 'ANGGOTA', nip TEXT NOT NULL DEFAULT '-')""")
        c.execute("CREATE TABLE IF NOT EXISTS pengaturan(kunci TEXT PRIMARY KEY, nilai TEXT)")
        if c.execute("SELECT COUNT(*) FROM anggota").fetchone()[0] == 0:
            c.executemany("INSERT INTO anggota(nama,jabatan) VALUES(?,?)", ANGGOTA_AWAL)
        c.commit()

    # ---- anggota
    def daftar_anggota(self):
        return self.con.execute(
            "SELECT * FROM anggota ORDER BY CASE UPPER(jabatan) WHEN 'KETUA' THEN 0 "
            "WHEN 'WAKIL KETUA' THEN 1 ELSE 2 END, id").fetchall()

    def tambah_anggota(self, nama, jabatan, nip="-"):
        self.con.execute("INSERT INTO anggota(nama,jabatan,nip) VALUES(?,?,?)",
                         (nama.strip(), jabatan.strip().upper(), nip.strip() or "-"))
        self.con.commit()

    def ubah_anggota(self, id_, nama, jabatan, nip):
        self.con.execute("UPDATE anggota SET nama=?,jabatan=?,nip=? WHERE id=?",
                         (nama.strip(), jabatan.strip().upper(), nip.strip() or "-", id_))
        self.con.commit()

    def hapus_anggota(self, id_):
        self.con.execute("DELETE FROM anggota WHERE id=?", (id_,))
        self.con.commit()

    def impor_anggota(self, rows):
        """rows: iterable (nama, jabatan, nip). Nama yang sudah ada dilewati. Return jumlah baru."""
        ada = {r["nama"].strip().upper() for r in self.daftar_anggota()}
        n = 0
        for nama, jab, nip in rows:
            if nama.strip().upper() in ada:
                continue
            self.tambah_anggota(nama, jab, nip)
            ada.add(nama.strip().upper())
            n += 1
        return n

    # ---- pengaturan
    def muat_pengaturan(self) -> Settings:
        s = Settings()
        for r in self.con.execute("SELECT kunci,nilai FROM pengaturan"):
            if hasattr(s, r["kunci"]):
                setattr(s, r["kunci"], r["nilai"])
        return s

    def simpan_pengaturan(self, s: Settings):
        for k, v in asdict(s).items():
            self.con.execute("INSERT OR REPLACE INTO pengaturan(kunci,nilai) VALUES(?,?)", (k, v))
        self.con.commit()


def kategori_dari_jabatan(jabatan: str) -> str:
    j = jabatan.upper()
    return "PIMPINAN" if "KETUA" in j else "ANGGOTA"
