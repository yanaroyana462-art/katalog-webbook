# Patch script.js: buka halaman unggah otomatis bila URL memuat ?aksi=unggah
import shutil, sys
p = 'script.js'
s = open(p, encoding='utf-8').read()
if "aksi') === 'unggah'" in s:
    print('Sudah dipatch, tidak ada perubahan.'); sys.exit(0)
anchor = "    init() {\n"
if anchor not in s:
    print('Anchor init() tidak ditemukan. Batalkan.'); sys.exit(1)
shutil.copy(p, p + '.bak')
add = anchor + "      if (new URLSearchParams(window.location.search).get('aksi') === 'unggah') this.currentView = 'upload';\n"
s = s.replace(anchor, add, 1)
open(p, 'w', encoding='utf-8').write(s)
print('OK: script.js dipatch (cadangan: script.js.bak)')