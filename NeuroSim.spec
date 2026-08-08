# -*- mode: python ; coding: utf-8 -*-

import os
block_cipher = None

# Ensure required directories exist before packaging
os.makedirs('reports', exist_ok=True)
os.makedirs('models', exist_ok=True)
os.makedirs('firmware', exist_ok=True)
os.makedirs('src/assets', exist_ok=True)

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('models', 'models'),
        ('firmware', 'firmware'),
        ('src/assets', 'src/assets'),
        ('docs/assets', 'docs/assets')
    ],
    hiddenimports=[
        'pyqtgraph',
        'scipy',
        'scipy.signal',
        'scipy.special',
        'sklearn',
        'sklearn.ensemble',
        'reportlab',
        'reportlab.lib',
        'reportlab.platypus',
        'serial',
        'sqlite3'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtWebEngine',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.Qt3D',
        'PySide6.QtDesigner',
        'PySide6.QtHelp',
        'PySide6.QtLocation',
        'PySide6.QtPositioning',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtSensors',
        'tkinter'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NeuroSim',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
