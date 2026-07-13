#!/usr/bin/env python3
"""
GHOST VIPER - Setup Wizard
First-time setup: installs deps, generates icons, creates shortcuts
"""

import os
import sys
import subprocess
import shutil
import ctypes

BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║           GHOST VIPER - SETUP WIZARD v4.2.0                 ║
║           The snake is preparing to hunt...                  ║
╚═══════════════════════════════════════════════════════════════╝
"""

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run():
    print(BANNER)
    root = os.path.dirname(os.path.abspath(__file__))
    os.environ['GHOST_VIPER_ROOT'] = root

    print("[1/5] Checking Python...")
    print(f"    Python {sys.version}")

    print("[2/5] Installing dependencies...")
    deps = ['requests', 'pillow', 'customtkinter', 'packaging']
    for dep in deps:
        try:
            __import__(dep.replace('-', '_'))
            print(f"    ✓ {dep}")
        except ImportError:
            print(f"    * Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--quiet"])
            print(f"    ✓ {dep} installed")

    print("[3/5] Generating resources...")
    sys.path.insert(0, root)
    try:
        from utils.icon_gen import generate_app_icon, generate_small_icon
        png = generate_app_icon()
        ico = generate_small_icon()
        print(f"    ✓ Icon: {ico}")
    except Exception as e:
        print(f"    ! Warning: {e}")

    print("[4/5] Creating shortcuts...")
    try:
        from utils.shortcut import create_onedrive_shortcut
        from core.config import GhostConfig
        config = GhostConfig()
        create_onedrive_shortcut(config)
        print("    ✓ OneDrive Desktop shortcut created")
        print("    ✓ Startup shortcut added")
    except Exception as e:
        print(f"    ! Warning: {e}")

    print("[5/5] Launching application...")
    print()
    print("═" * 50)
    print("  SETUP COMPLETE. LAUNCHING GHOST VIPER...")
    print("═" * 50)
    print()

    # Launch main app
    main_script = os.path.join(root, 'ghost_viper.py')
    os.chdir(root)
    subprocess.Popen([sys.executable, main_script], cwd=root)

if __name__ == '__main__':
    run()
