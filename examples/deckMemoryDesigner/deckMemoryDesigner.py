#!/usr/bin/env python3

import sys
from PyQt5 import QtCore, QtWidgets, uic


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('deckMemoryDesigner.ui', self)
        self.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
