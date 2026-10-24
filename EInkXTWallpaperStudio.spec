# PyInstaller spec for Windows, Linux and macOS. Run from the repository root.
from pathlib import Path
import sys
ROOT = Path(SPECPATH)
a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT / 'src')],
    binaries=[],
    datas=[(str(ROOT / 'lang'), 'lang'), (str(ROOT / 'assets'), 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='EInkXTWallpaperStudio',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, disable_windowed_traceback=False, argv_emulation=False,
    icon=str(ROOT / 'assets' / 'EInkXTWallpaperStudio-app.ico') if sys.platform == 'win32' else None,
    target_arch=None, codesign_identity=None, entitlements_file=None,
)
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='EInkXT Wallpaper Studio.app',
        icon=None,
        bundle_identifier='dev.evoll.einkxtwallpaperstudio',
        info_plist={'NSHighResolutionCapable': 'True', 'CFBundleDisplayName': 'EInkXT Wallpaper Studio'},
    )
