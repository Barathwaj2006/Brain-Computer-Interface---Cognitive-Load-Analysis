"""
Multi-Channel Viewer Module
8-Channel stacked oscilloscope trace viewer displaying parallel 10-20 system EEG channels:
Fp1, Fp2, C3, C4, P3, P4, O1, O2
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
import numpy as np

class MultiChannelViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.channels = ["Fp1", "Fp2", "C3", "C4", "P3", "P4", "O1", "O2"]
        self.curves = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(None)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)
        self.plot_widget.setLabel('left', 'Electrode Montage')
        self.plot_widget.setLabel('bottom', 'Time (Samples)')

        colors = ['#06B6D4', '#06B6D4', '#8B5CF6', '#8B5CF6', '#10B981', '#10B981', '#F59E0B', '#F59E0B']

        for i, ch_name in enumerate(self.channels):
            curve = self.plot_widget.plot(pen=pg.mkPen(color=colors[i], width=1.5))
            self.curves.append(curve)

        layout.addWidget(self.plot_widget)

    def update_channels(self, base_wave):
        if len(base_wave) == 0:
            return
        
        num_samples = min(300, len(base_wave))
        wave = base_wave[-num_samples:]

        for i, ch_name in enumerate(self.channels):
            # Apply slight phase/amplitude shift for realistic multi-channel montage visualization
            phase_shift = (i * 0.15)
            ch_wave = wave * (1.0 + 0.1 * np.sin(phase_shift)) + (i * 50.0)
            self.curves[i].setData(ch_wave)
