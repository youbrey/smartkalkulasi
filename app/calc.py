"""Mesin perhitungan biaya perjalanan dinas (Perpres 72/2025)."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from datetime import date, datetime

from . import data_perpres as P

BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]

KATEGORI_BIAYA = [
    "Tiket Pesawat Pergi", "Tiket Pesawat Pulang", "Tiket Kapal Laut",
    "Tiket Bus / Kereta Api", "Iuran Wajib / Kontribusi", "Biaya Transit",
    "Sewa Kendaraan", "Biaya Transportasi",
]
PESAWAT = {"Tiket Pesawat Pergi", "Tiket Pesawat Pulang"}


def rp(n) -> str:
    """Format angka gaya Indonesia: 1.234.567"""
    return f"{int(round(n)):,}".replace(",", ".")


def tgl_id(d: date, upper=False) -> str:
    s = f"{d.day} {BULAN[d.month]} {d.year}"
    return s.upper() if upper else s


def rentang_tgl(a: date, b: date) -> str:
    if a == b:
        return tgl_id(a, True)
    if a.year == b.year and a.month == b.month:
        return f"{a.day} S/D {b.day} {BULAN[b.month].upper()} {b.year}"
    if a.year == b.year:
        return f"{a.day} {BULAN[a.month].upper()} S/D {b.day} {BULAN[b.month].upper()} {b.year}"
    return f"{tgl_id(a, True)} S/D {tgl_id(b, True)}"


def nama_provinsi(p: str) -> str:
    """'JAWA BARAT' -> 'Jawa Barat', 'DKI JAKARTA' -> 'DKI Jakarta'."""
    out = []
    for w in p.split():
        if w in ("DKI",) or w.startswith("D.I"):
            out.append(w)
        else:
            out.append(w.capitalize())
    return " ".join(out)


# ----------------------------------------------------------------- model
@dataclass
class Leg:
    provinsi: str = "DKI JAKARTA"
    tujuan: str = ""                 # mis. KOTA BANDUNG
    jenis: str = P.JENIS_LUAR
    hari: int = 1                    # jumlah hari uang harian
    malam_30: int = 0                # jumlah malam dibayar lumpsum 30% tarif
    malam_riil: int = 0              # jumlah malam dibayar sesuai kwitansi/bill
    hotel_riil_total: int = 0        # total nominal pada kwitansi/bill untuk malam_riil di atas

    @property
    def malam(self) -> int:
        return self.malam_30 + self.malam_riil


@dataclass
class BiayaItem:
    kategori: str = "Tiket Pesawat Pergi"
    uraian: str = ""
    qty: float = 1
    harga: int = 0


@dataclass
class TransRiil:
    uraian: str = ""
    qty: int = 0
    harga: int = 0


TRANS_RIIL_LABEL = [
    "Transportasi dari tempat kedudukan ke terminal bis/bandara/pelabuhan (PP)",
    "Transportasi dari terminal bis/bandara/pelabuhan ke tempat tujuan (PP)",
    "Transportasi dari tempat tujuan ke tempat tujuan lainnya",
]


@dataclass
class Trip:
    nama: str = ""
    nip: str = "-"
    kategori: str = "ANGGOTA"        # PIMPINAN | ANGGOTA
    jabatan_dok: str = ""            # teks jabatan pada dokumen
    asal: str = "BITUNG"
    tgl_berangkat: date = field(default_factory=date.today)
    tgl_kembali: date = field(default_factory=date.today)
    spt_no: str = ""
    spt_tgl: date = field(default_factory=date.today)
    spd_no: str = ""
    spd_tgl: date = field(default_factory=date.today)
    tgl_dokumen: date = field(default_factory=date.today)
    tujuan_teks: str = ""            # bila kosong: dibentuk otomatis
    sertakan_representasi: bool = True
    legs: list = field(default_factory=lambda: [Leg()])
    items: list = field(default_factory=list)
    trans_riil: list = field(default_factory=lambda: [TransRiil(t) for t in TRANS_RIIL_LABEL])

    @property
    def lama(self) -> int:
        return max((self.tgl_kembali - self.tgl_berangkat).days + 1, 1)

    def tujuan_dokumen(self) -> str:
        if self.tujuan_teks.strip():
            return self.tujuan_teks.strip().upper()
        parts = [l.tujuan.strip().upper() or nama_provinsi(l.provinsi).upper() for l in self.legs]
        return f"{self.asal.upper()} - " + "-".join(parts)

    # -- simpan / muat draf
    def to_json(self) -> str:
        def conv(o):
            if isinstance(o, date):
                return o.isoformat()
            raise TypeError
        return json.dumps(asdict(self), default=conv, ensure_ascii=False, indent=1)

    @staticmethod
    def from_json(s: str) -> "Trip":
        d = json.loads(s)
        for k in ("tgl_berangkat", "tgl_kembali", "spt_tgl", "spd_tgl", "tgl_dokumen"):
            d[k] = datetime.strptime(d[k], "%Y-%m-%d").date()
        d["legs"] = [Leg(**_migrasi_leg(x)) for x in d["legs"]]
        d["items"] = [BiayaItem(**x) for x in d["items"]]
        d["trans_riil"] = [TransRiil(**x) for x in d["trans_riil"]]
        return Trip(**d)


def _migrasi_leg(x: dict) -> dict:
    """Konversi draf lama (satu mode hotel per destinasi) ke struktur baru (campuran 30% + kwitansi)."""
    if "malam_30" in x or "malam_riil" in x:
        return x
    malam = x.pop("malam", 0)
    mode = x.pop("hotel_mode", "30")
    per_malam = x.pop("hotel_riil", 0)
    if mode == "RIIL":
        x["malam_30"], x["malam_riil"], x["hotel_riil_total"] = 0, malam, per_malam * malam
    else:
        x["malam_30"], x["malam_riil"], x["hotel_riil_total"] = malam, 0, 0
    return x


@dataclass
class Line:
    label: str
    qty: float
    unit: str
    harga: int
    note: str = ""

    @property
    def jumlah(self) -> int:
        return int(round(self.qty * self.harga))


@dataclass
class Settings:
    kota: str = "BITUNG"
    provinsi_asal: str = "SULAWESI UTARA"
    instansi: str = "DPRD KOTA BITUNG"
    sekwan_jabatan: str = "Sekretaris DPRD Kota Bitung"
    sekwan_nama: str = "Drs. ALBERT M. SARESE, M.Si."
    sekwan_nip: str = "19681011 199010 1 002"
    pptk_jabatan: str = "Pejabat Pelaksana Teknis Kegiatan"
    pptk_nama: str = "MIRANDA M. MAILENZUN"
    pptk_nip: str = "19710120 199003 2 002"
    pembulatan: str = "NEAREST"      # NEAREST | UP | NONE


@dataclass
class Result:
    harian: list       # Line per leg
    representasi: list
    hotel30: list      # masuk DP Riil (tanpa bukti)
    hotel_riil: list   # sesuai kwitansi
    items: dict        # kategori -> [Line]
    trans_riil: list   # Line (3 baris) - biaya transportasi, HANYA masuk lembar KALKULASI
    warnings: list

    @property
    def total_dp_riil(self):
        """Total Daftar Pengeluaran Riil: uang harian, representasi, hotel 30%. TIDAK termasuk transportasi."""
        return sum(l.jumlah for l in self.harian + self.representasi + self.hotel30)

    @property
    def total_transportasi(self):
        """Biaya transportasi (dengan atau tanpa bukti) - hanya tampil di lembar KALKULASI."""
        return sum(l.jumlah for l in self.trans_riil) + sum(l.jumlah for l in self.items.get("Biaya Transportasi", []))

    @property
    def total_bukti(self):
        return (sum(l.jumlah for l in self.hotel_riil)
                + sum(l.jumlah for ls in self.items.values() for l in ls))

    @property
    def total(self):
        return self.total_dp_riil + self.total_bukti + sum(l.jumlah for l in self.trans_riil)


def bulatkan(x: int, mode: str) -> int:
    if mode == "UP":
        return int(math.ceil(x / 1000.0) * 1000)
    if mode == "NONE":
        return int(x)
    return int(math.floor(x / 1000.0 + 0.5) * 1000)


def hitung(trip: Trip) -> Result:
    warn = []
    harian, hotel30, hotel_riil = [], [], []
    hari_luar = hari_dalam = 0

    for i, lg in enumerate(trip.legs, 1):
        nm = nama_provinsi(lg.provinsi)
        if lg.hari > 0:
            tarif = P.uang_harian(lg.provinsi, lg.jenis)
            lbl = f"Uang Harian {nm}"
            if lg.jenis != P.JENIS_LUAR:
                lbl += f" ({P.JENIS_LABEL[lg.jenis]})"
            harian.append(Line(lbl, lg.hari, "hari", tarif))
            if lg.jenis == P.JENIS_DALAM:
                hari_dalam += lg.hari
            else:
                hari_luar += lg.hari
        if lg.malam_30 > 0 or lg.malam_riil > 0 or lg.hotel_riil_total > 0:
            plafon = P.tarif_hotel(lg.provinsi, trip.kategori)
            if lg.malam_30 > 0:
                per = plafon * P.HOTEL_LUMPSUM_PERSEN // 100
                hotel30.append(Line(f"Biaya Hotel {nm} ({P.HOTEL_LUMPSUM_PERSEN}% x {rp(plafon)})",
                                    lg.malam_30, "malam", per,
                                    f"({rp(plafon)}x {P.HOTEL_LUMPSUM_PERSEN}%)"))
            if lg.malam_riil > 0 or lg.hotel_riil_total > 0:
                hotel_riil.append(Line(f"Biaya Hotel {nm}", 1, "paket", lg.hotel_riil_total,
                                       f"({lg.malam_riil} malam, sesuai kwitansi/bill)"))
                if lg.hotel_riil_total == 0:
                    warn.append(f"Destinasi {i} ({nm}): total biaya hotel sesuai kwitansi masih Rp 0.")
                elif lg.malam_riil > 0:
                    rata2 = lg.hotel_riil_total / lg.malam_riil
                    if rata2 > plafon:
                        warn.append(f"Destinasi {i} ({nm}): rata-rata hotel Rp {rp(rata2)}/malam melebihi "
                                    f"satuan biaya Tabel 1.4 (Rp {rp(plafon)}). Perpres membolehkan at cost "
                                    f"selama ada bukti riil.")

    repr_lines = []
    if trip.sertakan_representasi:
        if hari_luar:
            repr_lines.append(Line("Uang Representasi", hari_luar, "hari", P.uang_representasi(P.JENIS_LUAR)))
        if hari_dalam:
            repr_lines.append(Line("Uang Representasi (dalam kota > 8 jam)", hari_dalam, "hari",
                                   P.uang_representasi(P.JENIS_DALAM)))

    items = {k: [] for k in KATEGORI_BIAYA}
    for it in trip.items:
        if it.harga or it.qty and it.uraian:
            items.setdefault(it.kategori, []).append(Line(it.uraian, it.qty, "x", it.harga))

    trans = [Line(TRANS_RIIL_LABEL[i], t.qty, "kali", t.harga) for i, t in enumerate(trip.trans_riil)]

    sum_hari = sum(l.hari for l in trip.legs)
    sum_malam = sum(l.malam_30 + l.malam_riil for l in trip.legs)
    if sum_hari != trip.lama:
        warn.append(f"Total hari destinasi ({sum_hari}) berbeda dari lama perjalanan ({trip.lama} hari).")
    if sum_malam > max(trip.lama - 1, 0):
        warn.append(f"Total malam hotel ({sum_malam}) melebihi jumlah malam perjalanan ({max(trip.lama - 1, 0)}).")
    if trip.tgl_kembali < trip.tgl_berangkat:
        warn.append("Tanggal kembali lebih awal dari tanggal berangkat.")

    return Result(harian, repr_lines, hotel30, hotel_riil, items, trans, warn)
