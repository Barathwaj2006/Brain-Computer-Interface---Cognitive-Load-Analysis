"""
Sidebar Navigation Component
Collapsible scientific sidebar featuring 7 primary categories and research sub-navigation.
"""

import os
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from src.app.config import COLOR_SIDEBAR_BG, COLOR_BORDER, COLOR_CYAN, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED

class Sidebar(QFrame):
    page_changed = Signal(int)  # Screen index in StackedWidget

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarWidget")
        self.is_collapsed = False
        self.setFixedWidth(240)
        self.setStyleSheet(f"""
            QFrame#SidebarWidget {{
                background-color: {COLOR_SIDEBAR_BG};
                border-right: 1px solid {COLOR_BORDER};
            }}
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(10)

        # Collapse / Expand Toggle Button
        h_toggle = QHBoxLayout()
        self.lbl_nav_title = QLabel("NAVIGATION")
        self.lbl_nav_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #6B7280; letter-spacing: 1px;")
        
        self.btn_toggle = QPushButton("◀")
        self.btn_toggle.setFixedSize(24, 24)
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background: #1F2937;
                color: #9CA3AF;
                border: 1px solid #374151;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background: #374151; color: #F9FAFB; }
        """)
        self.btn_toggle.clicked.connect(self.toggle_sidebar)

        h_toggle.addWidget(self.lbl_nav_title)
        h_toggle.addStretch()
        h_toggle.addWidget(self.btn_toggle)
        layout.addLayout(h_toggle)

        # Navigation Tree / List
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 10px 10px;
                border-radius: 6px;
                color: #9CA3AF;
                font-weight: 700;
                font-size: 12px;
                margin-bottom: 2px;
            }}
            QTreeWidget::item:hover {{
                background: rgba(14, 165, 233, 0.08);
                color: #F9FAFB;
            }}
            QTreeWidget::item:selected {{
                background: rgba(14, 165, 233, 0.15);
                color: {COLOR_CYAN};
                font-weight: 900;
            }}
        """)

        # Mapping screen names to stacked widget index
        self.screen_map = {}

        # Item 0: Overview
        item_overview = QTreeWidgetItem(["📊  Overview"])
        item_overview.setData(0, Qt.UserRole, 0)
        self.tree.addTopLevelItem(item_overview)

        # Item 1: Live Monitor
        item_monitor = QTreeWidgetItem(["📈  Live Monitor"])
        item_monitor.setData(0, Qt.UserRole, 1)
        self.tree.addTopLevelItem(item_monitor)

        # Item 2: Analysis (Results & Band Breakdown)
        item_analysis = QTreeWidgetItem(["🧠  Analysis & Results"])
        item_analysis.setData(0, Qt.UserRole, 12)  # Results Platform
        self.tree.addTopLevelItem(item_analysis)

        # Item 3: Sessions
        item_sessions = QTreeWidgetItem(["⏱️  Sessions"])
        item_sessions.setData(0, Qt.UserRole, 5)   # Session Control
        self.tree.addTopLevelItem(item_sessions)

        # Item 4: Reports
        item_reports = QTreeWidgetItem(["📄  Reports & AI"])
        item_reports.setData(0, Qt.UserRole, 7)    # Reports Screen
        self.tree.addTopLevelItem(item_reports)

        # Item 5: Research (Expandable Sub-Menu)
        item_research = QTreeWidgetItem(["🔬  Research Suite"])
        item_research.setData(0, Qt.UserRole, 2)   # Default Signal Lab
        
        child_lab = QTreeWidgetItem(["🧪  Signal Lab Pipeline"])
        child_lab.setData(0, Qt.UserRole, 2)
        
        child_val = QTreeWidgetItem(["✅  Validation Center"])
        child_val.setData(0, Qt.UserRole, 8)

        child_arch = QTreeWidgetItem(["🏛️  Architecture"])
        child_arch.setData(0, Qt.UserRole, 9)

        child_diag = QTreeWidgetItem(["🎛️  Device & Diagnostics"])
        child_diag.setData(0, Qt.UserRole, 11)  # Hardware Screen

        child_exp = QTreeWidgetItem(["🔬  Experiments & Compare"])
        child_exp.setData(0, Qt.UserRole, 4)

        item_research.addChild(child_lab)
        item_research.addChild(child_val)
        item_research.addChild(child_arch)
        item_research.addChild(child_diag)
        item_research.addChild(child_exp)

        self.tree.addTopLevelItem(item_research)
        item_research.setExpanded(True)

        # Item 6: Settings
        item_settings = QTreeWidgetItem(["⚙️  Settings & About"])
        item_settings.setData(0, Qt.UserRole, 13)
        self.tree.addTopLevelItem(item_settings)

        self.tree.setCurrentItem(item_overview)
        self.tree.itemClicked.connect(self.on_item_clicked)

        layout.addWidget(self.tree)
        layout.addStretch()

        # Presentation Mode Quick CTA
        self.btn_presentation = QPushButton("⚡ RESEARCH DEMO MODE")
        self.btn_presentation.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0EA5E9, stop:1 #0284C7);
                color: white;
                font-weight: 800;
                font-size: 11px;
                padding: 10px;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{ background: #0284C7; }}
        """)
        self.btn_presentation.clicked.connect(lambda: self.page_changed.emit(14))
        layout.addWidget(self.btn_presentation)

    def on_item_clicked(self, item, column):
        screen_idx = item.data(0, Qt.UserRole)
        if screen_idx is not None:
            self.page_changed.emit(screen_idx)

    def select_screen(self, screen_idx):
        # Programmatically set current tree selection
        for i in range(self.tree.topLevelItemCount()):
            top_item = self.tree.topLevelItem(i)
            if top_item.data(0, Qt.UserRole) == screen_idx:
                self.tree.setCurrentItem(top_item)
                return
            for j in range(top_item.childCount()):
                child = top_item.child(j)
                if child.data(0, Qt.UserRole) == screen_idx:
                    self.tree.setCurrentItem(child)
                    return

    def toggle_sidebar(self):
        if self.is_collapsed:
            self.setFixedWidth(240)
            self.btn_toggle.setText("◀")
            self.lbl_nav_title.show()
            self.btn_presentation.setText("⚡ RESEARCH DEMO MODE")
            self.is_collapsed = False
        else:
            self.setFixedWidth(64)
            self.btn_toggle.setText("▶")
            self.lbl_nav_title.hide()
            self.btn_presentation.setText("⚡")
            self.is_collapsed = True
