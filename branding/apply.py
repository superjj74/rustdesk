#!/usr/bin/env python3
"""Applica il branding WizDesk al sorgente RustDesk prima della build.
Eseguire dalla radice del repo: python3 branding/apply.py"""
import os, re, shutil, sys

APP = 'WizDesk'
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
errors = []

def patch(path, pairs, required=True):
    if not os.path.exists(path):
        (errors if required else [None]).append(f'manca {path}'); return
    with open(path, encoding='utf-8', newline='') as f: s = f.read()
    for pat, rep in pairs:
        s2, n = re.subn(pat, rep, s)
        if n == 0 and required: errors.append(f'{path}: nessuna corrispondenza per {pat!r}')
        s = s2
    with open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)

# 1) grafica: copia branding/files/* sopra il repo
n = 0
for d, _, files in os.walk(os.path.join(HERE, 'files')):
    for fn in files:
        src = os.path.join(d, fn); dst = os.path.relpath(src, os.path.join(HERE, 'files'))
        os.makedirs(os.path.dirname(dst) or '.', exist_ok=True); shutil.copyfile(src, dst); n += 1
print(f'copiati {n} file grafici')

# 2) nome applicazione (config, servizi, cartelle, testi UI)
patch('libs/hbb_common/src/config.rs',
      [(r'APP_NAME: RwLock<String> = RwLock::new\("RustDesk"\.to_owned\(\)\)',
        f'APP_NAME: RwLock<String> = RwLock::new("{APP}".to_owned())')])
# 3) Windows: proprietà dell'eseguibile
patch('flutter/windows/runner/Runner.rc',
      [(r'"FileDescription", "RustDesk Remote Desktop"', f'"FileDescription", "{APP}"'),
       (r'"ProductName", "RustDesk"', f'"ProductName", "{APP}"')])
# 4) macOS: WizDesk.app (il codice si aspetta /Applications/<APP_NAME>.app)
patch('flutter/macos/Runner/Configs/AppInfo.xcconfig', [(r'PRODUCT_NAME = RustDesk', f'PRODUCT_NAME = {APP}')])
patch('build.py', [(r'RustDesk\.app', f'{APP}.app'), (r'RustDesk Installer', f'{APP} Installer')])
# 5) Linux: voce di menu e titolo finestra
for f in ['res/rustdesk.desktop', 'res/rustdesk-link.desktop']:
    patch(f, [(r'(?m)^Name=RustDesk$', f'Name={APP}')], required=False)
patch('flutter/linux/my_application.cc', [(r'_set_title\((\w+), "rustdesk"\)', rf'_set_title(\1, "{APP}")')], required=False)
# 6) Android: nome app
patch('flutter/android/app/src/main/AndroidManifest.xml',
      [(r'android:label="RustDesk"', f'android:label="{APP}"'),
       (r'android:label="RustDesk Input"', f'android:label="{APP} Input"')])
patch('flutter/android/app/src/main/res/values/strings.xml',
      [(r'<string name="app_name">RustDesk</string>', f'<string name="app_name">{APP}</string>')])

# 7) il client usa sempre il server integrato: non trattarlo come "server pubblico"
#    (altrimenti mostra l'avviso "configura uno specifico server" e limita qualita'/FPS)
patch('src/common.rs',
      [(r'(pub fn using_public_server\(\) -> bool \{\n)\s*crate::get_custom_rendezvous_server\(get_option\("custom-rendezvous-server"\)\)\.is_empty\(\)',
        r'\1    false')])

if errors:
    print('ERRORI branding:\n  ' + '\n  '.join(errors)); sys.exit(1)
print(f'branding {APP} applicato')
