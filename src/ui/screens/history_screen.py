"""
Screen 8 — Session History Archive Screen
Interactive SQLite database session browser with review and report export capabilities.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from src.app.config import COLORS
from src.database.db_manager import DatabaseManager
from src.visualization.custom_widgets import GlassCard

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
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        
        self.refresh_btn = QPushButton("🔄 REFRESH HISTORY")
        self.refresh_btn.setProperty("class", "SecondaryBtn")
        self.refresh_btn.clicked.connect(self.load_history)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # Sessions Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Session ID", "Timestamp", "Duration (s)", "Mode", "Dominant Band", "Cognitive State", "Stress Index", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #151D2A;
                alternate-background-color: #0F172A;
                gridline-color: #1E293B;
                border: 1px solid #1E293B;
                border-radius: 8px;
            }}
        """)

        layout.addWidget(self.table)
        self.load_history()

    def load_history(self):
        sessions = self.db.get_all_sessions()
        self.table.setRowCount(len(sessions))

        for row_idx, sess in enumerate(sessions):
            self.table.setItem(row_idx, 0, QTableWidgetItem(sess['session_id']))
            self.table.setItem(row_idx, 1, QTableWidgetItem(sess['timestamp']))
            self.table.setItem(row_idx, 2, QTableWidgetItem(f"{sess['duration']:.1f}"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(sess['mode']))
            self.table.setItem(row_idx, 4, QTableWidgetItem(sess['dominant_band']))
            self.table.setItem(row_idx, 5, QTableWidgetItem(sess['cognitive_state']))
            self.table.setItem(row_idx, 6, QTableWidgetItem(f"{sess['stress_index']:.2f}"))

            # Action Button Widget
            btn_box = QWidget()
            btn_layout = QHBoxLayout(btn_box)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            
            view_btn = QPushButton("REVIEW")
            view_btn.setProperty("class", "PrimaryBtn")
            view_btn.setStyleSheet("font-size: 10px; padding: 4px 8px;")
            view_btn.clicked.connect(lambda _, s=sess: self.open_session_requested.emit(s))

            del_btn = QPushButton("DELETE")
            del_btn.setProperty("class", "DangerBtn")
            del_btn.setStyleSheet("font-size: 10px; padding: 4px 8px;")
            del_btn.clicked.connect(lambda _, sid=sess['session_id']: self._delete(sid))

            btn_layout.addWidget(view_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(row_idx, 7, btn_box)

    def _delete(self, session_id: str):
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete session {session_id}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_session(session_id)
            self.load_history()
