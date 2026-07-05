# -*- mode: python ; coding: utf-8 -*-
import os
import importlib
from PyInstaller.utils.hooks import collect_all, collect_data_files

datas = collect_data_files('customtkinter')
binaries = []
hiddenimports = ['tkinter', '_tkinter']
tmp_ret = collect_all('faster_whisper')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('ctranslate2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Collect NVIDIA DLLs if they are installed in the environment (e.g. Windows/Linux GPU packages)
for pkg_name in ["nvidia.cublas", "nvidia.cudnn", "nvidia.cuda_runtime"]:
    try:
        pkg = importlib.import_module(pkg_name)
        pkg_dir = None
        if hasattr(pkg, "__file__") and pkg.__file__:
            pkg_dir = os.path.dirname(pkg.__file__)
        elif hasattr(pkg, "__path__") and pkg.__path__:
            # Namespace packages have __path__ instead of __file__
            pkg_dir = list(pkg.__path__)[0]

        if pkg_dir:
            # On Windows, DLLs are in the bin/ directory
            if os.name == 'nt':
                bin_dir = os.path.join(pkg_dir, "bin")
                if os.path.exists(bin_dir):
                    binaries.append((os.path.join(bin_dir, "*.dll"), "."))
            else:
                # On Linux, shared libraries are in the lib/ directory
                lib_dir = os.path.join(pkg_dir, "lib")
                if os.path.exists(lib_dir):
                    binaries.append((os.path.join(lib_dir, "*.so*"), "."))
    except ImportError:
        pass


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas + [('assets/*', 'assets')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ManuscriptMatch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ManuscriptMatch',
)
