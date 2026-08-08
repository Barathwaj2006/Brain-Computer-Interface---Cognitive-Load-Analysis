"""
Spectrogram View Compatibility Module
Re-exports SpectrogramWidget from src.visualization.spectrogram_widget.
Guarantees compatibility for frozen executable import resolution.
"""

from src.visualization.spectrogram_widget import SpectrogramWidget

__all__ = ["SpectrogramWidget"]
