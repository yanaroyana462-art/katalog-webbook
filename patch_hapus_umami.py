import re, shutil, sys

path = "dashboard.html"
src = open(path, encoding="utf-8").read()

pattern = re.compile(
    r'<template x-if="isAdmin">\s*<div class="mt-12.*?cloud\.umami\.is/share.*?</iframe>\s*</div>\s*</div>\s*</template>[ \t]*\n?',
    re.S,
)

matches = pattern.findall(src)
if len(matches) == 0:
    print("[lewati] blok iframe Umami tidak ditemukan (mungkin sudah dihapus)")
    sys.exit(0)
if len(matches) != 1:
    sys.exit(f"[GAGAL] ditemukan {len(matches)} blok, harus tepat 1. Tidak ada yang diubah.")

shutil.copy(path, path + ".bak2")
src = pattern.sub("", src, count=1)
open(path, "w", encoding="utf-8").write(src)
print("[ok] iframe Umami dihapus (cadangan: dashboard.html.bak2)")
