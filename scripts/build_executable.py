"""
PyInstaller Packaging Script for NeuroSim Standalone Executable
Compiles src/main.py into dist/NeuroSim.exe
Supports:
  python scripts/build_executable.py           (One-File Bundle)
  python scripts/build_executable.py --onedir  (One-Directory Directory Build)
"""

import argparse
import subprocess
import sys
import os

def build_exe():
    parser = argparse.ArgumentParser(description="PyInstaller Packaging Script for NeuroSim")
    parser.add_argument('--onedir', action='store_true', help="Build as a directory folder instead of single executable (faster startup, easier code-signing)")
    args = parser.parse_args()

    print("Building NeuroSim Standalone Windows Executable...")
    venv_python = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'venv', 'Scripts', 'python.exe')
    pyinstaller_exe = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'venv', 'Scripts', 'pyinstaller.exe')

    if not os.path.exists(pyinstaller_exe):
        pyinstaller_exe = "pyinstaller"

    cmd = [
        pyinstaller_exe,
        "--noconfirm",
        "--clean"
    ]

    if args.onedir:
        cmd.append("--onedir")
        print("[Build] Mode: Directory Build (--onedir)")

    cmd.append("NeuroSim.spec")

    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print("Build finished successfully! Output location: dist/")

if __name__ == '__main__':
    build_exe()
