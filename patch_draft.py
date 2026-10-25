import re, shutil, sys

js = open("script.js", encoding="utf-8").read()
html = open("dashboard.html", encoding="utf-8").read()

if "isEditingDraft" in js:
    print("[lewati] sudah dipatch")
    sys.exit(0)

def apply(src, name, edits):
    # edits: (label, old, new, jumlah_wajib) ; jumlah_wajib bisa angka atau "opsional"
    for label, old, new, need in edits:
        n = src.count(old)
        if need == "opsional":
            continue
        if n != need:
            sys.exit(f"[GAGAL] {name}: '{label}' ditemukan {n}x (harus {need}x). Tidak ada yang diubah.")
    for label, old, new, need in edits:
        if need == "opsional" and src.count(old) != 1:
            continue
        src = src.replace(old, new)
    return src

# ---------------- script.js ----------------
helpers = """get isEditingDraft() {
     return Boolean(this.isEditingId && this.catalog.find(b => b.id === this.isEditingId)?.isDraft);
   },

   formatDate(d) {
     if (!d) return '';
     const s = String(d);
     const dt = new Date(s.length <= 10 ? s + 'T00:00:00' : s);
     if (isNaN(dt)) return '';
     return dt.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
   },

   isNewBook(book) {
     if (!book || book.isDraft || !book.createdAt) return false;
     const dt = new Date(book.createdAt + 'T00:00:00');
     return !isNaN(dt) && (Date.now() - dt.getTime()) < 30 * 24 * 60 * 60 * 1000;
   },

   formatCurrency(amount) {"""

js_edits = [
    ("tanda tangan fungsi", "async saveNewBook() {", "async saveNewBook(asDraft = false) {", 1),
    ("cek hak cipta",
     "if (!this.uploadForm.rightsAccepted || !this.uploadForm.rightsType) {",
     """if (asDraft) {
       if (!this.currentUser) { this.showToast('Masuk dulu untuk menyimpan draft.', 'error'); return; }
       if (!this.uploadForm.title.trim()) { this.showToast('Isi judul buku dulu sebelum menyimpan draft.', 'error'); return; }
     } else if (!this.uploadForm.rightsAccepted || !this.uploadForm.rightsType) {""", 1),
    ("bab cadangan", "if (formattedChapters.length === 0) {", "if (formattedChapters.length === 0 && !asDraft) {", 1),
    ("payload edit", "file_name: this.uploadForm.fileName || null,",
     "file_name: this.uploadForm.fileName || null,\n             is_draft: Boolean(asDraft),", 1),
    ("katalog lokal (edit)", "this.catalog[bookIdx].fileName = this.uploadForm.fileName;",
     """this.catalog[bookIdx].fileName = this.uploadForm.fileName;
         this.catalog[bookIdx].isDraft = Boolean(asDraft);
         this.showToast(asDraft ? 'Draft diperbarui.' : 'Perubahan tersimpan.', 'success');
         if (asDraft) this.scopeFilter = 'my-books';""", 1),
    ("buku baru", "id: 'book-' + Date.now(),", "id: 'book-' + Date.now(),\n       isDraft: Boolean(asDraft),", 1),
    ("payload baru", "if (this.currentUser?.id) bookPayload.user_id = this.currentUser.id;",
     "if (this.currentUser?.id) bookPayload.user_id = this.currentUser.id;\n         bookPayload.is_draft = Boolean(asDraft);", 1),
    ("katalog lokal (baru)", "this.catalog.unshift(newBook);",
     """this.catalog.unshift(newBook);
     if (asDraft) { this.scopeFilter = 'my-books'; this.showToast('Draft tersimpan. Lanjutkan kapan saja lewat tab Buku Saya.', 'success'); }
     else { this.showToast('Buku berhasil diterbitkan.', 'success'); }""", 1),
    ("baca dari database", "isPrivate: Boolean(item.is_private),",
     "isPrivate: Boolean(item.is_private),\n              isDraft: Boolean(item.is_draft),", 1),
    ("saring rak",
     "if (book.isPrivate && (!this.currentUser || book.userId !== this.currentUser.id)) return false;",
     """if (book.isPrivate && (!this.currentUser || book.userId !== this.currentUser.id)) return false;
       if (book.isDraft && (this.scopeFilter !== 'my-books' || !this.currentUser || book.userId !== this.currentUser.id)) return false;""", 1),
    ("daftar penulis",
     "return [...new Set(this.catalog.map(b => b.author))].sort();",
     "return [...new Set(this.catalog.filter(b => !b.isDraft && b.author).map(b => b.author))].sort();", 1),
    ("daftar judul melayang",
     "return this.catalog.filter(b => !q || b.title.toLowerCase().includes(q) || b.author.toLowerCase().includes(q));",
     "return this.catalog.filter(b => !b.isDraft && (!q || b.title.toLowerCase().includes(q) || b.author.toLowerCase().includes(q)));", 1),
    ("fungsi bantu", "formatCurrency(amount) {", helpers, 1),
    ("kategori filter (opsional)",
     ".filter(b => !b.isPrivate || (this.currentUser && b.userId === this.currentUser.id))",
     ".filter(b => !b.isDraft && (!b.isPrivate || (this.currentUser && b.userId === this.currentUser.id)))", "opsional"),
]

# ---------------- dashboard.html ----------------
badge_old = '<span x-show="book.isPrivate" class="text-[10px] bg-slate-800/95 text-slate-200 px-2 py-0.5 rounded font-medium shadow-sm border border-slate-700">Internal</span>'
badge_new = ('<span x-show="book.isDraft" class="text-[10px] bg-amber-500/95 text-white border border-amber-400 px-2 py-0.5 rounded font-semibold shadow-sm">Draft</span>\n'
             '                  <span x-show="isNewBook(book)" class="text-[10px] bg-indigo-600/95 text-white border border-indigo-400 px-2 py-0.5 rounded font-semibold shadow-sm">Baru</span>\n'
             '                  ' + badge_old)

author_old = '<p class="text-sm font-medium text-stone-500 dark:text-slate-400 mt-1" x-text="`Penulis: ${activeBook?.author}`"></p>'
author_new = author_old + '\n            <p class="text-xs text-stone-400 dark:text-slate-500 mt-0.5" x-text="activeBook?.isDraft ? \'Draft (belum diterbitkan)\' : `Diterbitkan ${formatDate(activeBook?.createdAt)}`"></p>'

submit_old = '<button type="submit" :disabled="isSaving" class="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white text-xs font-semibold rounded-lg shadow-md shadow-indigo-600/30 transition flex items-center gap-1.5">'
draft_btn = ('<button type="button" x-show="!isEditingId || isEditingDraft" @click="saveNewBook(true)" :disabled="isSaving" '
             'class="px-4 py-2 bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/40 dark:hover:bg-amber-900/50 text-amber-800 dark:text-amber-200 border border-amber-200 dark:border-amber-800 disabled:opacity-60 text-xs font-semibold rounded-lg transition">Simpan Draft</button>\n        ')

html_edits = [
    ("label draft dan baru", badge_old, badge_new, 1),
    ("tanggal di kartu", 'x-text="`${book.chapters.length} Materi`"',
     'x-text="`${book.chapters.length} Materi · ${formatDate(book.createdAt)}`"', 1),
    ("bagikan di kartu", '<button @click.stop="shareBook(book)"', '<button x-show="!book.isDraft" @click.stop="shareBook(book)"', 1),
    ("pensil draft", '<button @click="openEditModal(book)"',
     '<button @click="book.isDraft ? (editForm.originalBook = book, editInFullForm()) : openEditModal(book)"', 1),
    ("tanggal di halaman buku", author_old, author_new, 1),
    ("hitungan buku", 'font-semibold" x-text="catalog.length"', 'font-semibold" x-text="catalog.filter(b => !b.isDraft).length"', 1),
    ("baris tombol",
     '<div class="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">',
     '<div class="flex flex-wrap items-center justify-end gap-2 sm:gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">', 1),
    ("tombol draft", submit_old, draft_btn + submit_old, 1),
    ("teks tombol terbit", "x-text=\"isSaving ? 'Menyimpan...' : 'Simpan ke Rak Buku'\"",
     "x-text=\"isSaving ? 'Menyimpan...' : ((!isEditingId || isEditingDraft) ? 'Terbitkan ke Rak Buku' : 'Simpan Perubahan')\"", 1),
]

js = apply(js, "script.js", js_edits)
html = apply(html, "dashboard.html", html_edits)

m = re.search(r'script\.js\?v=(\d+)\.(\d+)', html)
if m:
    new_ver = f"{m.group(1)}.{int(m.group(2)) + 1}"
    html = html.replace(m.group(0), f"script.js?v={new_ver}")
    print(f"[info] versi cache script.js: {m.group(1)}.{m.group(2)} -> {new_ver}")
else:
    print("[peringatan] versi cache script.js tidak ditemukan, naikkan manual")

shutil.copy("script.js", "script.js.bak_draft")
shutil.copy("dashboard.html", "dashboard.html.bak_draft")
open("script.js", "w", encoding="utf-8").write(js)
open("dashboard.html", "w", encoding="utf-8").write(html)
print("[ok] fitur draft dan tanggal terpasang (cadangan: *.bak_draft)")
