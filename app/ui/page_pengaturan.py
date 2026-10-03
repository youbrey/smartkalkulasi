from dataclasses import replace

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QComboBox, QGridLayout, QLabel, QLineEdit, QMessageBox,
                               QPushButton, QScrollArea, QVBoxLayout, QWidget)

from .. import data_perpres as P
from ..calc import Settings
from ..db import Database
from .widgets import Card, field


class PengaturanPage(QWidget):
    saved = Signal(object)

    def __init__(self, db: Database, st: Settings):
        super().__init__()
        self.db, self.st = db, st
        v = QVBoxLayout(self); v.setContentsMargins(28, 22, 28, 22); v.setSpacing(6)
        t = QLabel("Pengaturan"); t.setObjectName("PageTitle")
        s = QLabel("Identitas instansi dan pejabat penanda tangan yang tercetak pada dokumen."); s.setObjectName("PageSub")
        v.addWidget(t); v.addWidget(s); v.addSpacing(8)
        sc = QScrollArea(); sc.setWidgetResizable(True); v.addWidget(sc, 1)
        inner = QWidget(); col = QVBoxLayout(inner); col.setSpacing(16); sc.setWidget(inner)

        c = Card("Instansi")
        g = QGridLayout(); g.setHorizontalSpacing(12); g.setVerticalSpacing(6)
        self.ed_kota = QLineEdit(st.kota); self.ed_inst = QLineEdit(st.instansi)
        self.cb_prov = QComboBox(); self.cb_prov.addItems(P.DAFTAR_PROVINSI); self.cb_prov.setCurrentText(st.provinsi_asal)
        g.addWidget(field("Kota (untuk tanggal & kota asal)"), 0, 0); g.addWidget(field("Nama instansi pada jabatan"), 0, 1)
        g.addWidget(self.ed_kota, 1, 0); g.addWidget(self.ed_inst, 1, 1)
        g.addWidget(field("Provinsi asal (untuk tarif taksi otomatis)"), 2, 0, 1, 2); g.addWidget(self.cb_prov, 3, 0, 1, 2)
        c.add(g); col.addWidget(c)

        c = Card("Mengetahui / menyetujui")
        g = QGridLayout(); g.setHorizontalSpacing(12); g.setVerticalSpacing(6)
        self.sj = QLineEdit(st.sekwan_jabatan); self.sn = QLineEdit(st.sekwan_nama); self.sp = QLineEdit(st.sekwan_nip)
        for i, (lab, w) in enumerate((("Jabatan", self.sj), ("Nama", self.sn), ("NIP", self.sp))):
            g.addWidget(field(lab), i * 2, 0); g.addWidget(w, i * 2 + 1, 0)
        c.add(g); col.addWidget(c)

        c = Card("Pejabat pelaksana teknis kegiatan (PPTK)")
        g = QGridLayout(); g.setHorizontalSpacing(12); g.setVerticalSpacing(6)
        self.pj = QLineEdit(st.pptk_jabatan); self.pn = QLineEdit(st.pptk_nama); self.pp = QLineEdit(st.pptk_nip)
        for i, (lab, w) in enumerate((("Jabatan", self.pj), ("Nama", self.pn), ("NIP", self.pp))):
            g.addWidget(field(lab), i * 2, 0); g.addWidget(w, i * 2 + 1, 0)
        c.add(g); col.addWidget(c)

        c = Card("Pembulatan total", "Diterapkan pada baris 'Dibulatkan' di lembar KALKULASI.")
        self.cb_bulat = QComboBox()
        for k, lab in (("NEAREST", "Ke ribuan terdekat"), ("UP", "Ke atas (ribuan)"), ("NONE", "Tanpa pembulatan")):
            self.cb_bulat.addItem(lab, k)
        self.cb_bulat.setCurrentIndex(self.cb_bulat.findData(st.pembulatan))
        c.add(self.cb_bulat); col.addWidget(c)
        col.addStretch(1)

        b = QPushButton("Simpan pengaturan"); b.setProperty("kind", "primary"); b.clicked.connect(self.simpan)
        v.addWidget(b)

    def simpan(self):
        st = Settings(kota=self.ed_kota.text().strip().upper(), provinsi_asal=self.cb_prov.currentText(),
                      instansi=self.ed_inst.text().strip().upper(),
                      sekwan_jabatan=self.sj.text().strip(), sekwan_nama=self.sn.text().strip(), sekwan_nip=self.sp.text().strip(),
                      pptk_jabatan=self.pj.text().strip(), pptk_nama=self.pn.text().strip(), pptk_nip=self.pp.text().strip(),
                      pembulatan=self.cb_bulat.currentData())
        self.db.simpan_pengaturan(st)
        self.saved.emit(st)
        QMessageBox.information(self, "Tersimpan", "Pengaturan disimpan.")
