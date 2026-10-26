# -*- mode: python ; coding: utf-8 -*-
# Đóng gói: pyinstaller VE_MONGBANCOSUON.spec  ->  dist/VE_MONGBANCOSUON.exe
a = Analysis(
    ['app.py'],
    pathex=[],
    datas=[('assets', 'assets')],
    hiddenimports=['ezdxf.addons.drawing.pymupdf', 'PIL.ImageTk', 'PIL._tkinter_finder'],
    excludes=['matplotlib', 'PyQt5', 'PySide6', 'IPython', 'pandas', 'scipy',
              'pymupdf.layout', 'pymupdf_layout', 'pymupdf4llm', 'onnxruntime', 'torch'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='VE_MONGBANCOSUON',
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon='assets/icon.ico',
    version='version_info.txt',
)
