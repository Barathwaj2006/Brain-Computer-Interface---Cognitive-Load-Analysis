"""
NeuroSim Main Application Entry Point
Initializes PySide6 QApplication, applies dark glassmorphism stylesheet, and launches MainWindow.
"""

import sys
import os

# Ensure src parent directory is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.visualization.styles import MAIN_STYLESHEET
from src.ui.main_window import MainWindow

def main():
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setStyleSheet(MAIN_STYLESHEET)
    app.setApplicationName("NeuroSim")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
