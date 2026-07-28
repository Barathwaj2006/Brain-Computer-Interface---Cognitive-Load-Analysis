from setuptools import setup, find_packages

setup(
    name="neurosim-eeg-cognitive-analysis",
    version="1.0.0",
    description="Synthetic EEG Cognitive Analysis & Clinical Stress Desktop Platform",
    author="NeuroSim Team",
    packages=find_packages(),
    install_requires=[
        "PySide6>=6.5.0",
        "pyqtgraph>=0.13.0",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "pyserial>=3.5",
        "pandas>=2.0.0",
        "scikit-learn>=1.2.0",
        "reportlab>=4.0.0",
        "pyinstaller>=5.10.0",
        "matplotlib>=3.7.0",
        "joblib>=1.2.0",
        "pytest>=7.3.0"
    ],
    entry_points={
        'console_scripts': [
            'neurosim=src.main:main',
        ],
    },
)
