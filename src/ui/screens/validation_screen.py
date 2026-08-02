"""
Validation Center Screen Module
Executes automated DSP self-tests across Delta (2Hz), Theta (6Hz), Alpha (10Hz), and Beta (20Hz).
Outputs target vs detected frequency, frequency error (Hz), band match, and PASS/FAIL verdict.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
from src.processing.psd import PSDAnalyzer
from src.app.config import COLOR_CARD_BG, COLOR_CYAN, COLOR_EMERALD, COLOR_ROSE

class ValidationScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analyzer = PSDAnalyzer()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px;")
        h_layout = QHBoxLayout(header_card)
        
        v_title_box = QVBoxLayout()
        v_title = QLabel("SYSTEM VALIDATION CENTER — AUTOMATED DSP VERIFICATION")
        v_title.setStyleSheet("font-size: 15px; font-weight: 900; color: #F8FAFC; letter-spacing: 1px;")
        v_sub = QLabel("Executes frequency accuracy tests to prove signal filtering, FFT PSD, and band classification precision.")
        v_sub.setStyleSheet("font-size: 11px; color: #94A3B8;")
        v_title_box.addWidget(v_title)
        v_title_box.addWidget(v_sub)

        self.btn_run_all = QPushButton("⚡ RUN ALL VALIDATION TESTS")
        self.btn_run_all.setStyleSheet("background: linear-gradient(135deg, #06B6D4, #0284C7); color: white; font-weight: 800; font-size: 12px; padding: 12px 20px; border-radius: 8px; border: none;")
        self.btn_run_all.setCursor(Qt.PointingHandCursor)
        self.btn_run_all.clicked.connect(self.run_all_tests)

        h_layout.addLayout(v_title_box)
        h_layout.addStretch()
        h_layout.addWidget(self.btn_run_all)
        
        layout.addWidget(header_card)

        # Test Results Table
        table_card = QFrame()
        table_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px;")
        t_layout = QVBoxLayout(table_card)

        self.table = QTableWidget(4, 6)
        self.table.setHorizontalHeaderLabels([
            "Test Frequency", "Target (Hz)", "Detected Peak (Hz)", "Expected Band", "Detected Band", "Verdict"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background: transparent; border: none; gridline-color: rgba(255,255,255,0.05); color: #F8FAFC; font-size: 12px; }
            QHeaderView::section { background: rgba(15,23,42,0.8); color: #94A3B8; font-weight: 800; font-size: 11px; padding: 8px; border: none; }
        """)

        t_layout.addWidget(self.table)
        layout.addWidget(table_card)

        self.populate_default_table()

    def populate_default_table(self):
        bands = [("Delta Test", "2.00 Hz", "—", "DELTA", "—", "PENDING"),
                 ("Theta Test", "6.00 Hz", "—", "THETA", "—", "PENDING"),
                 ("Alpha Test", "10.00 Hz", "—", "ALPHA", "—", "PENDING"),
                 ("Beta Test", "20.00 Hz", "—", "BETA", "—", "PENDING")]
        
        for row, b in enumerate(bands):
            for col, text in enumerate(b):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

    def run_all_tests(self):
        test_bands = ['delta', 'theta', 'alpha', 'beta']
        for row, b in enumerate(test_bands):
            res = self.analyzer.run_validation_test(b)
            
            self.table.setItem(row, 0, QTableWidgetItem(f"{b.upper()} TEST"))
            self.table.setItem(row, 1, QTableWidgetItem(f"{res['target_frequency_hz']:.2f} Hz"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{res['detected_frequency_hz']:.2f} Hz"))
            self.table.setItem(row, 3, QTableWidgetItem(b.upper()))
            self.table.setItem(row, 4, QTableWidgetItem(res['detected_band']))

            verdict_item = QTableWidgetItem(f"✓ {res['result']}")
            verdict_item.setTextAlignment(Qt.AlignCenter)
            if res['passed']:
                verdict_item.setForeground(Qt.green)
            else:
                verdict_item.setForeground(Qt.red)
            self.table.setItem(row, 5, verdict_item)
