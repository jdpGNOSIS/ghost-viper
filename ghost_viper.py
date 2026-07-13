#!/usr/bin/env python3
"""
GHOST VIPER - GitHub OSINT Hunter
Advanced Social Engineering Toolkit
Version 4.2.0
"""

import sys
import os
import ctypes
import subprocess

sys.dont_write_bytecode = True
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║       ██████  ██   ██  ██████  ███████ ████████  ██          ║
║      ██       ██   ██ ██    ██ ██         ██    ██          ║
║      ██   ███ ███████ ██    ██ ███████    ██    ██          ║
║      ██    ██ ██   ██ ██    ██      ██    ██    ██          ║
║       ██████  ██   ██  ██████  ███████    ██    ██          ║
║                                                               ║
║      ██    ██ ██ ██████  ███████ ██████                      ║
║      ██    ██ ██ ██   ██ ██      ██   ██                     ║
║      ██    ██ ██ ██████  █████   ██████                      ║
║       ██  ██  ██ ██      ██      ██   ██                     ║
║        ████   ██ ██      ███████ ██   ██                     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""

def require_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def ensure_deps():
    missing = []
    pkgs = {
        'requests': 'requests',
        'PIL': 'pillow',
        'customtkinter': 'customtkinter',
        'tkinter': None,
    }
    for mod, pkg in pkgs.items():
        try:
            __import__(mod)
        except ImportError:
            if pkg:
                missing.append(pkg)
    return missing

def main():
    print(BANNER)
    print("[*] Initializing GHOST VIPER...")

    missing = ensure_deps()
    if missing:
        print(f"[!] Missing dependencies: {', '.join(missing)}")
        print("[*] Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, "--quiet"])
        print("[+] Dependencies installed.")

    os.environ['GHOST_VIPER_ROOT'] = os.path.dirname(os.path.abspath(__file__))

    from ui.app import GhostViperApp

    app = GhostViperApp()
    app.run()

if __name__ == "__main__":
    main()
