# -*- mode: python ; coding: utf-8 -*-

# Improved PyInstaller spec for VCF Processor
# Build with: pyinstaller build_improved.spec

block_cipher = None

# Analysis block with comprehensive dependencies
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    
    # Include all necessary data files
    datas=[
        ('config.ini', '.'),
        ('static', 'static'),
        ('templates', 'templates'),
        ('vcf_extractor.py', '.'),
        ('config.py', '.'),
    ],
    
    # Comprehensive hidden imports for VCF processing
    hiddenimports=[
        # Core dependencies
        'openpyxl',
        'pandas',
        'numpy',
        'unidecode',
        'configparser',
        'json',
        'ast',
        'logging',
        'os',
        'sys',
        'io',
        're',
        'threading',
        'time',
        'signal',
        'subprocess',
        
        # Web framework
        'webview',
        'flask',
        'werkzeug',
        'jinja2',
        'markupsafe',
        'itsdangerous',
        'click',
        'importlib_metadata',
        
        # Pandas Excel support
        'pandas.io.excel',
        'pandas.io.parsers',
        'pandas.io.common',
        'pandas.core.dtypes',
        'pandas.io.excel._openpyxl',
        'pandas.io.parsers.readers',
        'pandas.io.formats.format',
        'pandas.io.formats.excel',
        'pandas._libs.writers',
        
        # OpenPyXL dependencies
        'openpyxl.workbook',
        'openpyxl.worksheet',
        'openpyxl.styles',
        'openpyxl.utils',
        'openpyxl.writer.excel',
        
        # Additional encoding support
        'encodings.utf_8',
        'encodings.utf_8_sig',
        'encodings.iso8859_1',
        'encodings.cp1252',
        'encodings.latin_1',
        
        # WebView dependencies
        'webview.platforms',
        'webview.dom',
        'webview.js',
        'webview.util',
    ],
    
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PIL',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Create PYZ archive
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable (onedir for faster startup)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VCF_Processor_Fast',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX for faster startup
    console=False,  # Hide console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Add icon
)

# Collect all files (onedir)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Disable UPX for faster startup
    upx_exclude=[],
    name='VCF_Processor_Fast',
)