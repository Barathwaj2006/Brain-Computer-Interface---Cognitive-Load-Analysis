"""
PyInstaller Packaging Build Script
Builds standalone NeuroSim.exe Windows desktop executable in dist/ directory.
"""

import os
import sys
import subprocess

def build():
    print("[Build] Compiling NeuroSim executable with PyInstaller...")
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec_path = os.path.join(project_root, "NeuroSim.spec")

    venv_pyinstaller = os.path.join(project_root, "venv", "Scripts", "pyinstaller.exe")
    cmd = [venv_pyinstaller, "--noconfirm", spec_path]

    res = subprocess.run(cmd, cwd=project_root)
    if res.returncode == 0:
        exe_path = os.path.join(project_root, "dist", "NeuroSim.exe")
        print(f"\n[Build Success] Package built successfully!")
        print(f"Executable location: {exe_path}")
    else:
        print(f"\n[Build Failure] PyInstaller exited with code {res.returncode}")
        sys.exit(res.returncode)

if __name__ == '__main__':
    build()
