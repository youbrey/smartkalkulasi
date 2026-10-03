import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app.db import Database
from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Kalkulasi SPJ")
    app.setStyle("Fusion")
    f = QFont("Segoe UI", 10)
    app.setFont(f)
    win = MainWindow(Database())
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
