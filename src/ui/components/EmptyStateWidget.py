"""
Empty State Component
Displays professional empty states when no sessions, reports, or data exist.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt, Signal
from src.app.config import COLOR_CARD_BG, COLOR_BORDER, COLOR_CYAN, COLOR_TEXT_MUTED

class EmptyStateWidget(QFrame):
    action_requested = Signal()

    def __init__(self, title="NO DATA RECORDED", description="Start an analysis session to record neural data.", button_text="START SESSION", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CARD_BG};
                border: 1px dashed {COLOR_BORDER};
                border-radius: 12px;
                padding: 30px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        icon_lbl = QLabel("📂")
        icon_lbl.setStyleSheet("font-size: 36px; color: #9CA3AF;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #F9FAFB; letter-spacing: 1px;")
        title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED}; max-width: 400px;")
        desc_lbl.setWordWrap(True)
        desc_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_lbl)

        if button_text:
            btn = QPushButton(button_text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0EA5E9, stop:1 #0284C7);
                    color: white;
                    font-weight: 800;
                    font-size: 12px;
                    padding: 10px 24px;
                    border-radius: 6px;
                    border: none;
                    margin-top: 8px;
                }}
                QPushButton:hover {{ background: #0284C7; }}
            """)
            btn.clicked.connect(self.action_requested.emit)
            layout.addWidget(btn, alignment=Qt.AlignCenter)
