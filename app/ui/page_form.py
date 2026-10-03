import os
import sys

from PySide6.QtCore import QDate, Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFrame,
                               QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                               QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget)

from .. import data_perpres as P
from ..calc import (KATEGORI_BIAYA, PESAWAT, TRANS_RIIL_LABEL, BiayaItem, Leg, Settings,
                    TransRiil, Trip, bulatkan, hitung, nama_provinsi, rp)
from ..db import Database, kategori_dari_jabatan
from ..export_docx import export_docx
from ..export_xlsx import export_xlsx
from .widgets import Card, DatePicker, NoWheelCombo, NoWheelSpin, RpSpin, SearchCombo, field

ALAT_KELENGKAPAN = ["", "KOMISI I", "KOMISI II", "KOMISI III", "BADAN ANGGARAN",
                    "BADAN MUSYAWARAH", "BAPEMPERDA", "BADAN KEHORMATAN"]


def qdate(d):
    return QDate(d.year, d.month, d.day)


def mkdate():
    return DatePicker(QDate.currentDate())


# ------------------------------------------------------------------ destinasi
class LegWidget(QFrame):
    changed = Signal()
    removeRequested = Signal(object)

    def __init__(self, idx=1):
        super().__init__()
        self.setObjectName("Leg")
        self._manual = False
        self._loading = False
        g = QGridLayout(self)
        g.setContentsMargins(14, 12, 14, 12)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(6)

        self.chip = QLabel(f"Destinasi {idx}"); self.chip.setObjectName("Chip")
        self.btn_del = QPushButton("Hapus"); self.btn_del.setProperty("kind", "danger")
        self.btn_del.clicked.connect(lambda: self.removeRequested.emit(self))
        top = QHBoxLayout(); top.addWidget(self.chip); top.addStretch(); top.addWidget(self.btn_del)
        g.addLayout(top, 0, 0, 1, 4)

        self.cb_prov = SearchCombo(); self.cb_prov.set_items(P.DAFTAR_PROVINSI)
        self.cb_prov.setCurrentText("DKI JAKARTA")
        self.ed_tujuan = QLineEdit(); self.ed_tujuan.setPlaceholderText("mis. KOTA BANDUNG")
        self.cb_jenis = NoWheelCombo()
        for k, v in P.JENIS_LABEL.items():
            self.cb_jenis.addItem(v, k)
        self.sp_hari = NoWheelSpin(); self.sp_hari.setRange(0, 90); self.sp_hari.setSuffix(" hari"); self.sp_hari.setValue(1)

        self.sp_malam30 = NoWheelSpin(); self.sp_malam30.setRange(0, 90); self.sp_malam30.setSuffix(" malam")
        self.sp_malam_riil = NoWheelSpin(); self.sp_malam_riil.setRange(0, 90); self.sp_malam_riil.setSuffix(" malam")
        self.lb_riil_total = field("Total sesuai kwitansi/bill (untuk malam di atas)")
        self.sp_riil_total = RpSpin()
        self.info = QLabel(); self.info.setObjectName("Info"); self.info.setWordWrap(True)

        g.addWidget(field("Provinsi tujuan"), 1, 0, 1, 2); g.addWidget(field("Kota / Kabupaten tujuan"), 1, 2, 1, 2)
        g.addWidget(self.cb_prov, 2, 0, 1, 2); g.addWidget(self.ed_tujuan, 2, 2, 1, 2)
        g.addWidget(field("Jenis perjalanan"), 3, 0); g.addWidget(field("Uang harian"), 3, 1)
        g.addWidget(self.cb_jenis, 4, 0); g.addWidget(self.sp_hari, 4, 1)
        g.addWidget(field("Malam — skema 30% (lumpsum)"), 3, 2); g.addWidget(field("Malam — sesuai kwitansi/bill"), 3, 3)
        g.addWidget(self.sp_malam30, 4, 2); g.addWidget(self.sp_malam_riil, 4, 3)
        g.addWidget(self.lb_riil_total, 5, 3); g.addWidget(self.sp_riil_total, 6, 3)
        g.addWidget(self.info, 5, 0, 2, 3)
        g.setColumnStretch(0, 3); g.setColumnStretch(1, 2); g.setColumnStretch(2, 2); g.setColumnStretch(3, 3)

        self.cb_prov.currentTextChanged.connect(self._emit)
        self.cb_jenis.currentIndexChanged.connect(self._emit)
        self.ed_tujuan.textChanged.connect(self._emit)
        self.sp_riil_total.valueChanged.connect(self._emit)
        self.sp_hari.valueChanged.connect(self._user_edit)
        self.sp_malam30.valueChanged.connect(self._user_edit)
        self.sp_malam_riil.valueChanged.connect(self._user_edit)
        self.sp_malam_riil.valueChanged.connect(self._toggle)
        self._toggle()

    def _toggle(self):
        ada = self.sp_malam_riil.value() > 0
        self.lb_riil_total.setVisible(ada)
        self.sp_riil_total.setVisible(ada)

    def _emit(self, *_):
        if not self._loading:
            self.changed.emit()

    def _user_edit(self, *_):
        if not self._loading:
            self._manual = True
            self.changed.emit()

    def set_index(self, i):
        self.chip.setText(f"Destinasi {i}")

    def set_removable(self, ok):
        self.btn_del.setVisible(ok)

    def auto(self, hari, malam):
        if self._manual:
            return
        self._loading = True
        self.sp_hari.setValue(hari); self.sp_malam30.setValue(malam); self.sp_malam_riil.setValue(0)
        self._loading = False
        self._toggle()

    def leg(self) -> Leg:
        prov = self.cb_prov.currentText().strip().upper()
        return Leg(provinsi=prov if prov in P.DAFTAR_PROVINSI else "", tujuan=self.ed_tujuan.text(),
                   jenis=self.cb_jenis.currentData(), hari=self.sp_hari.value(),
                   malam_30=self.sp_malam30.value(), malam_riil=self.sp_malam_riil.value(),
                   hotel_riil_total=self.sp_riil_total.value())

    def load(self, lg: Leg):
        self._loading = True
        self._manual = True
        self.cb_prov.setCurrentText(lg.provinsi)
        self.ed_tujuan.setText(lg.tujuan)
        self.cb_jenis.setCurrentIndex(self.cb_jenis.findData(lg.jenis))
        self.sp_hari.setValue(lg.hari)
        self.sp_malam30.setValue(lg.malam_30); self.sp_malam_riil.setValue(lg.malam_riil)
        self.sp_riil_total.setValue(lg.hotel_riil_total)
        self._loading = False
        self._toggle()

    def refresh_info(self, kategori):
        lg = self.leg()
        if not lg.provinsi:
            self.info.setText("Pilih provinsi dari daftar Perpres.")
            return
        harian = P.uang_harian(lg.provinsi, lg.jenis)
        plafon = P.tarif_hotel(lg.provinsi, kategori)
        txt = f"Uang harian Rp {rp(harian)}/hari  ·  Tarif hotel (Tabel 1.4) Rp {rp(plafon)}/malam"
        if lg.malam_30 > 0:
            txt += f"  ·  30% = Rp {rp(plafon * P.HOTEL_LUMPSUM_PERSEN // 100)}/malam"
        if lg.malam_riil > 0:
            rata2 = lg.hotel_riil_total / lg.malam_riil if lg.malam_riil else 0
            txt += f"  ·  kwitansi rata-rata Rp {rp(rata2)}/malam"
        self.info.setText(txt)


# ------------------------------------------------------------------ biaya dengan bukti
class ItemRow(QFrame):
    changed = Signal()
    removeRequested = Signal(object)

    def __init__(self):
        super().__init__()
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        self.cb = NoWheelCombo(); self.cb.addItems(KATEGORI_BIAYA)
        self.ed = QLineEdit(); self.ed.setPlaceholderText("Uraian / rute"); self.ed.setMinimumWidth(80)
        self.qty = NoWheelSpin(); self.qty.setRange(1, 999); self.qty.setPrefix("x ")
        self.harga = RpSpin()
        self.jml = QLabel("Rp 0"); self.jml.setMinimumWidth(110); self.jml.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.bt = QPushButton("✕"); self.bt.setProperty("kind", "danger"); self.bt.setFixedWidth(34)
        self.bt.clicked.connect(lambda: self.removeRequested.emit(self))
        h.addWidget(self.cb, 3); h.addWidget(self.ed, 4); h.addWidget(self.qty, 1); h.addWidget(self.harga, 3)
        h.addWidget(self.jml); h.addWidget(self.bt)
        self.cb.currentIndexChanged.connect(self._c); self.ed.textChanged.connect(self._c)
        self.qty.valueChanged.connect(self._c); self.harga.valueChanged.connect(self._c)
        self._loading = False

    def _c(self, *_):
        self.jml.setText(f"Rp {rp(self.qty.value() * self.harga.value())}")
        if not self._loading:
            self.changed.emit()

    def item(self) -> BiayaItem:
        return BiayaItem(self.cb.currentText(), self.ed.text().strip(), self.qty.value(), self.harga.value())

    def load(self, it: BiayaItem):
        self._loading = True
        self.cb.setCurrentText(it.kategori); self.ed.setText(it.uraian)
        self.qty.setValue(int(it.qty)); self.harga.setValue(int(it.harga))
        self._loading = False
        self._c()


def sep():
    f = QFrame(); f.setFrameShape(QFrame.HLine); f.setStyleSheet("color:#E5E7EB;")
    return f


# ================================================================== halaman utama
class FormPage(QWidget):
    def __init__(self, db: Database, settings: Settings):
        super().__init__()
        self.db, self.settings = db, settings
        self._loading = False
        self.legs, self.rows = [], []
        self._build()
        self.reload_anggota()
        self.add_leg()
        self.refresh()

    # ---- UI
    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(20)

        left = QVBoxLayout(); left.setSpacing(4)
        t = QLabel("Buat SPJ Perjalanan Dinas"); t.setObjectName("PageTitle")
        s = QLabel("Isi formulir - biaya uang harian dan hotel dihitung otomatis berdasarkan Perpres 72/2025.")
        s.setObjectName("PageSub")
        left.addWidget(t); left.addWidget(s); left.addSpacing(10)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget(); col = QVBoxLayout(inner); col.setSpacing(16); col.setContentsMargins(0, 0, 8, 0)
        scroll.setWidget(inner)
        left.addWidget(scroll, 1)
        root.addLayout(left, 1)

        # 1. Pelaksana
        c = Card("1 · Pelaksana perjalanan dinas", "Pilih dari database pimpinan & anggota DPRD.")
        g = QGridLayout(); g.setHorizontalSpacing(12); g.setVerticalSpacing(6)
        self.cb_anggota = SearchCombo()
        self.cb_ak = NoWheelCombo(); self.cb_ak.setEditable(True)
        self.cb_ak.addItems(ALAT_KELENGKAPAN)
        self.cb_ak.lineEdit().setPlaceholderText("mis. KOMISI I (opsional)")
        self.ed_jabatan = QLineEdit(); self.ed_nip = QLineEdit("-")
        self.cb_kat = NoWheelCombo()
        self.cb_kat.addItem("Pimpinan DPRD - Tabel 1.4 kolom (4)", "PIMPINAN")
        self.cb_kat.addItem("Anggota DPRD - Tabel 1.4 kolom (5)", "ANGGOTA")
        g.addWidget(field("Nama pelaksana"), 0, 0, 1, 2); g.addWidget(self.cb_anggota, 1, 0, 1, 2)
        g.addWidget(field("Alat kelengkapan"), 2, 0); g.addWidget(field("NIP"), 2, 1)
        g.addWidget(self.cb_ak, 3, 0); g.addWidget(self.ed_nip, 3, 1)
        g.addWidget(field("Jabatan pada dokumen"), 4, 0, 1, 2); g.addWidget(self.ed_jabatan, 5, 0, 1, 2)
        g.addWidget(field("Kategori tarif penginapan"), 6, 0, 1, 2); g.addWidget(self.cb_kat, 7, 0, 1, 2)
        c.add(g); col.addWidget(c)

        # 2. Dasar perjalanan
        c = Card("2 · Dasar & jadwal perjalanan")
        g = QGridLayout(); g.setHorizontalSpacing(12); g.setVerticalSpacing(6)
        self.ed_spt = QLineEdit(); self.ed_spt.setPlaceholderText("mis. 98/SPT/DPRD/V/2025")
        self.dt_spt = mkdate()
        self.ed_spd = QLineEdit(); self.ed_spd.setPlaceholderText("mis. 120/SPD.LD/Setwan/V/2025")
        self.dt_spd = mkdate()
        self.dt_ber = mkdate(); self.dt_kem = mkdate(); self.dt_dok = mkdate()
        self.lb_lama = QLabel("1 hari"); self.lb_lama.setObjectName("Chip")
        self.ed_asal = QLineEdit(self.settings.kota)
        self.ed_tujuan = QLineEdit(); self.ed_tujuan.setPlaceholderText("Otomatis dari destinasi (boleh diisi manual)")
        g.addWidget(field("Nomor SPT"), 0, 0); g.addWidget(field("Tanggal SPT"), 0, 1)
        g.addWidget(self.ed_spt, 1, 0); g.addWidget(self.dt_spt, 1, 1)
        g.addWidget(field("Nomor SPD"), 2, 0); g.addWidget(field("Tanggal SPD"), 2, 1)
        g.addWidget(self.ed_spd, 3, 0); g.addWidget(self.dt_spd, 3, 1)
        g.addWidget(field("Tanggal berangkat"), 4, 0); g.addWidget(field("Tanggal kembali"), 4, 1)
        g.addWidget(self.dt_ber, 5, 0); g.addWidget(self.dt_kem, 5, 1)
        g.addWidget(field("Lama perjalanan"), 6, 0); g.addWidget(field("Tanggal dokumen (tanda tangan)"), 6, 1)
        g.addWidget(self.lb_lama, 7, 0, alignment=Qt.AlignLeft); g.addWidget(self.dt_dok, 7, 1)
        g.addWidget(field("Kota asal"), 8, 0); g.addWidget(field("Tujuan pada dokumen"), 8, 1)
        g.addWidget(self.ed_asal, 9, 0); g.addWidget(self.ed_tujuan, 9, 1)
        c.add(g); col.addWidget(c)

        # 3. Destinasi
        c = Card("3 · Destinasi perjalanan dinas",
                 "Tambahkan lebih dari satu destinasi bila perjalanan singgah di beberapa provinsi. "
                 "Uang harian dan hotel mengikuti tarif provinsi masing-masing. Malam hotel boleh dipecah: "
                 "sebagian 30% (tanpa bukti) dan sebagian lagi sesuai total nominal kwitansi/bill yang dimiliki.")
        self.legs_box = QVBoxLayout(); self.legs_box.setSpacing(10)
        c.add(self.legs_box)
        b = QPushButton("＋ Tambah destinasi"); b.setProperty("kind", "ghost")
        b.clicked.connect(lambda: self.add_leg(user=True))
        c.add(b); col.addWidget(c)

        # 4. Biaya dengan bukti
        c = Card("4 · Tiket & transportasi (sesuai kwitansi / nota)",
                 "Masukkan nilai yang tertera pada bukti. Perpres 72/2025 menetapkan tiket dan taksi at cost.")
        self.items_box = QVBoxLayout(); self.items_box.setSpacing(8)
        c.add(self.items_box)
        b = QPushButton("＋ Tambah biaya"); b.setProperty("kind", "ghost")
        b.clicked.connect(lambda: self.add_item(user=True))
        c.add(b)
        c.add(sep())
        c.add(field("Cek plafon tiket pesawat PP (Tabel 2.2) — hanya sebagai pembanding"))
        h = QHBoxLayout()
        self.cb_pa = SearchCombo(); self.cb_pa.set_items(P.KOTA_TIKET)
        self.cb_pb = SearchCombo(); self.cb_pb.set_items(P.KOTA_TIKET)
        self.cb_pa.setCurrentText("MANADO"); self.cb_pb.setCurrentText("JAKARTA")
        h.addWidget(self.cb_pa); h.addWidget(QLabel("→")); h.addWidget(self.cb_pb)
        c.add(h)
        self.lb_plafon = QLabel(); self.lb_plafon.setObjectName("Info"); self.lb_plafon.setWordWrap(True)
        c.add(self.lb_plafon)
        self.cb_pa.currentTextChanged.connect(self._plafon); self.cb_pb.currentTextChanged.connect(self._plafon)
        col.addWidget(c)

        # 5. Transportasi tanpa bukti
        c = Card("5 · Transportasi tanpa bukti (Daftar Pengeluaran Riil)",
                 "Taksi/transportasi lokal yang tidak ada bukti pengeluarannya. Tarif taksi dapat diisi otomatis dari Tabel 2.3.")
        self.tr_rows = []
        for i, lab in enumerate(TRANS_RIIL_LABEL):
            l = QLabel(lab); l.setWordWrap(True)
            q = NoWheelSpin(); q.setRange(0, 99); q.setSuffix(" kali")
            h_ = RpSpin()
            q.valueChanged.connect(self._changed); h_.valueChanged.connect(self._changed)
            row = QHBoxLayout(); row.addWidget(l, 5); row.addWidget(q, 1); row.addWidget(h_, 2)
            c.add(row); self.tr_rows.append((q, h_))
        b = QPushButton("Isi tarif taksi otomatis (Tabel 2.3)"); b.setProperty("kind", "ghost")
        b.clicked.connect(self.isi_taksi)
        c.add(b); col.addWidget(c)

        # 6. Opsi
        c = Card("6 · Opsi")
        self.chk_repr = QCheckBox("Sertakan uang representasi (pejabat negara / pejabat daerah)")
        self.chk_repr.setChecked(True); self.chk_repr.toggled.connect(self._changed)
        c.add(self.chk_repr); col.addWidget(c)
        col.addStretch(1)

        # ---- panel ringkasan
        side = Card("Ringkasan biaya")
        side.setFixedWidth(320)
        self.sum_grid = QGridLayout(); self.sum_grid.setHorizontalSpacing(8); self.sum_grid.setVerticalSpacing(7)
        side.add(self.sum_grid)
        side.add(sep())
        lt = QLabel("Total dibulatkan"); lt.setProperty("cls", "field")
        self.lb_total = QLabel("Rp 0"); self.lb_total.setObjectName("Total")
        side.add(lt); side.add(self.lb_total)
        self.lb_warn = QLabel(); self.lb_warn.setObjectName("Warn"); self.lb_warn.setWordWrap(True)
        side.add(self.lb_warn)
        b1 = QPushButton("Ekspor ke Excel (.xlsx)"); b1.setProperty("kind", "primary"); b1.clicked.connect(lambda: self.export("xlsx"))
        b2 = QPushButton("Ekspor ke Word (.docx)"); b2.clicked.connect(lambda: self.export("docx"))
        b3 = QPushButton("Simpan draf"); b3.clicked.connect(self.simpan_draf)
        b4 = QPushButton("Buka draf"); b4.clicked.connect(self.buka_draf)
        b5 = QPushButton("Formulir baru"); b5.setProperty("kind", "ghost"); b5.clicked.connect(self.reset)
        for b in (b1, b2):
            side.add(b)
        h = QHBoxLayout(); h.addWidget(b3); h.addWidget(b4); side.add(h)
        side.add(b5)
        side.lay.addStretch(1)
        root.addWidget(side)

        # sinyal
        self.cb_anggota.currentIndexChanged.connect(self._anggota_changed)
        self.cb_ak.currentTextChanged.connect(lambda *_: self._compose_jabatan(keep_nip=True))
        self.cb_kat.currentIndexChanged.connect(self._changed)
        self.dt_ber.dateChanged.connect(self._tgl_changed); self.dt_kem.dateChanged.connect(self._tgl_changed)
        for w in (self.ed_jabatan, self.ed_nip, self.ed_spt, self.ed_spd, self.ed_asal, self.ed_tujuan):
            w.textChanged.connect(self._changed)
        self._plafon()

    # ---- data
    def reload_anggota(self):
        cur = self.cb_anggota.currentData()
        self._loading = True
        rows = self.db.daftar_anggota()
        self.cb_anggota.set_items([f"{r['nama']}  ·  {r['jabatan'].title()}" for r in rows])
        for i, r in enumerate(rows):
            self.cb_anggota.setItemData(i, dict(id=r["id"], nama=r["nama"], jabatan=r["jabatan"], nip=r["nip"]))
        if cur:
            for i, r in enumerate(rows):
                if r["id"] == cur["id"]:
                    self.cb_anggota.setCurrentIndex(i)
        self._loading = False

    def apply_settings(self, st: Settings):
        self.settings = st
        self.ed_asal.setText(st.kota)
        self._compose_jabatan()
        self.refresh()

    def _anggota_changed(self, *_):
        if self._loading:
            return
        d = self.cb_anggota.currentData()
        if d:
            self.cb_kat.setCurrentIndex(self.cb_kat.findData(kategori_dari_jabatan(d["jabatan"])))
        self._compose_jabatan()
        self._changed()

    def _compose_jabatan(self, keep_nip=False):
        d = self.cb_anggota.currentData()
        if not d or self._loading:
            return
        jab = d["jabatan"].upper()
        ak = self.cb_ak.currentText().strip().upper()
        inst = self.settings.instansi
        self.ed_jabatan.setText(f"{jab} {inst}" if "KETUA" in jab else
                                (f"ANGGOTA {ak} {inst}" if ak else f"ANGGOTA {inst}"))
        if not keep_nip:
            self.ed_nip.setText(d["nip"] or "-")

    def _tgl_changed(self, *_):
        if self._loading:
            return
        if self.dt_kem.date() < self.dt_ber.date():
            self.dt_kem.setDate(self.dt_ber.date())
        self._changed()

    def _plafon(self, *_):
        r = P.plafon_tiket(self.cb_pa.currentText(), self.cb_pb.currentText())
        if r:
            self.lb_plafon.setText(f"Plafon tiket PP — Bisnis Rp {rp(r[0])}  ·  Ekonomi Rp {rp(r[1])}")
        else:
            self.lb_plafon.setText("Rute tidak tercantum di Tabel 2.2. Kepala Daerah dapat menetapkan standar; "
                                   "input tetap sesuai nota.")

    def add_leg(self, user=False, leg=None):
        w = LegWidget(len(self.legs) + 1)
        w.changed.connect(self._changed)
        w.removeRequested.connect(self.remove_leg)
        self.legs.append(w); self.legs_box.addWidget(w)
        if leg:
            w.load(leg)
        self._renumber()
        if user:
            self._changed()

    def remove_leg(self, w):
        if len(self.legs) <= 1:
            return
        self.legs.remove(w); w.setParent(None); w.deleteLater()
        self._renumber(); self._changed()

    def _renumber(self):
        for i, w in enumerate(self.legs, 1):
            w.set_index(i); w.set_removable(len(self.legs) > 1)

    def add_item(self, user=False, item=None):
        r = ItemRow()
        r.changed.connect(self._changed); r.removeRequested.connect(self.remove_item)
        self.rows.append(r); self.items_box.addWidget(r)
        if item:
            r.load(item)
        elif user and len(self.rows) == 1:
            r.cb.setCurrentText("Tiket Pesawat Pergi")
        if user:
            self._changed()

    def remove_item(self, r):
        self.rows.remove(r); r.setParent(None); r.deleteLater(); self._changed()

    def isi_taksi(self):
        try:
            asal = P.tarif_taksi(self.settings.provinsi_asal)
        except KeyError:
            asal = 0
        legs = [l.leg() for l in self.legs]
        tuj = P.tarif_taksi(legs[0].provinsi) if legs and legs[0].provinsi else 0
        for (q, h), tarif in zip(self.tr_rows[:2], (asal, tuj)):
            h.setValue(tarif)
            if q.value() == 0:
                q.setValue(2)

    # ---- kumpulkan & hitung
    def collect(self) -> Trip:
        d = self.cb_anggota.currentData() or {}
        return Trip(
            nama=d.get("nama", ""), nip=self.ed_nip.text().strip() or "-",
            kategori=self.cb_kat.currentData(), jabatan_dok=self.ed_jabatan.text().strip(),
            asal=self.ed_asal.text().strip() or self.settings.kota,
            tgl_berangkat=self.dt_ber.date().toPython(), tgl_kembali=self.dt_kem.date().toPython(),
            spt_no=self.ed_spt.text().strip(), spt_tgl=self.dt_spt.date().toPython(),
            spd_no=self.ed_spd.text().strip(), spd_tgl=self.dt_spd.date().toPython(),
            tgl_dokumen=self.dt_dok.date().toPython(), tujuan_teks=self.ed_tujuan.text(),
            sertakan_representasi=self.chk_repr.isChecked(),
            legs=[l.leg() for l in self.legs if l.leg().provinsi],
            items=[r.item() for r in self.rows],
            trans_riil=[TransRiil(TRANS_RIIL_LABEL[i], q.value(), h.value()) for i, (q, h) in enumerate(self.tr_rows)],
        )

    def _changed(self, *_):
        if not self._loading:
            self.refresh()

    def refresh(self):
        trip = self.collect()
        self.lb_lama.setText(f"{trip.lama} hari  ·  {max(trip.lama - 1, 0)} malam")
        if len(self.legs) == 1:
            self.legs[0].auto(trip.lama, max(trip.lama - 1, 0))
            trip = self.collect()
        for w in self.legs:
            w.refresh_info(trip.kategori)
        if not trip.legs:
            self._render_summary(None, trip)
            return
        self._render_summary(hitung(trip), trip)

    def _render_summary(self, res, trip):
        while self.sum_grid.count():
            it = self.sum_grid.takeAt(0)
            wdg = it.widget()
            if wdg:
                wdg.setParent(None)
                wdg.deleteLater()
        if res is None:
            self.lb_total.setText("Rp 0"); self.lb_warn.setText("Pilih minimal satu provinsi tujuan."); self.lb_warn.show()
            return
        biaya_transport_nota = sum(l.jumlah for l in res.items.get("Biaya Transportasi", []))
        rows = [("Uang harian", sum(l.jumlah for l in res.harian)),
                ("Uang representasi", sum(l.jumlah for l in res.representasi)),
                ("Hotel 30% (lumpsum)", sum(l.jumlah for l in res.hotel30)),
                ("  ↳ Subtotal Daftar Pengeluaran Riil", res.total_dp_riil),
                ("Hotel sesuai kwitansi", sum(l.jumlah for l in res.hotel_riil)),
                ("Tiket & biaya lain (nota)",
                 sum(l.jumlah for ls in res.items.values() for l in ls) - biaya_transport_nota),
                ("Biaya transportasi (khusus Kalkulasi)", res.total_transportasi)]
        for i, (a, b) in enumerate(rows):
            la = QLabel(a); la.setToolTip(a); lb = QLabel(f"Rp {rp(b)}"); lb.setAlignment(Qt.AlignRight)
            if a.strip().startswith("↳"):
                la.setStyleSheet("font-weight:600; font-size:8.5pt;"); lb.setStyleSheet("font-weight:600; font-size:8.5pt;")
            else:
                la.setProperty("cls", "muted")
            self.sum_grid.addWidget(la, i, 0); self.sum_grid.addWidget(lb, i, 1)
        n = len(rows)
        la = QLabel("Jumlah"); lb = QLabel(f"Rp {rp(res.total)}"); lb.setAlignment(Qt.AlignRight)
        la.setStyleSheet("font-weight:600"); lb.setStyleSheet("font-weight:600")
        self.sum_grid.addWidget(la, n, 0); self.sum_grid.addWidget(lb, n, 1)
        self.lb_total.setText(f"Rp {rp(bulatkan(res.total, self.settings.pembulatan))}")
        self.lb_warn.setText("\n\n".join("⚠ " + w for w in res.warnings))
        self.lb_warn.setVisible(bool(res.warnings))

    # ---- ekspor
    def _validate(self):
        trip = self.collect()
        if not trip.nama:
            QMessageBox.warning(self, "Data belum lengkap", "Pilih nama pelaksana perjalanan dinas."); return None
        if not trip.legs:
            QMessageBox.warning(self, "Data belum lengkap", "Pilih minimal satu provinsi tujuan."); return None
        res = hitung(trip)
        if res.warnings:
            m = QMessageBox(self); m.setIcon(QMessageBox.Question); m.setWindowTitle("Periksa kembali")
            m.setText("Ada peringatan pada perhitungan:\n\n" + "\n".join("• " + w for w in res.warnings)
                      + "\n\nTetap lanjut ekspor?")
            m.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            if m.exec() != QMessageBox.Yes:
                return None
        return trip

    def export(self, kind):
        trip = self._validate()
        if not trip:
            return
        nm = "".join(ch for ch in trip.nama.split(",")[0] if ch.isalnum() or ch == " ").strip().replace(" ", "_")
        default = f"SPJ_{nm}_{trip.tgl_berangkat:%Y%m%d}.{kind}"
        flt = "Excel (*.xlsx)" if kind == "xlsx" else "Word (*.docx)"
        path, _ = QFileDialog.getSaveFileName(self, "Simpan dokumen", os.path.join(os.path.expanduser("~"), "Documents", default), flt)
        if not path:
            return
        try:
            (export_xlsx if kind == "xlsx" else export_docx)(trip, self.settings, path)
        except PermissionError:
            QMessageBox.critical(self, "Gagal menyimpan", "File sedang dibuka di aplikasi lain. Tutup file lalu coba lagi.")
            return
        except Exception as e:                       # noqa
            QMessageBox.critical(self, "Gagal mengekspor", str(e)); return
        m = QMessageBox(self); m.setWindowTitle("Berhasil"); m.setText(f"Dokumen tersimpan:\n{path}")
        bo = m.addButton("Buka file", QMessageBox.AcceptRole); m.addButton("Tutup", QMessageBox.RejectRole)
        m.exec()
        if m.clickedButton() is bo:
            if sys.platform.startswith("win"):
                os.startfile(path)                   # noqa
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    # ---- draf
    def simpan_draf(self):
        trip = self.collect()
        path, _ = QFileDialog.getSaveFileName(self, "Simpan draf", "draf_spj.json", "Draf SPJ (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(trip.to_json())

    def buka_draf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Buka draf", "", "Draf SPJ (*.json)")
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                self.set_trip(Trip.from_json(f.read()))
        except Exception as e:                       # noqa
            QMessageBox.critical(self, "Draf tidak valid", str(e))

    def set_trip(self, t: Trip):
        self._loading = True
        for i in range(self.cb_anggota.count()):
            d = self.cb_anggota.itemData(i)
            if d and d["nama"] == t.nama:
                self.cb_anggota.setCurrentIndex(i)
        self.ed_jabatan.setText(t.jabatan_dok); self.ed_nip.setText(t.nip)
        self.cb_kat.setCurrentIndex(self.cb_kat.findData(t.kategori))
        self.ed_asal.setText(t.asal); self.ed_tujuan.setText(t.tujuan_teks)
        self.ed_spt.setText(t.spt_no); self.ed_spd.setText(t.spd_no)
        for w, d in ((self.dt_ber, t.tgl_berangkat), (self.dt_kem, t.tgl_kembali), (self.dt_spt, t.spt_tgl),
                     (self.dt_spd, t.spd_tgl), (self.dt_dok, t.tgl_dokumen)):
            w.setDate(qdate(d))
        self.chk_repr.setChecked(t.sertakan_representasi)
        for w in self.legs[:]:
            w.setParent(None); w.deleteLater()
        self.legs.clear()
        for lg in t.legs:
            self.add_leg(leg=lg)
        if not self.legs:
            self.add_leg()
        for r in self.rows[:]:
            r.setParent(None); r.deleteLater()
        self.rows.clear()
        for it in t.items:
            self.add_item(item=it)
        for (q, h), tr in zip(self.tr_rows, t.trans_riil):
            q.setValue(tr.qty); h.setValue(tr.harga)
        self._loading = False
        self.refresh()

    def reset(self):
        if QMessageBox.question(self, "Formulir baru", "Kosongkan semua isian?") != QMessageBox.Yes:
            return
        self.set_trip(Trip(asal=self.settings.kota))
        self.cb_anggota.setCurrentIndex(-1); self.cb_anggota.setCurrentText("")
        self.ed_jabatan.clear(); self.ed_nip.setText("-")
        self.refresh()
