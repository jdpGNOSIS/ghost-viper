#!/usr/bin/env python3
"""
GHOST VIPER - Build Standalone Executable
Creates a single .exe with PyInstaller
"""

import os
import sys
import shutil
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))

def ensure_deps():
    pkgs = ['pyinstaller', 'requests', 'pillow', 'customtkinter', 'packaging']
    for pkg in pkgs:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            print(f"[*] Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])

def build():
    ensure_deps()

    # Generate icon first
    sys.path.insert(0, ROOT)
    from utils.icon_gen import generate_app_icon, generate_small_icon

    print("[*] Generating icons...")
    png_icon = generate_app_icon()
    ico_icon = generate_small_icon()
    print(f"[+] Icons: {png_icon}, {ico_icon}")

    entry = os.path.join(ROOT, 'ghost_viper.py')

    print("[*] Building executable...")
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name', 'GHOST_VIPER',
        '--icon', ico_icon,
        '--add-data', f"{png_icon};assets",
        '--add-data', f"{ico_icon};assets",
        '--hidden-import', 'customtkinter',
        '--hidden-import', 'PIL',
        '--hidden-import', 'PIL._tkinter_finder',
        '--hidden-import', 'requests',
        '--clean',
        '--noconfirm',
        entry,
    ]

    subprocess.check_call(cmd, cwd=ROOT)

    # Copy icon to dist
    dist_icon = os.path.join(ROOT, 'dist', 'ghost_viper_icon.png')
    if os.path.exists(png_icon):
        shutil.copy2(png_icon, dist_icon)

    exe_path = os.path.join(ROOT, 'dist', 'GHOST_VIPER.exe')
    if os.path.exists(exe_path):
        print(f"\n[+] SUCCESS: {exe_path}")
        print(f"    Size: {os.path.getsize(exe_path) / 1024 / 1024:.1f} MB")
    else:
        print("\n[!] Build may have failed. Check dist/ directory.")

if __name__ == '__main__':
    build()
