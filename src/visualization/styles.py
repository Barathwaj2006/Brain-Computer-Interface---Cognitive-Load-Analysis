"""
NeuroSim Bright Frosted Glassmorphism Medical UI Stylesheet & Styling System
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
    background-color: #FFFFFF;
    border-right: 1px solid #E2E8F0;
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
    background-color: rgba(2, 132, 199, 0.06);
    color: {COLORS['text_primary']};
}}

QPushButton#NavButton:checked {{
    background-color: rgba(2, 132, 199, 0.12);
    color: {COLORS['accent_cyan']};
    font-weight: bold;
    border-left: 3px solid {COLORS['accent_cyan']};
}}

/* Cards & Glass Panels */
QFrame.GlassCard {{
    background-color: rgba(255, 255, 255, 0.85);
    border: 1px solid rgba(226, 232, 240, 0.9);
    border-radius: 12px;
}}

QFrame.GlassCard:hover {{
    border: 1px solid {COLORS['accent_cyan']};
}}

/* Action Buttons */
QPushButton.PrimaryBtn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284C7, stop:1 #0369A1);
    color: #FFFFFF;
    font-weight: bold;
    font-size: 13px;
    padding: 10px 20px;
    border-radius: 8px;
    border: none;
}}

QPushButton.PrimaryBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369A1, stop:1 #075985);
}}

QPushButton.SecondaryBtn {{
    background-color: #F1F5F9;
    color: {COLORS['text_primary']};
    font-weight: 600;
    font-size: 13px;
    padding: 10px 20px;
    border-radius: 8px;
    border: 1px solid #CBD5E1;
}}

QPushButton.SecondaryBtn:hover {{
    background-color: #E2E8F0;
}}

QPushButton.DangerBtn {{
    background-color: #E11D48;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 13px;
    padding: 10px 20px;
    border-radius: 8px;
    border: none;
}}

QPushButton.DangerBtn:hover {{
    background-color: #BE123C;
}}

/* Sliders */
QSlider::groove:horizontal {{
    height: 6px;
    background: #E2E8F0;
    border-radius: 3px;
}}

QSlider::sub-page:horizontal {{
    background: {COLORS['accent_cyan']};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: #FFFFFF;
    border: 2px solid {COLORS['accent_cyan']};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

/* Table View */
QTableWidget {{
    background-color: #FFFFFF;
    gridline-color: #E2E8F0;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    color: #0F172A;
}}

QHeaderView::section {{
    background-color: #F8FAFC;
    color: #475569;
    padding: 8px;
    font-weight: bold;
    border: none;
    border-bottom: 1px solid #E2E8F0;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: #F1F5F9;
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: #CBD5E1;
    border-radius: 4px;
}}
"""
