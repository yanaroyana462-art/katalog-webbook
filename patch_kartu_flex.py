import shutil, sys

path = "dashboard.html"
src = open(path, encoding="utf-8").read()

if "book-grid" in src:
    print("[lewati] sudah dipatch")
    sys.exit(0)

css = """<link rel="stylesheet" href="style.css" />
  <style>
    /* Rak buku: flex, kartu rata tinggi, sampul utuh */
    .book-grid { display: flex; flex-wrap: wrap; gap: .75rem; }
    .book-card { flex: 1 1 calc(50% - .375rem); max-width: calc(50% - .375rem); min-width: 0; }
    @media (min-width: 640px) {
      .book-grid { gap: 1.25rem; }
      .book-card { flex-basis: calc(33.333% - .84rem); max-width: calc(33.333% - .84rem); }
    }
    @media (min-width: 1280px) {
      .book-card { flex-basis: calc(25% - .95rem); max-width: calc(25% - .95rem); }
    }
    .book-cover { display: flex; flex-direction: column; }
    .book-img { display: block; width: 100%; aspect-ratio: 3 / 4; object-fit: contain; background-color: #f1efe9; }
    .dark .book-img { background-color: #0f172a; }
    .book-badges { display: flex; flex-wrap: wrap; gap: .25rem; padding: .5rem .5rem 0; }
    .book-badges > div { display: flex; flex-wrap: wrap; gap: .25rem; }
    .book-actions { flex-wrap: wrap; }
    @media (max-width: 639px) {
      .book-read { flex: 1 1 100%; justify-content: center; padding-top: .5rem; padding-bottom: .5rem; }
    }
  </style>"""

edits = [
    ("css", '<link rel="stylesheet" href="style.css" />', css),
    ("grid",
     '<div class="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-5" x-show="filteredBooks.length > 0">',
     '<div class="book-grid" x-show="filteredBooks.length > 0">'),
    ("kartu",
     '<div class="bg-gradient-to-b from-white via-[#faf9f6]/80',
     '<div class="book-card bg-gradient-to-b from-white via-[#faf9f6]/80'),
    ("cover",
     'class="relative h-44 w-full overflow-hidden bg-slate-100 dark:bg-slate-800 cursor-pointer"',
     'class="book-cover relative w-full bg-slate-100 dark:bg-slate-800 cursor-pointer"'),
    ("img",
     'class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out"',
     'class="book-img"'),
    ("placeholder",
     'class="w-full h-full bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center text-white/40"',
     'class="book-img bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center text-white/40"'),
    ("overlay",
     '<div class="absolute inset-0 bg-gradient-to-t from-slate-900/30 via-transparent to-transparent"></div>',
     ''),
    ("label",
     '<div class="absolute top-3 left-3 right-3 flex items-center justify-between">',
     '<div class="book-badges">'),
    ("aksi",
     '<div class="flex items-center justify-between gap-1 sm:justify-start sm:gap-2">',
     '<div class="book-actions flex items-center justify-between gap-1 sm:justify-start sm:gap-2">'),
    ("tombol",
     'title="Baca Sekarang" aria-label="Baca Sekarang" class="px-2 sm:px-3.5',
     'title="Baca Sekarang" aria-label="Baca Sekarang" class="book-read px-2 sm:px-3.5'),
    ("teks",
     '<span class="hidden sm:inline">Baca Sekarang</span>',
     '<span>Baca Sekarang</span>'),
]

for label, old, new in edits:
    n = src.count(old)
    if n != 1:
        sys.exit(f"[GAGAL] anchor '{label}' ditemukan {n}x (harus 1x). Tidak ada yang diubah.")
    src = src.replace(old, new)

shutil.copy(path, path + ".bak3")
open(path, "w", encoding="utf-8").write(src)
print("[ok] kartu buku diubah ke flex (cadangan: dashboard.html.bak3)")
