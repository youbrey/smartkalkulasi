from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QHeaderView, QLabel, QLineEdit, QTabWidget,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from .. import data_perpres as P
from ..calc import rp


def make_table(headers, rows, money_from=1):
    tb = QTableWidget(len(rows), len(headers))
    tb.setHorizontalHeaderLabels(headers)
    tb.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tb.setSelectionBehavior(QAbstractItemView.SelectRows)
    tb.setAlternatingRowColors(True); tb.verticalHeader().setVisible(False); tb.setShowGrid(False)
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            if isinstance(v, int) and j >= money_from:
                it = QTableWidgetItem(f"Rp {rp(v)}"); it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            else:
                it = QTableWidgetItem(str(v))
            tb.setItem(i, j, it)
        tb.setRowHeight(i, 32)
    hh = tb.horizontalHeader()
    hh.setSectionResizeMode(QHeaderView.Stretch)
    return tb


class ReferensiPage(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self); v.setContentsMargins(28, 22, 28, 22); v.setSpacing(6)
        t = QLabel("Database Satuan Biaya · Perpres 72/2025"); t.setObjectName("PageTitle")
        s = QLabel("Data referensi (hanya baca) yang dipakai mesin perhitungan. Sumber: lampiran Perpres Nomor 72 Tahun 2025.")
        s.setObjectName("PageSub")
        v.addWidget(t); v.addWidget(s); v.addSpacing(8)
        self.search = QLineEdit(); self.search.setPlaceholderText("Cari provinsi / kota…")
        self.search.textChanged.connect(self._filter)
        v.addWidget(self.search)
        self.tabs = QTabWidget()
        v.addWidget(self.tabs, 1)
        pv = P.PROVINSI
        self._add("Uang harian (T 1.2)", ["Provinsi", "Luar kota", "Dalam kota > 8 jam", "Diklat"],
                  [(p[0], p[1], p[2], p[3]) for p in pv])
        self._add("Penginapan (T 1.4)", ["Provinsi", "Pimpinan DPRD / Eselon I", "Anggota DPRD / Eselon II",
                                          "Eselon III / Gol IV", "Eselon IV / Gol III, II, I"],
                  [(p[0], p[5], p[6], p[7], p[8]) for p in pv])
        self._add("Representasi (T 1.3)", ["Penerima", "Luar kota", "Dalam kota > 8 jam"],
                  [(k, a, b) for k, (a, b) in P.REPRESENTASI.items()])
        self._add("Taksi (T 2.3)", ["Provinsi", "Per orang / kali"], [(p[0], p[4]) for p in pv])
        self._add("Tiket pesawat PP (T 2.2)", ["Kota asal", "Kota tujuan", "Bisnis", "Ekonomi"],
                  P.TIKET_PESAWAT, money_from=2)
        note = QLabel("Hotel: biaya penginapan berlaku at cost; bila tidak menginap diberikan lumpsum setinggi-tingginya "
                      "30% dari tarif kota tujuan. Tarif Tabel 2.4 & 2.5 (transportasi darat) belum dimuat — "
                      "input sesuai nota.")
        note.setObjectName("Info"); note.setWordWrap(True)
        v.addWidget(note)

    def _add(self, name, headers, rows, money_from=1):
        tb = make_table(headers, rows, money_from)
        self.tabs.addTab(tb, name)

    def _filter(self):
        q = self.search.text().strip().lower()
        tb = self.tabs.currentWidget()
        for i in range(tb.rowCount()):
            txt = " ".join(tb.item(i, j).text().lower() for j in range(min(2, tb.columnCount())))
            tb.setRowHidden(i, bool(q) and q not in txt)
