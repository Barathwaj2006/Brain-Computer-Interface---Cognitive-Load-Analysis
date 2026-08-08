"""
Error State Component
Displays user-friendly error banners and recovery options without showing raw tracebacks.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from src.app.config import COLOR_CARD_BG, COLOR_ROSE, COLOR_TEXT_MUTED

class ErrorStateWidget(QFrame):
    retry_requested = Signal()
    fallback_requested = Signal()

    def __init__(self, title="CONNECTION / EXECUTION ERROR", message="An unexpected error occurred during processing.", retry_text="RETRY", fallback_text="USE SIMULATOR", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(239, 68, 68, 0.08);
                border: 1px solid {COLOR_ROSE};
                border-radius: 10px;
                padding: 20px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        h_head = QHBoxLayout()
        icon_lbl = QLabel("⚠️")
        icon_lbl.setStyleSheet("font-size: 20px;")
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {COLOR_ROSE}; letter-spacing: 1px;")

        h_head.addWidget(icon_lbl)
        h_head.addWidget(t_lbl)
        h_head.addStretch()
        layout.addLayout(h_head)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet("font-size: 12px; color: #F9FAFB;")
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        if retry_text:
            btn_retry = QPushButton(retry_text)
            btn_retry.setStyleSheet(f"""
                QPushButton {{
                    background: {COLOR_ROSE};
                    color: white;
                    font-weight: 800;
                    font-size: 11px;
                    padding: 8px 16px;
                    border-radius: 6px;
                    border: none;
                }}
                QPushButton:hover {{ background: #DC2626; }}
            """)
            btn_retry.clicked.connect(self.retry_requested.emit)
            btn_layout.addWidget(btn_retry)

        if fallback_text:
            btn_fallback = QPushButton(fallback_text)
            btn_fallback.setStyleSheet("""
                QPushButton {
                    background: #1F2937;
                    color: #F9FAFB;
                    font-weight: 700;
                    font-size: 11px;
                    padding: 8px 16px;
                    border-radius: 6px;
                    border: 1px solid #374151;
                }
                QPushButton:hover { background: #374151; }
            """)
            btn_fallback.clicked.connect(self.fallback_requested.emit)
            btn_layout.addWidget(btn_fallback)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)
