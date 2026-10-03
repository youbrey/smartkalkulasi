from PySide6.QtCore import Qt, QLocale, Signal
from PySide6.QtWidgets import (QComboBox, QCompleter, QDateEdit, QFrame, QHBoxLayout,
                               QLabel, QSpinBox, QVBoxLayout, QWidget)

ID = QLocale(QLocale.Indonesian, QLocale.Indonesia)


def field(text):
    lb = QLabel(text)
    lb.setProperty("cls", "field")
    return lb


class Card(QFrame):
    def __init__(self, title, hint="", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(20, 18, 20, 18)
        self.lay.setSpacing(12)
        head = QVBoxLayout()
        head.setSpacing(2)
        t = QLabel(title); t.setObjectName("CardTitle")
        head.addWidget(t)
        if hint:
            h = QLabel(hint); h.setObjectName("CardHint"); h.setWordWrap(True)
            head.addWidget(h)
        self.lay.addLayout(head)

    def add(self, w):
        if isinstance(w, QWidget):
            self.lay.addWidget(w)
        else:
            self.lay.addLayout(w)


class RpSpin(QSpinBox):
    """Input rupiah dengan pemisah ribuan."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLocale(ID)
        self.setRange(0, 2_000_000_000)
        self.setGroupSeparatorShown(True)
        self.setPrefix("Rp ")
        self.setSingleStep(10_000)
        self.setButtonSymbols(QSpinBox.NoButtons)
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setKeyboardTracking(True)

    def wheelEvent(self, e):      # cegah nilai berubah saat scroll halaman
        e.ignore()


class NoWheelSpin(QSpinBox):
    def wheelEvent(self, e):
        e.ignore()


class NoWheelCombo(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.setMinimumContentsLength(8)

    def wheelEvent(self, e):
        e.ignore()


class SearchCombo(NoWheelCombo):
    """Combo dengan pencarian ketik (cocok sebagian kata)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self._comp = None

    def set_items(self, texts):
        self.clear()
        self.addItems(texts)
        self._comp = QCompleter(texts, self)
        self._comp.setFilterMode(Qt.MatchContains)
        self._comp.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(self._comp)
        self.setCurrentIndex(-1)


class DatePicker(QDateEdit):
    """Input tanggal yang wajib memakai kalender (klik dimana saja untuk membuka),
    tidak bisa diketik manual supaya format tanggal selalu benar."""
    def __init__(self, date=None, parent=None):
        from PySide6.QtCore import QDate as _QDate
        super().__init__(date or _QDate.currentDate(), parent)
        self.setLocale(ID)
        self.setCalendarPopup(True)
        self.setDisplayFormat("dd MMMM yyyy")
        self.setMinimumDate(_QDate(2015, 1, 1))
        self.setMaximumDate(_QDate(2100, 12, 31))
        self.lineEdit().setReadOnly(True)
        self.setToolTip("Klik untuk memilih tanggal dari kalender")
        cal = self.calendarWidget()
        cal.setLocale(ID)
        cal.setGridVisible(True)
        cal.setFirstDayOfWeek(Qt.Monday)

    def mousePressEvent(self, e):
        from PySide6.QtCore import QPointF
        from PySide6.QtGui import QMouseEvent
        self.setFocus()
        # Simulasikan klik tepat pada tombol panah kalender (ujung kanan),
        # supaya klik di mana saja pada kolom ini membuka kalender.
        pt = QPointF(max(self.width() - 10, 0), self.height() / 2)
        press = QMouseEvent(QMouseEvent.Type.MouseButtonPress, pt, self.mapToGlobal(pt.toPoint()).toPointF(),
                            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        release = QMouseEvent(QMouseEvent.Type.MouseButtonRelease, pt, self.mapToGlobal(pt.toPoint()).toPointF(),
                              Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        QDateEdit.mousePressEvent(self, press)
        QDateEdit.mouseReleaseEvent(self, release)

    def wheelEvent(self, e):
        e.ignore()
