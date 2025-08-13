# -*- mode: python ; coding: utf-8 -*-

# Este é um arquivo de especificação para o PyInstaller.
# Para construir o executável, execute no terminal:
# pyinstaller build_fixed.spec

block_cipher = None

# a: Analysis block. Aqui definimos as fontes do nosso código e as dependências.
a = Analysis(
    ['app.py'],  # O script principal do seu aplicativo
    pathex=[],
    binaries=[],
    
    # datas: A parte mais importante para incluir arquivos que não são de código.
    # O formato é uma lista de tuplas: ('caminho/do/arquivo/ou/pasta', 'pasta_de_destino_no_exe')
    datas=[
        ('config.ini', '.'),
        ('static', 'static'),
        ('templates', 'templates'),
        ('vcf_extractor.py', '.'),
    ],
    
    # hiddenimports: Lista de bibliotecas que o PyInstaller pode não encontrar sozinho.
    # Esta é a correção para o problema do 'pandas' não encontrar o motor do Excel.
    hiddenimports=[
        'openpyxl',
        'pandas',
        'numpy',
        'configparser',
        'json',
        'ast',
        'logging',
        'os',
        'sys',
        'threading',
        'time',
        'signal',
        'subprocess',
        'webview',
        'flask',
        'werkzeug',
        'jinja2',
        'markupsafe',
        'itsdangerous',
        'click',
        'importlib_metadata',
        'pandas.io.excel',
        'pandas.io.parsers',
        'pandas.io.common',
        'pandas.core.dtypes',
        'pandas.io.excel._openpyxl',
        'pandas.io.parsers.readers',
        'pandas.io.formats.format',
    ],
    
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# pyz: Cria o arquivo .pyz que agrupa todos os módulos Python.
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# exe: Define as configurações para o executável final.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VCF_Processor',  # O nome do seu arquivo .exe
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # <<< ALTERADO >>> 'True' para ver mensagens de debug
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# coll: Usado para o modo de pasta (não --onefile). Não precisamos mexer aqui.
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VCF_Processor',
)
