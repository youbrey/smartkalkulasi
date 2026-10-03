from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QButtonGroup, QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QStackedWidget, QVBoxLayout, QWidget)

from ..db import Database
from .page_anggota import AnggotaPage
from .page_form import FormPage
from .page_pengaturan import PengaturanPage
from .page_referensi import ReferensiPage
from .theme import QSS


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.setWindowTitle("Kalkulasi SPJ Perjalanan Dinas DPRD")
        self.resize(1360, 860)
        self.setMinimumSize(1180, 700)
        self.setStyleSheet(QSS)
        self.db = db
        st = db.muat_pengaturan()

        central = QWidget(); self.setCentralWidget(central)
        root = QHBoxLayout(central); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        side = QWidget(); side.setObjectName("Sidebar"); side.setFixedWidth(210)
        sv = QVBoxLayout(side); sv.setContentsMargins(16, 22, 16, 16); sv.setSpacing(4)
        b = QLabel("Kalkulasi SPJ"); b.setObjectName("Brand")
        bs = QLabel("Perpres 72/2025"); bs.setObjectName("BrandSub")
        sv.addWidget(b); sv.addWidget(bs); sv.addSpacing(22)

        self.stack = QStackedWidget()
        self.form = FormPage(db, st)
        self.anggota = AnggotaPage(db)
        self.ref = ReferensiPage()
        self.set = PengaturanPage(db, st)
        pages = [("Buat SPJ", self.form), ("Data Anggota", self.anggota),
                 ("Database Perpres", self.ref), ("Pengaturan", self.set)]
        grp = QButtonGroup(self); grp.setExclusive(True)
        for i, (name, w) in enumerate(pages):
            btn = QPushButton(name); btn.setObjectName("Nav"); btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            grp.addButton(btn, i); sv.addWidget(btn); self.stack.addWidget(w)
            if i == 0:
                btn.setChecked(True)
        grp.idClicked.connect(self.stack.setCurrentIndex)
        sv.addStretch(1)
        ver = QLabel("v1.0"); ver.setObjectName("BrandSub"); sv.addWidget(ver)

        root.addWidget(side); root.addWidget(self.stack, 1)

        self.anggota.changed.connect(self.form.reload_anggota)
        self.set.saved.connect(self.form.apply_settings)
