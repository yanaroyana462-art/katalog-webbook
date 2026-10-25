import re, shutil, sys

def load(path):
    return open(path, encoding="utf-8").read()

js = load("script.js")
html = load("dashboard.html")

if "filterCategories" in js:
    print("[lewati] sudah dipatch")
    sys.exit(0)

# ---------- script.js ----------
old_cat = "categories: ['Semua', 'Teknologi & AI', 'Edukasi & Parenting', 'Bisnis & SOP', 'Agama & Pemikiran'],"
new_cat = """categories: ['Semua', 'Teknologi & AI', 'Edukasi & Parenting', 'Bisnis & SOP', 'Agama & Pemikiran', 'Pengembangan Diri & Komunikasi', 'Fiksi & Sastra', 'Kesehatan & Gaya Hidup', 'Sejarah', 'Politik', 'Ekonomi'],"""

old_get = "get availableCategories() {"
new_get = """get filterCategories() {
      // Filter rak: sembunyikan kategori yang belum punya buku terlihat
      const visible = new Set(
        this.catalog
          .filter(b => !b.isPrivate || (this.currentUser && b.userId === this.currentUser.id))
          .map(b => b.category)
      );
      return ['Semua', ...this.categories.slice(1).filter(c => visible.has(c) || c === this.selectedCategory)];
    },

    get availableCategories() {"""

for label, old, expected in [("daftar kategori", old_cat, 1), ("getter", old_get, 1)]:
    n = js.count(old)
    if n != expected:
        sys.exit(f"[GAGAL] script.js: '{label}' ditemukan {n}x (harus {expected}x). Tidak ada yang diubah.")

js = js.replace(old_cat, new_cat).replace(old_get, new_get)

# ---------- dashboard.html ----------
old_for = 'x-for="cat in categories"'
n = html.count(old_for)
if n != 2:
    sys.exit(f"[GAGAL] dashboard.html: filter kategori ditemukan {n}x (harus 2x). Tidak ada yang diubah.")
html = html.replace(old_for, 'x-for="cat in filterCategories"')

# naikkan versi cache script.js otomatis
m = re.search(r'script\.js\?v=(\d+)\.(\d+)', html)
if m:
    new_ver = f"{m.group(1)}.{int(m.group(2)) + 1}"
    html = html.replace(m.group(0), f"script.js?v={new_ver}")
    print(f"[info] versi cache script.js: {m.group(1)}.{m.group(2)} -> {new_ver}")
else:
    print("[peringatan] versi cache script.js tidak ditemukan, naikkan manual")

shutil.copy("script.js", "script.js.bak_kategori")
shutil.copy("dashboard.html", "dashboard.html.bak_kategori")
open("script.js", "w", encoding="utf-8").write(js)
open("dashboard.html", "w", encoding="utf-8").write(html)
print("[ok] kategori ditambah (cadangan: *.bak_kategori)")
