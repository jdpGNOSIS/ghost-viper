import os
import sys
import subprocess
import winreg
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

def get_onedrive_desktop():
    """Get OneDrive Desktop path (handles both personal and work/school)."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\OneDrive\Accounts\Personal")
        onedrive_path = winreg.QueryValueEx(key, "UserFolder")[0]
        key.Close()
        desktop = os.path.join(onedrive_path, "Desktop")
        if os.path.exists(desktop):
            return desktop
    except:
        pass
    return os.path.join(os.path.expanduser('~'), 'OneDrive', 'Desktop')

def create_shortcut(target, shortcut_path, arguments=None, description=None, icon_path=None, working_dir=None):
    """Create a Windows shortcut using PowerShell."""
    ps_script = f"""
    $WScriptShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WScriptShell.CreateShortcut("{shortcut_path}")
    $Shortcut.TargetPath = "{target}"
    """

    if arguments:
        ps_script += f"$Shortcut.Arguments = {arguments}\n"
    ps_script += "$Shortcut.WindowStyle = 7\n"
    if working_dir:
        ps_script += f'$Shortcut.WorkingDirectory = "{working_dir}"\n'
    if description:
        ps_script += f'$Shortcut.Description = "{description}"\n'
    if icon_path:
        ps_script += f'$Shortcut.IconLocation = "{icon_path}, 0"\n'

    ps_script += "$Shortcut.Save()\n"

    result = subprocess.run(
        ['powershell.exe', '-NoProfile', '-Command', ps_script],
        capture_output=True, text=True, timeout=30
    )
    return result.returncode == 0

def create_onedrive_shortcut(config):
    """Create desktop shortcut on OneDrive Desktop with custom icon."""
    onedrive_desktop = get_onedrive_desktop()
    if not os.path.exists(onedrive_desktop):
        onedrive_desktop = os.path.join(os.path.expanduser('~'), 'Desktop')

    icon_path = os.path.join(os.environ.get('GHOST_VIPER_ROOT', os.path.expanduser('~')),
                              'assets', 'ghost_viper_small.ico')

    # If icon doesn't exist yet, use default python
    icon_arg = f'"{icon_path}"' if os.path.exists(icon_path) else ''

    main_script = os.path.join(os.environ.get('GHOST_VIPER_ROOT', os.path.expanduser('~')),
                                'ghost_viper.py')
    python_exe = sys.executable

    shortcut_path = os.path.join(onedrive_desktop, 'GHOST VIPER.lnk')

    success = create_shortcut(
        target=python_exe,
        arguments=f'"{main_script}"',
        shortcut_path=shortcut_path,
        description='GHOST VIPER - GitHub OSINT Hunter Toolkit',
        icon_path=icon_path if os.path.exists(icon_path) else python_exe,
        working_dir=os.environ.get('GHOST_VIPER_ROOT', os.path.expanduser('~')),
    )

    if success:
        print(f"[+] Shortcut created: {shortcut_path}")
    else:
        print(f"[!] Failed to create shortcut.")

    # Also try OneNote / other known OneDrive paths
    alt_desktops = [
        os.path.join(os.path.expanduser('~'), 'OneDrive', 'Desktop'),
        os.path.join(os.environ.get('OneDriveConsumer', ''), 'Desktop'),
        os.path.join(os.environ.get('OneDriveCommercial', ''), 'Desktop'),
    ]
    for ad in alt_desktops:
        if ad and ad != onedrive_desktop and os.path.exists(ad):
            alt_path = os.path.join(ad, 'GHOST VIPER.lnk')
            if not os.path.exists(alt_path):
                create_shortcut(
                    target=python_exe,
                    arguments=f'"{main_script}"',
                    shortcut_path=alt_path,
                    description='GHOST VIPER - GitHub OSINT Hunter Toolkit',
                    icon_path=icon_path if os.path.exists(icon_path) else python_exe,
                    working_dir=os.environ.get('GHOST_VIPER_ROOT', os.path.expanduser('~')),
                )

    # Pin to taskbar via startup
    startup_path = os.path.join(os.environ.get('APPDATA', ''),
                                 r'Microsoft\Windows\Start Menu\Programs\Startup')
    if os.path.exists(startup_path):
        startup_lnk = os.path.join(startup_path, 'GHOST VIPER.lnk')
        if not os.path.exists(startup_lnk):
            create_shortcut(
                target=python_exe,
                arguments=f'"{main_script}"',
                shortcut_path=startup_lnk,
                description='GHOST VIPER - GitHub OSINT Hunter',
                icon_path=icon_path if os.path.exists(icon_path) else python_exe,
                working_dir=os.environ.get('GHOST_VIPER_ROOT', os.path.expanduser('~')),
            )

    return success
