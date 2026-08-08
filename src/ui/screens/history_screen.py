"""
Session History Archive Screen Module
Interactive SQLite database session browser with review, report export capabilities,
light theme styling, and empty state placeholder handling.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from src.app.config import COLORS
from src.database.db_manager import DatabaseManager

class HistoryScreen(QWidget):
    open_session_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("RECORDED SESSION HISTORY (SQLITE DATABASE)")
        title.setStyleSheet("font-size: 16px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        
        self.refresh_btn = QPushButton("🔄 REFRESH HISTORY")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: #F1F5F9;
                color: #0F172A;
                font-weight: 700;
                font-size: 11px;
                padding: 8px 16px;
                border-radius: 6px;
                border: 1px solid #CBD5E1;
            }
            QPushButton:hover { background: #E2E8F0; }
        """)
        self.refresh_btn.clicked.connect(self.load_history)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # Empty State Placeholder Label
        self.empty_card = QFrame()
        self.empty_card.setStyleSheet("background: #FFFFFF; border: 1px dashed #CBD5E1; border-radius: 10px; padding: 40px;")
        ec_layout = QVBoxLayout(self.empty_card)
        ec_layout.setAlignment(Qt.AlignCenter)
        
        icon_lbl = QLabel("📂")
        icon_lbl.setStyleSheet("font-size: 32px; margin-bottom: 8px;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        
        empty_lbl = QLabel("No recorded sessions found in database.\nStart an analysis session to record and archive session telemetry.")
        empty_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #64748B;")
        empty_lbl.setAlignment(Qt.AlignCenter)

        ec_layout.addWidget(icon_lbl)
        ec_layout.addWidget(empty_lbl)
        layout.addWidget(self.empty_card)
        self.empty_card.hide()

        # Sessions Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Session ID", "Timestamp", "Duration (s)", "Mode", "Dominant Band", "Cognitive State", "Stress Index", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: #F8FAFC;
                gridline-color: #E2E8F0;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                color: #0F172A;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #475569;
                font-weight: 800;
                font-size: 11px;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #E2E8F0;
            }
        """)

        layout.addWidget(self.table)
        self.load_history()

    def load_history(self):
        sessions = self.db.get_all_sessions()
        
        if len(sessions) == 0:
            self.table.hide()
            self.empty_card.show()
            return

        self.empty_card.hide()
        self.table.show()
        self.table.setRowCount(len(sessions))

        for row_idx, sess in enumerate(sessions):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(sess.get('session_id', 'N/A'))))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(sess.get('timestamp', 'N/A'))))
            self.table.setItem(row_idx, 2, QTableWidgetItem(f"{float(sess.get('duration', 0.0)):.1f}"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(sess.get('mode', 'SIMULATION'))))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(sess.get('dominant_band', 'ALPHA'))))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(sess.get('cognitive_state', 'MODERATE'))))
            self.table.setItem(row_idx, 6, QTableWidgetItem(f"{float(sess.get('stress_index', 0.5)):.2f}"))

            # Action Button Widget
            btn_box = QWidget()
            btn_layout = QHBoxLayout(btn_box)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            
            view_btn = QPushButton("REVIEW")
            view_btn.setStyleSheet("background: #0284C7; color: white; font-weight: bold; font-size: 10px; padding: 4px 10px; border-radius: 4px; border: none;")
            view_btn.clicked.connect(lambda _, s=sess: self.open_session_requested.emit(s))

            del_btn = QPushButton("DELETE")
            del_btn.setStyleSheet("background: #E11D48; color: white; font-weight: bold; font-size: 10px; padding: 4px 10px; border-radius: 4px; border: none;")
            del_btn.clicked.connect(lambda _, sid=sess.get('session_id'): self._delete(sid))

            btn_layout.addWidget(view_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(row_idx, 7, btn_box)

    def _delete(self, session_id: str):
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete session {session_id}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_session(session_id)
            self.load_history()
