#!/usr/bin/env python3
"""
Patch Pustaka WebBook: Kata Pengantar, Pendahuluan, Glosarium, dan Daftar Pustaka
tidak lagi dihitung sebagai "Bab". Penomoran Bab dan Subbab mengikuti naskah asli.

  Kata Pengantar / Pendahuluan  -> label "Pembuka" (tanpa nomor)
  Glosarium / Daftar Pustaka    -> label "Penutup"  (tanpa nomor)
  Bab sesungguhnya              -> Bab 1, Bab 2, ... mulai dari 1
  Subbab                        -> nomor mengikuti Bab-nya (mis. 1.1, 1.2)

Berlaku juga untuk buku lama (dikenali dari judul), tanpa migrasi database.

Pakai (di folder berisi script.js dan dashboard.html):
  python3 patch_penomoran_bab.py
  python3 patch_penomoran_bab.py /path/ke/folder

Aman dijalankan ulang. Cadangan: script.js.bak3 dan dashboard.html.bak3
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
JS = folder / "script.js"
HTML = folder / "dashboard.html"
if not HTML.exists() and (folder / "index.html").exists():
    HTML = folder / "index.html"

for f in (JS, HTML):
    if not f.exists():
        sys.exit(f"File tidak ditemukan: {f}")

report = []

NEW_LABEL_FN = r"""// Judul yang berasal dari kolom Pembuka/Penutup, bukan bab bernomor
   isFrontBackMatter(chapter) {
     const t = (this.getChapterDisplayTitle(chapter) || '').trim();
     return /^(kata pengantar|prakata|pendahuluan|glosarium|daftar pustaka)$/i.test(t);
   },

   getMatterLabel(chapter) {
     const t = (this.getChapterDisplayTitle(chapter) || '').trim();
     return /^(glosarium|daftar pustaka)$/i.test(t) ? 'Penutup' : 'Pembuka';
   },

   getChapterLabel(chapter, index) {
     const chapters = this.activeBook?.chapters;
     if (!chapters) return `Bab ${index + 1}`;
     const sub = this.getChapterSubchapter(chapter);
     if (sub) {
       // parentIndex tersimpan sebagai posisi di daftar utama; ubah ke nomor Bab sesungguhnya
       const mains = chapters.filter(c => !this.isSubchapter(c));
       const num = mains.slice(0, sub.parentIndex).filter(c => !this.isFrontBackMatter(c)).length;
       return `Subbab ${num || sub.parentIndex}.${sub.subchapterIndex}`;
     }
     if (this.isFrontBackMatter(chapter)) return this.getMatterLabel(chapter);
     const n = chapters
       .slice(0, index + 1)
       .filter(c => !this.isSubchapter(c) && !this.isFrontBackMatter(c)).length;
     return `Bab ${n}`;
   },

   getChapterBadge(chapter, index) {
     if (this.isSubchapter(chapter)) return this.getChapterSubchapter(chapter).subchapterIndex;
     if (this.isFrontBackMatter(chapter)) return '•';
     return this.getChapterLabel(chapter, index).replace('Bab ', '');
   },"""

# ---------------- script.js ----------------
shutil.copy(JS, str(JS) + ".bak3")
js = JS.read_text(encoding="utf-8")

if "isFrontBackMatter(chapter) {" in js:
    report.append("= script.js: penomoran bab sudah terpasang, dilewati")
else:
    pattern = re.compile(
        r"getChapterLabel\(chapter, index\)\s*\{[\s\S]*?Bab \$\{chapterNumber\}`;\s*\},"
    )
    matches = pattern.findall(js)
    if len(matches) != 1:
        report.append(f"! script.js: fungsi getChapterLabel ditemukan {len(matches)}x (perlu 1x), TIDAK ditambal")
    else:
        js = pattern.sub(lambda m: NEW_LABEL_FN, js, count=1)
        report.append("+ script.js: getChapterLabel + helper pembuka/penutup: OK")
JS.write_text(js, encoding="utf-8")

# ---------------- HTML ----------------
shutil.copy(HTML, str(HTML) + ".bak3")
html = HTML.read_text(encoding="utf-8")


def patch(text, label, old, new):
    if old not in text:
        report.append(f"= {label}: " + ("sudah terpasang, dilewati" if new in text else "ANCHOR TIDAK DITEMUKAN (!)"))
        return text
    if text.count(old) > 1:
        report.append(f"! {label}: anchor muncul {text.count(old)}x, dilewati")
        return text
    report.append(f"+ {label}: OK")
    return text.replace(old, new)


html = patch(
    html,
    "html: badge daftar isi",
    "x-text=\"isSubchapter(chapter) ? getChapterSubchapter(chapter).subchapterIndex : getChapterLabel(chapter, idx).replace('Bab ', '')\"",
    'x-text="getChapterBadge(chapter, idx)"',
)

html = patch(
    html,
    "html: tombol mulai baca",
    "'Baca Pratinjau (Bab 1)' : 'Mulai Baca Bab 1'",
    "'Baca Pratinjau' : 'Mulai Membaca'",
)
HTML.write_text(html, encoding="utf-8")

print("\n".join(report))
try:
    r = subprocess.run(["node", "--check", str(JS)], capture_output=True, text=True)
    if r.returncode == 0:
        print("\nCek sintaks script.js: OK")
    else:
        print("\nCek sintaks GAGAL:\n" + r.stderr)
        print(f"Pulihkan dengan: cp {JS}.bak3 {JS}")
except FileNotFoundError:
    print("\n(node tidak ditemukan, cek sintaks dilewati)")