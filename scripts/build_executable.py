"""
PyInstaller Packaging Script for NeuroSim Standalone Executable
Compiles src/main.py into dist/NeuroSim.exe
"""

import subprocess
import sys
import os

def build_exe():
    print("Building NeuroSim Standalone Windows Executable...")
    venv_python = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'venv', 'Scripts', 'python.exe')
    pyinstaller_exe = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'venv', 'Scripts', 'pyinstaller.exe')

    if not os.path.exists(pyinstaller_exe):
        pyinstaller_exe = "pyinstaller"

    cmd = [
        pyinstaller_exe,
        "--noconfirm",
        "--clean",
        "NeuroSim.spec"
    ]
    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print("Build finished successfully! Binary location: dist/NeuroSim.exe")

if __name__ == '__main__':
    build_exe()
