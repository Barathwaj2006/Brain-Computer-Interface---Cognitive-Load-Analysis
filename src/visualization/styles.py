"""
NeuroSim Glassmorphism Dark Medical UI Stylesheet & Styling System
"""

from src.app.config import COLORS

MAIN_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
}}

QWidget {{
    font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
    color: {COLORS['text_primary']};
}}

/* Sidebar Navigation */
#SidebarWidget {{
    background-color: #0F172A;
    border-right: 1px solid #1E293B;
}}

QPushButton#NavButton {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    font-size: 13px;
    font-weight: 600;
    text-align: left;
    padding: 12px 18px;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0px;
}}

QPushButton#NavButton:hover {{
    background-color: #1E293B;
    color: {COLORS['text_primary']};
}}

QPushButton#NavButton:checked {{
    background-color: #1E293B;
    color: {COLORS['accent_cyan']};
    border-left: 3px solid {COLORS['accent_cyan']};
}}

/* Cards & Glass Panels */
QFrame.GlassCard {{
    background-color: rgba(21, 29, 42, 0.95);
    border: 1px solid #1E293B;
    border-radius: 12px;
}}

QFrame.GlassCard:hover {{
    border: 1px solid #334155;
}}

/* Action Buttons */
QPushButton.PrimaryBtn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06B6D4, stop:1 #0284C7);
    color: #FFFFFF;
    font-weight: bold;
    font-size: 13px;
    padding: 10px 20px;
    border-radius: 8px;
    border: none;
}}

QPushButton.PrimaryBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #22D3EE, stop:1 #0369A1);
}}

QPushButton.SecondaryBtn {{
    background-color: #1E293B;
    color: {COLORS['text_primary']};
    font-weight: 600;
    font-size: 13px;
    padding: 10px 20px;
    border-radius: 8px;
    border: 1px solid #334155;
}}

QPushButton.SecondaryBtn:hover {{
    background-color: #334155;
}}

QPushButton.DangerBtn {{
    background-color: #EF4444;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 13px;
    padding: 10px 20px;
    border-radius: 8px;
    border: none;
}}

QPushButton.DangerBtn:hover {{
    background-color: #DC2626;
}}

/* Sliders */
QSlider::groove:horizontal {{
    height: 6px;
    background: #1E293B;
    border-radius: 3px;
}}

QSlider::sub-page:horizontal {{
    background: {COLORS['accent_cyan']};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: #F8FAFC;
    border: 2px solid {COLORS['accent_cyan']};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

/* Table View */
QTableWidget {{
    background-color: #151D2A;
    gridline-color: #1E293B;
    border: 1px solid #1E293B;
    border-radius: 8px;
    color: #F8FAFC;
}}

QHeaderView::section {{
    background-color: #0F172A;
    color: #94A3B8;
    padding: 8px;
    font-weight: bold;
    border: none;
    border-bottom: 1px solid #1E293B;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: #0B0F19;
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: #334155;
    border-radius: 4px;
}}
"""
