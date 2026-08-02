"""
NeuroSim Configuration Module — Medical-Grade Research Standard
Centralized application settings, medical-grade styling tokens, and branding constants.
"""

# Platform Branding & Identity
APP_NAME = "NeuroSim"
APP_TITLE = "NeuroSim — Intelligent EEG Cognitive Analytics Platform"
APP_SUBTITLE = "Real-Time Neural Signal Processing • Cognitive Analytics • Research Platform"
APP_LOGO_TEXT = "◉╱╲◉ NeuroSim"
APP_TAGLINE = "Neural Intelligence Platform"
STATUS_BADGE = "RESEARCH SYSTEM"
VERSION = "1.0.0-MEDICAL-RESEARCH"

# Medical-Grade Terminology Standards
INTERFACE_NAME = "NeuroSim Neural Sensor Array"
SOURCE_SIMULATOR = "Neural Signal Synthesizer"
SOURCE_DEVICE = "NeuroSim Hardware Interface"

# 10-20 International System Electrode Montage (8 Channels)
CHANNELS_1020 = ["Fp1", "Fp2", "C3", "C4", "P3", "P4", "O1", "O2"]
IMPEDANCE_THRESHOLD_KOHM = 4.8  # kΩ (< 5 kΩ is excellent contact)

# Signal Processing Parameters & Aliases
SAMPLING_RATE = 250  # Hz
SAMPLING_RATE_HZ = 250  # Hz alias for legacy compatibility
WINDOW_SIZE_SEC = 5.0
FFT_WINDOW_SAMPLES = int(SAMPLING_RATE * WINDOW_SIZE_SEC)  # 1250 samples

# Frequency Target Frequencies (Hz)
FREQ_TARGETS = {
    'delta': 2.0,
    'theta': 6.0,
    'alpha': 10.0,
    'beta': 20.0
}

# Active Medical Filter Indicators
NOTCH_FILTER_STATUS = "50/60 Hz Notch ON"
EOG_FILTER_STATUS = "Ocular Artifact Filter ON"
EMG_FILTER_STATUS = "EMG Muscle Filter ON"

# Frequency Bands (Hz)
BANDS = {
    'delta': (0.5, 4.0),
    'theta': (4.0, 8.0),
    'alpha': (8.0, 13.0),
    'beta': (13.0, 30.0)
}

# Color Palette (Dark Medical & Glassmorphism Theme)
COLOR_BACKGROUND = "#0B0F19"
COLOR_CARD_BG = "rgba(21, 29, 42, 0.75)"
COLOR_SIDEBAR_BG = "#0F172A"
COLOR_BORDER = "rgba(255, 255, 255, 0.08)"
COLOR_BORDER_GLOW = "rgba(6, 182, 212, 0.3)"

# Accent Colors
COLOR_CYAN = "#06B6D4"      # Primary / Waveform
COLOR_EMERALD = "#10B981"   # Theta / Signal Quality / Pass
COLOR_PURPLE = "#8B5CF6"    # Alpha / Relaxation
COLOR_AMBER = "#F59E0B"     # Beta / Moderate
COLOR_ROSE = "#EF4444"      # High Load / Warning / Fail
COLOR_TEXT_MAIN = "#F8FAFC"
COLOR_TEXT_MUTED = "#94A3B8"

# Universal COLORS Dictionary for Stylesheet & Widget Compatibility
COLORS = {
    'bg_dark': COLOR_BACKGROUND,
    'bg_card': COLOR_CARD_BG,
    'bg_sidebar': COLOR_SIDEBAR_BG,
    'text_primary': COLOR_TEXT_MAIN,
    'text_main': COLOR_TEXT_MAIN,
    'text_secondary': COLOR_TEXT_MUTED,
    'text_muted': COLOR_TEXT_MUTED,
    'accent_cyan': COLOR_CYAN,
    'accent_emerald': COLOR_EMERALD,
    'accent_purple': COLOR_PURPLE,
    'accent_amber': COLOR_AMBER,
    'accent_rose': COLOR_ROSE,
    'cyan': COLOR_CYAN,
    'emerald': COLOR_EMERALD,
    'purple': COLOR_PURPLE,
    'amber': COLOR_AMBER,
    'rose': COLOR_ROSE
}
