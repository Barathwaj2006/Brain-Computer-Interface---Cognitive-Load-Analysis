"""
NeuroSim App Configuration & Global Constants
"""

# App Metadata
APP_NAME = "NEUROSIM"
APP_SUBTITLE = "Synthetic EEG Cognitive Analysis & Clinical Stress Platform"
APP_VERSION = "1.0.0"

# Signal Acquisition & DSP Constants
SAMPLING_RATE_HZ = 250
WINDOW_SECONDS = 5.0
WINDOW_SAMPLES = int(SAMPLING_RATE_HZ * WINDOW_SECONDS)  # 1250 samples
BUFFER_CAPACITY = int(SAMPLING_RATE_HZ * 10.0)           # 2500 samples (10 seconds)

# EEG Frequency Band Boundaries (Hz)
BAND_LIMITS = {
    'delta': (0.5, 4.0),
    'theta': (4.0, 8.0),
    'alpha': (8.0, 13.0),
    'beta': (13.0, 30.0),
    'gamma': (30.0, 45.0)
}

# Synthetic Frequency Targets for Simulation
FREQ_TARGETS = {
    'delta': 2.0,
    'theta': 6.0,
    'alpha': 10.0,
    'beta': 20.0
}

# Clinical State Thresholds (Based on Spectral Ratios)
COGNITIVE_LOAD_CLASSES = ['LOW', 'MODERATE', 'HIGH']

# UI Color Palette (Dark Neomorphic / Glassmorphism Medical Theme)
COLORS = {
    'bg_dark': '#0B0F19',
    'bg_card': '#151D2A',
    'bg_card_hover': '#1E293B',
    'border_glow': '#1E293B',
    'text_primary': '#F8FAFC',
    'text_secondary': '#94A3B8',
    'text_muted': '#64748B',
    'accent_cyan': '#06B6D4',     # Primary accent / Delta
    'accent_emerald': '#10B981',  # Theta / Good status
    'accent_purple': '#8B5CF6',   # Alpha / Moderate status
    'accent_amber': '#F59E0B',    # Beta / High status
    'accent_rose': '#EF4444',     # Stress warning
    'grid_line': '#1E293B'
}

# Serial Defaults
DEFAULT_COM_PORT = "AUTO"
DEFAULT_BAUD_RATE = 115200
