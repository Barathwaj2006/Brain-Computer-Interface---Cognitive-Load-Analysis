"""
Results & Research Platform Screen Module
Executive single-view unified research platform combining:
- Side-by-Side Dual Classifier Panel (Rule-Based Margin vs ML Probability)
- Disagreement Warning Flag
- Band Power Breakdown Matrix
- One-Click PDF Report Exporter
Theme: Bright Frosted Glassmorphism
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QGridLayout
from PySide6.QtCore import Qt, Signal
from src.app.config import COLOR_CARD_BG, COLOR_CYAN, COLOR_EMERALD, COLOR_PURPLE, COLOR_AMBER, COLOR_ROSE
from src.reporting.pdf_generator import PDFReportGenerator

class ResultsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf_generator = PDFReportGenerator()
        self.current_metrics = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header Title
        h_card = QFrame()
        h_card.setStyleSheet("background: rgba(255, 255, 255, 0.85); border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px;")
        h_layout = QHBoxLayout(h_card)

        t_box = QVBoxLayout()
        title = QLabel("UNIFIED RESULTS & DUAL CLASSIFIER COMPARISON")
        title.setStyleSheet("font-size: 15px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        sub = QLabel("Side-by-Side Clinical Rule Heuristics vs Machine Learning Probability Metrics")
        sub.setStyleSheet("font-size: 11px; color: #64748B;")
        t_box.addWidget(title)
        t_box.addWidget(sub)

        btn_export = QPushButton("📄 EXPORT PDF REPORT")
        btn_export.setStyleSheet("background: linear-gradient(135deg, #0284C7, #0369A1); color: white; font-weight: 800; font-size: 12px; padding: 12px 20px; border-radius: 8px; border: none;")
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.clicked.connect(self.export_pdf_report)

        h_layout.addLayout(t_box)
        h_layout.addStretch()
        h_layout.addWidget(btn_export)
        layout.addWidget(h_card)

        # Disagreement Warning Flag Banner
        self.disagree_banner = QFrame()
        self.disagree_banner.setStyleSheet("background: rgba(225, 29, 72, 0.1); border: 1px solid #E11D48; border-radius: 8px; padding: 8px 16px;")
        self.disagree_banner.hide()
        d_layout = QHBoxLayout(self.disagree_banner)
        d_layout.setContentsMargins(8, 4, 8, 4)
        
        self.disagree_lbl = QLabel("⚠️ CLASSIFIER DISAGREEMENT: Rule-Based and ML Classifiers predicted different states!")
        self.disagree_lbl.setStyleSheet("color: #E11D48; font-weight: 800; font-size: 11px;")
        d_layout.addWidget(self.disagree_lbl)
        layout.addWidget(self.disagree_banner)

        # Side-by-Side Dual Classifier Panel
        cls_card = QFrame()
        cls_card.setStyleSheet("background: rgba(255, 255, 255, 0.85); border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px;")
        cls_layout = QHBoxLayout(cls_card)
        cls_layout.setSpacing(16)

        # Left: Rule-Based Classifier Box
        rule_box = QFrame()
        rule_box.setStyleSheet("background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 10px; padding: 14px;")
        r_layout = QVBoxLayout(rule_box)
        
        r_title = QLabel("RULE-BASED CLASSIFIER (CLINICAL HEURISTICS)")
        r_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #64748B; letter-spacing: 1px;")
        self.val_rule_state = QLabel("MODERATE")
        self.val_rule_state.setStyleSheet("font-size: 20px; font-weight: 900; color: #0284C7; margin-top: 4px;")
        self.val_rule_margin = QLabel("Rule Margin: 85.0%")
        self.val_rule_margin.setToolTip("Heuristic threshold score (0-100), not a statistical probability.")
        self.val_rule_margin.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569;")

        r_layout.addWidget(r_title)
        r_layout.addWidget(self.val_rule_state)
        r_layout.addWidget(self.val_rule_margin)
        cls_layout.addWidget(rule_box, stretch=1)

        # Right: ML Classifier Box (Random Forest)
        ml_box = QFrame()
        ml_box.setStyleSheet("background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 10px; padding: 14px;")
        m_layout = QVBoxLayout(ml_box)

        m_title = QLabel("ML CLASSIFIER (RANDOM FOREST PROBABILITY)")
        m_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #64748B; letter-spacing: 1px;")
        self.val_ml_state = QLabel("MODERATE")
        self.val_ml_state.setStyleSheet("font-size: 20px; font-weight: 900; color: #7C3AED; margin-top: 4px;")
        self.val_ml_conf = QLabel("Statistical Confidence: 92.4%")
        self.val_ml_conf.setToolTip("Real statistical probability predicted by Random Forest model.")
        self.val_ml_conf.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569;")

        m_layout.addWidget(m_title)
        m_layout.addWidget(self.val_ml_state)
        m_layout.addWidget(self.val_ml_conf)
        cls_layout.addWidget(ml_box, stretch=1)

        layout.addWidget(cls_card)

        # Main Grid Layout for Metrics & Band Breakdown
        grid_card = QFrame()
        grid_card.setStyleSheet("background: rgba(255, 255, 255, 0.85); border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px;")
        g_layout = QGridLayout(grid_card)
        g_layout.setSpacing(16)

        # Row 1: Key Performance Metrics
        self.val_stress = self._create_result_box("SPECTRAL STRESS INDEX", "0.48", COLOR_AMBER, g_layout, 0, 0)
        self.val_dom = self._create_result_box("DOMINANT RHYTHM", "ALPHA (10 Hz)", COLOR_PURPLE, g_layout, 0, 1)
        self.val_tbr = self._create_result_box("THETA / BETA RATIO (TBR)", "1.00", COLOR_CYAN, g_layout, 0, 2)
        self.val_quality = self._create_result_box("SIGNAL QUALITY / SAMPLING", "EXCELLENT (250 Hz)", COLOR_EMERALD, g_layout, 0, 3)

        # Row 2: Band Breakdown Cards
        self.val_delta = self._create_result_box("DELTA POWER (0.5-4 Hz)", "25.0 %", COLOR_CYAN, g_layout, 1, 0)
        self.val_theta = self._create_result_box("THETA POWER (4-8 Hz)", "25.0 %", COLOR_EMERALD, g_layout, 1, 1)
        self.val_alpha = self._create_result_box("ALPHA POWER (8-13 Hz)", "25.0 %", COLOR_PURPLE, g_layout, 1, 2)
        self.val_beta  = self._create_result_box("BETA POWER (13-30 Hz)", "25.0 %", COLOR_AMBER, g_layout, 1, 3)

        layout.addWidget(grid_card)

    def _create_result_box(self, title, val, color, grid_layout, row, col):
        frame = QFrame()
        frame.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px;")
        l = QVBoxLayout(frame)
        
        t = QLabel(title)
        t.setStyleSheet("font-size: 10px; font-weight: 800; color: #64748B; letter-spacing: 1px;")
        
        v = QLabel(val)
        v.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {color}; margin-top: 4px;")

        l.addWidget(t)
        l.addWidget(v)

        grid_layout.addWidget(frame, row, col)
        return v

    def update_results(self, band_powers, metrics, rule_res=None, ml_res=None):
        self.current_metrics = metrics
        self.current_metrics.update(band_powers)

        self.val_delta.setText(f"{band_powers.get('delta_rel', 25.0):.1f} %")
        self.val_theta.setText(f"{band_powers.get('theta_rel', 25.0):.1f} %")
        self.val_alpha.setText(f"{band_powers.get('alpha_rel', 25.0):.1f} %")
        self.val_beta.setText(f"{band_powers.get('beta_rel', 25.0):.1f} %")

        self.val_stress.setText(f"{metrics.get('stress_index', 0.48):.2f}")
        self.val_tbr.setText(f"{metrics.get('tbr', 1.0):.2f}")
        self.val_dom.setText(metrics.get('dominant_band', 'ALPHA'))

        # Rule-Based vs ML Display
        rule_state = rule_res.get('cognitive_state', metrics.get('load_class', 'MODERATE')) if rule_res else metrics.get('load_class', 'MODERATE')
        rule_margin = rule_res.get('rule_margin', rule_res.get('confidence', 80.0)) if rule_res else 80.0
        
        ml_state = ml_res.get('cognitive_state', 'MODERATE') if ml_res else 'MODERATE'
        ml_conf = ml_res.get('confidence', 85.0) if ml_res else 85.0
        is_ml_active = ml_res.get('is_ml', True) if ml_res else True

        self.val_rule_state.setText(rule_state)
        self.val_rule_margin.setText(f"Rule Margin: {rule_margin:.1f}% (Heuristic)")

        if is_ml_active:
            self.val_ml_state.setText(ml_state)
            self.val_ml_conf.setText(f"Statistical Probability: {ml_conf:.1f}%")
        else:
            self.val_ml_state.setText("N/A (Fallback)")
            self.val_ml_conf.setText("Model Not Loaded")

        # Disagreement Flag
        if is_ml_active and (rule_state != ml_state):
            self.disagree_banner.show()
            self.disagree_lbl.setText(f"⚠️ CLASSIFIER DISAGREEMENT: Rule-Based ({rule_state}) vs ML ({ml_state})")
        else:
            self.disagree_banner.hide()

    def export_pdf_report(self):
        filepath = self.pdf_generator.generate_report(self.current_metrics)
        alert_text = f"Report Generated Successfully!\nSaved to: {filepath}"
        print(alert_text)
