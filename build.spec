# build.spec

# -*- mode: python ; coding: utf-8 -*-

import os

base_path = os.getcwd()

a = Analysis(
    ['app.py'],
    pathex=[base_path],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('config.ini', '.'),
        ('vcf_extractor.py', '.')
    ],
    # --- THIS IS THE CHANGE ---
    hiddenimports=[
        'webview',
        'webview.platforms.winforms', # Often needed for Windows
        'pandas._libs.tslibs.base'    # Still needed for pandas
    ],
    excludes=['torch', 'tensorflow', 'tensorflow_estimator', 'torchvision', 'torchaudio', 'tensorboard'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Processador_de_VCF',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False , icon='icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Processador_de_VCF')
