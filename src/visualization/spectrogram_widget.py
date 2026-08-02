"""
Spectrogram Widget Module
PyQtGraph ImageItem real-time 2D Time-Frequency Spectrogram / Waterfall plot.
Y-axis: Frequency (0-40 Hz), X-axis: Time history, Color: Power Spectral Density.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
import numpy as np

class SpectrogramWidget(QWidget):
    def __init__(self, parent=None, history_len=100, freqs_len=60):
        super().__init__(parent)
        self.history_len = history_len
        self.freqs_len = freqs_len
        self.img_data = np.zeros((self.freqs_len, self.history_len))
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(None)
        self.plot_widget.showGrid(x=False, y=True, alpha=0.15)
        self.plot_widget.setLabel('left', 'Frequency', units='Hz')
        self.plot_widget.setLabel('bottom', 'Time Window')

        self.img_item = pg.ImageItem()
        self.plot_widget.addItem(self.img_item)

        # Medical Plasma / Viridis Colormap Lookup Table
        pos = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        color = np.array([
            [11, 15, 25, 255],     # Dark background
            [6, 182, 212, 255],    # Cyan
            [16, 185, 129, 255],   # Emerald
            [245, 158, 11, 255],   # Amber
            [239, 68, 68, 255]     # Rose Peak
        ], dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        self.img_item.setLookupTable(cmap.getLookupTable())

        layout.addWidget(self.plot_widget)

    def update_spectrogram(self, psd_slice):
        if len(psd_slice) == 0:
            return
        
        # Resample psd_slice to freqs_len
        if len(psd_slice) != self.freqs_len:
            psd_resampled = np.interp(np.linspace(0, 1, self.freqs_len), np.linspace(0, 1, len(psd_slice)), psd_slice)
        else:
            psd_resampled = psd_slice

        # Shift image data matrix to left & append new column
        self.img_data = np.roll(self.img_data, -1, axis=1)
        self.img_data[:, -1] = psd_resampled

        self.img_item.setImage(self.img_data, autoLevels=True)
