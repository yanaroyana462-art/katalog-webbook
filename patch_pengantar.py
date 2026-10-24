#!/usr/bin/env python3
"""
Patch Pustaka WebBook: kolom Kata Pengantar, Pendahuluan, Glosarium, dan
Daftar Pustaka tidak lagi menghasilkan <br/> liar. Tiap baris = satu paragraf.

Syarat: patch_normalisasi_bab.py sudah pernah dijalankan (plainTextToHtml ada).

Pakai:
  python3 patch_pengantar.py
  python3 patch_pengantar.py /path/ke/folder

Aman dijalankan ulang. Cadangan: script.js.bak2
"""
import shutil
import subprocess
import sys
from pathlib import Path

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
JS = folder / "script.js"
if not JS.exists():
    sys.exit(f"File tidak ditemukan: {JS}")

js = JS.read_text(encoding="utf-8")
if "plainTextToHtml(text) {" not in js:
    sys.exit("plainTextToHtml belum ada. Jalankan patch_normalisasi_bab.py dulu.")

shutil.copy(JS, str(JS) + ".bak2")
report = []


def patch(text, label, old, new):
    if old not in text:
        if new in text:
            report.append(f"= {label}: sudah terpasang, dilewati")
        else:
            report.append(f"! {label}: ANCHOR TIDAK DITEMUKAN")
        return text
    n = text.count(old)
    if n > 1:
        report.append(f"! {label}: anchor muncul {n}x, dilewati")
        return text
    report.append(f"+ {label}: OK")
    return text.replace(old, new)


# 1) Aturan paragraf: tiap baris = satu paragraf
js = patch(
    js,
    "aturan paragraf (tiap baris = paragraf)",
    r"const paras = /\n\s*\n/.test(t) ? t.split(/\n\s*\n/) : t.split('\n');",
    r"const paras = t.split(/\n+/);",
)

# 2) Empat kolom dialihkan ke plainTextToHtml
for field in ("foreword", "introduction", "glossary", "bibliography"):
    old = (
        "`<p>${this.uploadForm." + field + r".trim().replace(/\n\n/g, '</p><p>')"
        r".replace(/\n/g, '<br/>')}</p>`"
    )
    new = "this.plainTextToHtml(this.uploadForm." + field + ")"
    js = patch(js, f"kolom {field}", old, new)

JS.write_text(js, encoding="utf-8")

print("\n".join(report))
try:
    r = subprocess.run(["node", "--check", str(JS)], capture_output=True, text=True)
    if r.returncode == 0:
        print("\nCek sintaks script.js: OK")
    else:
        print("\nCek sintaks GAGAL:\n" + r.stderr)
        print("Pulihkan dengan: cp script.js.bak2 script.js")
except FileNotFoundError:
    print("\n(node tidak ditemukan, cek sintaks dilewati)")